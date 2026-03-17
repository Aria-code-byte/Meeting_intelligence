"""
Jinni 会议精灵 - FastAPI 后端服务器
===============================
架构设计：
1. FastAPI 提供高性能异步 REST API
2. BackgroundTasks 处理长时任务（无需 Redis）
3. SQLAlchemy ORM 管理数据库
4. Whisper ASR 语音转文字
5. 多种 LLM Provider 支持（Mock/DeepSeek/OpenAI/GLM/Anthropic）

启动方式：
    uvicorn main:app --reload --host 0.0.0.0 --port 8000
"""

import asyncio
import json
import os
import shutil
import subprocess
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional

# 加载 .env 文件
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # 如果没有 python-dotenv，跳过环境变量加载

from fastapi import (
    FastAPI,
    UploadFile,
    File,
    Form,
    HTTPException,
    BackgroundTasks,
    Depends,
    Query,
)
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict
from sqlalchemy import create_engine, or_
from sqlalchemy.orm import Session, sessionmaker

from models import Base, Meeting, Result, Template, Summary

# ============================================================
# 导入真实 ASR 和 Summarizer 模块
# ============================================================
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from audio.extract_audio import extract_audio
from asr.transcribe import transcribe as asr_transcribe
from summarizer.llm.base import LLMMessage

# ============================================================
# 配置与初始化
# ============================================================

# 项目路径配置
BASE_DIR = Path(__file__).parent
STORAGE_DIR = BASE_DIR / "storage"
VIDEO_DIR = STORAGE_DIR / "videos"
DB_DIR = STORAGE_DIR / "db"
TRANSCRIPT_DIR = STORAGE_DIR / "transcripts"
CPP_ENGINE_PATH = BASE_DIR / "core" / "jinni_engine"

# 创建必要目录
for dir_path in [STORAGE_DIR, VIDEO_DIR, DB_DIR, TRANSCRIPT_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# SQLite 数据库配置
DATABASE_URL = f"sqlite:///{DB_DIR}/jinni.db"
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # SQLite 多线程支持
    echo=False,  # 生产环境关闭 SQL 日志
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建表
Base.metadata.create_all(bind=engine)

# FastAPI 应用初始化
app = FastAPI(
    title="Jinni 会议精灵 API",
    description="基于 Whisper ASR 与多种 LLM 的智能会议处理平台",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS 中间件配置（允许 Streamlit 前端跨域访问）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 竞赛环境允许所有源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 支持的视频格式
ALLOWED_EXTENSIONS = {".mp4", ".mp3", ".wav", ".m4a", ".m4v", ".avi", ".mov"}
MAX_FILE_SIZE = int(1024 * 1024 * 1024 * 2.5)  # 2.5GB


# ============================================================
# 数据库依赖注入
# ============================================================

def get_db():
    """获取数据库会话（依赖注入）"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============================================================
# Pydantic 请求/响应模型
# ============================================================

class MeetingResponse(BaseModel):
    """会议记录响应模型"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    video_path: str
    video_size: Optional[int] = None
    duration: Optional[float] = None
    status: str
    error_message: Optional[str] = None
    progress: int
    one_line_summary: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class ResultResponse(BaseModel):
    """处理结果响应模型"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    meeting_id: int
    transcript_raw: str
    transcript_enhanced: Optional[str] = None
    summary_json: dict
    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None
    processing_time: Optional[float] = None
    word_count: Optional[int] = None
    created_at: datetime


class MeetingDetailResponse(MeetingResponse):
    """会议详情响应（包含结果）"""
    results: List[ResultResponse] = []


# ============================================================
# LLM Provider 创建（参考 meeting_intelligence/cli.py）
# ============================================================

def create_llm_provider(provider_name: str = "mock"):
    """
    创建 LLM Provider

    Args:
        provider_name: LLM 提供商名称

    Returns:
        LLM Provider 实例

    Raises:
        RuntimeError: API Key 未设置
        ValueError: 不支持的 provider
    """
    if provider_name == "mock":
        from summarizer.llm.mock import MockLLMProvider
        return MockLLMProvider()
    elif provider_name == "glm":
        from summarizer.llm.glm import GLMProvider
        api_key = os.environ.get("ZHIPU_API_KEY")
        if not api_key:
            raise RuntimeError("未设置 ZHIPU_API_KEY 环境变量")
        return GLMProvider(api_key=api_key, model="glm-4-flash")
    elif provider_name == "openai":
        from summarizer.llm.openai import OpenAIProvider
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("未设置 OPENAI_API_KEY 环境变量")
        return OpenAIProvider(api_key=api_key, model="gpt-4o-mini")
    elif provider_name == "deepseek":
        from summarizer.llm.deepseek import DeepSeekProvider
        api_key = os.environ.get("DEEPSEEK_API_KEY")
        if not api_key:
            raise RuntimeError("未设置 DEEPSEEK_API_KEY 环境变量")
        return DeepSeekProvider(api_key=api_key, model="deepseek-chat")
    elif provider_name == "anthropic":
        from summarizer.llm.anthropic import AnthropicProvider
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError("未设置 ANTHROPIC_API_KEY 环境变量")
        return AnthropicProvider(api_key=api_key, model="claude-3-5-sonnet-20241022")
    else:
        raise ValueError(f"不支持的 provider: {provider_name}")


def _get_template_by_name(template_name: str):
    """
    从数据库获取模板或返回默认模板

    Args:
        template_name: 模板名称

    Returns:
        Template 对象或默认模板
    """
    db = SessionLocal()
    try:
        template = db.query(Template).filter(Template.name == template_name).first()
        if template:
            return template
        # 返回默认模板
        from dataclasses import dataclass

        @dataclass
        class DefaultTemplate:
            name: str = "通用总结"
            description: str = "请提供会议的全面总结，包括主要议题、讨论要点和后续行动计划。"

        return DefaultTemplate()
    finally:
        db.close()


# ============================================================
# 真实会议处理模块（参考 CLI 流程，优化版）
# ============================================================
# 全局缓存：Whisper 模型（避免重复加载）
_whisper_model_cache = {}
_whisper_model_lock = asyncio.Lock()


def _extract_audio_sync(video_path: str):
    """同步音频提取（在线程池中运行）"""
    return extract_audio(video_path)


def _transcribe_sync(audio_path: str, model_size: str):
    """标准 ASR 转写（回退方案，使用原始 asr.transcribe）"""
    return asr_transcribe(
        audio_path,
        language="auto",
        model_size=model_size
    )


def _transcribe_fast_sync(audio_path: str, model_size: str):
    """
    快速 ASR 转写（优化版，直接调用 Whisper，跳过文件 I/O）

    优化点：
    1. 直接使用 Whisper，跳过中间 JSON 文件保存
    2. 复用已加载的模型（全局缓存）
    3. 跳过后处理（可选）
    """
    import whisper
    import wave
    import os
    from asr.types import Utterance
    from audio.extract_audio import _get_audio_duration

    # 验证音频文件
    if not os.path.exists(audio_path):
        raise RuntimeError(f"音频文件不存在: {audio_path}")

    # 检查文件大小
    file_size = os.path.getsize(audio_path)
    if file_size < 1000:  # 小于 1KB，可能是空文件
        raise RuntimeError(f"音频文件太小或为空: {audio_path} ({file_size} bytes)")

    # 获取时长并验证
    duration = _get_audio_duration(audio_path)
    if duration < 0.5:  # 小于 0.5 秒
        raise RuntimeError(f"音频时长太短，无法转写: {duration:.2f}秒 (至少需要 0.5 秒)")

    # 使用缓存的模型（如果存在）
    model_key = f"whisper_{model_size}"

    # 检查是否已缓存（在同步上下文中）
    if model_key in _whisper_model_cache:
        model = _whisper_model_cache[model_key]
    else:
        # 加载新模型
        model = whisper.load_model(model_size)
        _whisper_model_cache[model_key] = model

    # 语言参数处理：指定中文或英文，避免误检测
    # 检测语言：如果是中文环境，优先使用中文
    import locale
    system_lang = locale.getdefaultlocale()[0] or ''
    if 'zh' in system_lang or 'CN' in system_lang:
        language_arg = 'zh'  # 强制使用中文
    else:
        language_arg = None  # 自动检测

    # 转写（使用更稳定的参数）
    try:
        result = model.transcribe(
            audio_path,
            language=language_arg,
            word_timestamps=False,
            verbose=False,
            # 添加以下参数提高稳定性
            fp16=False,  # 使用 FP32 避免 FP16 精度问题
            compression_ratio_threshold=2.4,  # 过滤重复内容
            no_speech_threshold=0.6,  # 过滤静音
            condition_on_previous_text=True,  # 基于前文预测
        )
    except RuntimeError as e:
        if "reshape" in str(e) or "0 elements" in str(e):
            # 长音频末尾分块问题：使用标准方法
            raise RuntimeError(f"音频格式兼容问题，请使用标准转写: {e}")
        raise

    # 转换为 Utterance 格式
    utterances = []
    for segment in result.get("segments", []):
        text = segment["text"].strip()
        if text:
            utterances.append(Utterance(
                start=segment["start"],
                end=segment["end"],
                text=text
            ))

    # 构建结果（模仿 TranscriptionResult）
    from dataclasses import dataclass
    from datetime import datetime

    @dataclass
    class FastTranscriptionResult:
        utterances: list
        duration: float
        audio_path: str
        asr_provider: str
        timestamp: str

    return FastTranscriptionResult(
        utterances=utterances,
        duration=duration,
        audio_path=audio_path,
        asr_provider=f"whisper-{model_size}",
        timestamp=datetime.now().isoformat()
    )


def _llm_generate_sync(llm, messages, temperature, max_tokens):
    """同步 LLM 生成（在线程池中运行）"""
    return llm.generate_with_retry(messages=messages, temperature=temperature, max_tokens=max_tokens)


def _create_time_blocks(utterances: list, block_duration_minutes: int = 3) -> list:
    """
    将 utterances 按时间跨度聚合为时间块

    Args:
        utterances: 原始 utterance 列表（Utterance 对象）
        block_duration_minutes: 每块的时长（分钟）

    Returns:
        时间块列表
    """
    if not utterances:
        return []

    block_duration_ms = block_duration_minutes * 60 * 1000
    blocks = []

    current_block = {
        "start_ms": int(utterances[0].start * 1000),
        "end_ms": int(utterances[0].end * 1000),
        "text": "",
    }

    for u in utterances:
        u_start_ms = int(u.start * 1000)
        u_end_ms = int(u.end * 1000)

        # 检查是否应该开始新块
        if u_start_ms >= current_block["start_ms"] + block_duration_ms and current_block["text"]:
            # 保存当前块
            blocks.append({
                "start_ms": current_block["start_ms"],
                "end_ms": current_block["end_ms"],
                "text": current_block["text"].strip()
            })
            # 开始新块
            current_block = {
                "start_ms": u_start_ms,
                "end_ms": u_end_ms,
                "text": "",
            }

        current_block["end_ms"] = max(current_block["end_ms"], u_end_ms)
        current_block["text"] += " " + u.text

    # 添加最后一个块
    if current_block["text"].strip():
        blocks.append({
            "start_ms": current_block["start_ms"],
            "end_ms": current_block["end_ms"],
            "text": current_block["text"].strip()
        })

    return blocks


def _ms_to_mmss(ms: int) -> str:
    """将毫秒转换为 MM:SS 格式"""
    seconds = ms // 1000
    mm = seconds // 60
    ss = seconds % 60
    return f"{mm:02d}:{ss:02d}"


async def _create_enhanced_transcript(utterances: list, llm, base_name: str) -> str:
    """
    创建 LLM 增强的转录文本（带时间戳的纯净实录）

    Args:
        utterances: Whisper 识别的 utterances 列表
        llm: LLM Provider 实例
        base_name: 基础名称（用于缓存）

    Returns:
        增强后的转录文本
    """
    from template.recorder import get_recorder_prompts

    # 创建时间块（每3分钟一块）
    time_blocks = _create_time_blocks(utterances, block_duration_minutes=3)
    print(f"[进程] 创建了 {len(time_blocks)} 个时间块")

    refined_lines = []

    # 处理时间块（添加请求间隔，避免速率限制）
    REQUEST_DELAY = 2  # 秒

    for i, block in enumerate(time_blocks):
        start_time = _ms_to_mmss(block["start_ms"])
        end_time = _ms_to_mmss(block["end_ms"])

        print(f"[进程] 处理块 {i+1}/{len(time_blocks)}: [{start_time} - {end_time}]")

        # 获取提示词
        prompts = get_recorder_prompts(block["text"])

        messages = [
            LLMMessage(role="system", content=prompts["system_prompt"]),
            LLMMessage(role="user", content=prompts["user_prompt"])
        ]

        # 调用 LLM
        try:
            response = await asyncio.to_thread(_llm_generate_sync, llm, messages, 0.3, 2000)
            refined_text = response.content if hasattr(response, 'content') else str(response)
        except Exception as e:
            print(f"[进程] 块 {i+1} 处理失败，使用原文: {e}")
            refined_text = block["text"]

        # 清洗文本
        import re
        refined_text = refined_text.strip()
        refined_text = re.sub(r'\n{3,}', '\n\n', refined_text)

        # 添加时间戳
        refined_line = f"[{start_time} - {end_time}] {refined_text}"
        refined_lines.append(refined_line)

        # 请求之间延迟（最后一个块不需要）
        if i < len(time_blocks) - 1:
            await asyncio.sleep(REQUEST_DELAY)

    return "\n\n".join(refined_lines)


async def process_meeting_real(video_path: str, template_name: str = "general") -> dict:
    """
    使用真实模块处理会议视频（参考 CLI 流程，优化版）

    处理流程：
    1. 提取音频（如果是视频文件）
    2. ASR 转写- 使用缓存的模型，跳过文件 I/O
    3. 构建原始文字稿
    4. 使用 LLM 生成总结

    优化点：
    - Whisper 模型全局缓存，避免重复加载
    - 跳过中间 JSON 文件保存
    - 直接调用 Whisper API

    Args:
        video_path: 视频文件路径
        template_name: 模板名称

    Returns:
        dict: 处理结果
        {
            "transcript_raw": "原始文字稿",
            "transcript_enhanced": "增强文字稿",
            "summaries": [{"role": "产品经理", "content": "..."}],
            "metadata": {"duration": 180.5, "word_count": 5000, ...}
        }

    Raises:
        FileNotFoundError: 文件不存在
        RuntimeError: 处理失败
    """
    import time
    start_time = time.time()

    # 阶段 1: 提取音频（参考 CLI 第 409-417 行）
    path = Path(video_path)
    ext = path.suffix.lower()

    if ext in ['.mp4', '.mkv', '.mov']:
        print(f"[进程] 正在从视频提取音频: {path.name}")
        audio_result = await asyncio.to_thread(_extract_audio_sync, video_path)
        audio_path = audio_result.path
        duration = audio_result.duration
        print(f"[进程] 音频提取完成，时长: {duration:.1f}秒")
    else:
        audio_path = video_path
        # 对于音频文件，获取时长
        from audio.extract_audio import _get_audio_duration
        duration = _get_audio_duration(audio_path)

    # 阶段 2: ASR 转写（使用优化的快速转写函数）
    model_size = os.environ.get("WHISPER_MODEL", "base")
    print(f"[进程] 正在加载 Whisper 模型 ({model_size}) 并转写...")

    # 检查音频时长，长音频使用标准方法（更稳定）
    if duration and duration > 1800:  # 超过 30 分钟
        print(f"[进程] 检测到长音频 ({duration/60:.1f}分钟)，使用标准转写方法")
        transcript_result = await asyncio.to_thread(_transcribe_sync, audio_path, model_size)
    else:
        try:
            transcript_result = await asyncio.to_thread(_transcribe_fast_sync, audio_path, model_size)
        except Exception as e:
            print(f"[进程] 快速转写失败: {e}")
            print(f"[进程] 回退到标准转写方法...")
            # 回退到原始方法（可能有更好的兼容性）
            transcript_result = await asyncio.to_thread(_transcribe_sync, audio_path, model_size)

    # 构建原始文字稿（参考 CLI 第 452-455 行）
    utterances = transcript_result.utterances
    print(f"[进程] ASR 转写完成，识别到 {len(utterances)} 条语句")

    transcript_raw = "\n".join([
        f"[{u.start:.1f}s - {u.end:.1f}s] {u.text}"
        for u in utterances
    ])

    # 创建 LLM 增强文字稿
    print(f"[进程] 正在生成 LLM 增强文字稿...")
    llm = create_llm_provider(os.environ.get("DEFAULT_LLM_PROVIDER", "mock"))
    base_name = path.stem  # 视频文件名（不含扩展名）
    transcript_enhanced = await _create_enhanced_transcript(utterances, llm, base_name)

    # 阶段 3: 获取模板并生成总结
    template = _get_template_by_name(template_name)

    llm_provider_name = getattr(llm, 'name', 'unknown')
    llm_model_name = getattr(llm, 'model', 'unknown')
    print(f"[进程] 正在生成总结 (LLM: {llm_provider_name}/{llm_model_name})...")

    # 构建 Prompt（参考 CLI 第 543-548 行）
    prompt = (
        f"你是一名专业会议分析助手。请从【{template.name}】的视角总结以下会议内容。\n"
        f"总结要求：{template.description}。\n"
        f"请使用结构化方式输出。\n\n"
        f"会议内容：\n{transcript_raw}"
    )

    # 调用 LLM
    messages = [LLMMessage(role="user", content=prompt)]
    response = await asyncio.to_thread(_llm_generate_sync, llm, messages, 0.3, 4000)

    # 返回结果
    processing_time = time.time() - start_time
    print(f"[进程] 处理完成！总耗时: {processing_time:.1f}秒")

    return {
        "transcript_raw": transcript_raw,
        "transcript_enhanced": transcript_enhanced,  # LLM 增强后的文字稿
        "summaries": [
            {
                "role": template.name,
                "content": response.content if hasattr(response, 'content') else str(response)
            }
        ],
        "metadata": {
            "duration": transcript_result.duration,
            "word_count": sum(len(u.text.split()) for u in utterances),
            "processing_time": processing_time,
            "llm_provider": str(llm_provider_name),
            "llm_model": str(llm_model_name)
        }
    }


# ============================================================
# 异步任务处理
# ============================================================

async def process_meeting_task(
    meeting_id: int,
    video_path: str,
    db: Session
):
    """
    异步会议处理任务（使用真实 ASR 和 LLM 模块）
    =================================================
    流程：
    1. 更新状态为 processing
    2. 调用真实模块处理视频（ASR + LLM）
    3. 解析结果并存储到数据库
    4. 更新状态为 completed/failed

    Args:
        meeting_id: 会议 ID
        video_path: 视频文件路径
        db: 数据库会话
    """
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        return

    try:
        print(f"\n{'='*60}")
        print(f"🎬 开始处理会议 #{meeting_id}: {meeting.title}")
        print(f"📁 文件: {video_path}")
        print(f"{'='*60}")

        # 更新状态：处理中
        meeting.status = "processing"
        meeting.progress = 5
        db.commit()

        # 🚀 调用真实模块处理（带进度更新）
        meeting.progress = 10
        db.commit()

        result_data = await process_meeting_real(
            video_path=video_path,
            template_name="general"  # 使用默认模板
        )

        meeting.progress = 90
        db.commit()

        # 解析结果并存储
        result = Result(
            meeting_id=meeting_id,
            transcript_raw=result_data.get("transcript_raw", ""),
            transcript_enhanced=result_data.get("transcript_enhanced"),
            summary_json={"templates": result_data.get("summaries", [])},
            llm_provider=result_data.get("metadata", {}).get("llm_provider"),
            llm_model=result_data.get("metadata", {}).get("llm_model"),
            processing_time=result_data.get("metadata", {}).get("processing_time"),
            word_count=result_data.get("metadata", {}).get("word_count"),
        )
        db.add(result)

        # 更新会议元数据
        meeting.duration = result_data.get("metadata", {}).get("duration")
        meeting.status = "completed"
        meeting.progress = 100
        db.commit()

        print(f"✅ 会议 #{meeting_id} 处理完成！")
        print(f"{'='*60}\n")

    except Exception as e:
        # 处理失败
        meeting.status = "failed"
        meeting.error_message = str(e)
        meeting.progress = 0
        db.commit()
        print(f"❌ 会议处理失败 (ID: {meeting_id}): {e}")
        import traceback
        traceback.print_exc()


# ============================================================
# API 路由端点
# ============================================================

@app.get("/", tags=["根路径"])
async def root():
    """根路径：返回 API 信息"""
    return {
        "name": "Jinni 会议精灵 API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "github": "https://github.com/your-repo/jinni-meeting-assistant"
    }


@app.get("/health", tags=["健康检查"])
async def health_check():
    """健康检查端点"""
    # 检查依赖
    ffmpeg_available = False
    try:
        from audio.extract_audio import is_ffmpeg_available
        ffmpeg_available = is_ffmpeg_available()
    except Exception:
        pass

    whisper_available = False
    try:
        import whisper
        whisper_available = True
    except ImportError:
        pass

    llm_provider = os.environ.get("DEFAULT_LLM_PROVIDER", "mock")

    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "modules": {
            "ffmpeg": "available" if ffmpeg_available else "not available",
            "whisper": "available" if whisper_available else "not available",
            "llm_provider": llm_provider
        }
    }


@app.post("/api/upload", response_model=MeetingResponse, tags=["会议管理"])
async def upload_meeting(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="音视频文件 (mp4/wav/mp3/m4a)"),
    title: str = Form(..., description="会议标题"),
    db: Session = Depends(get_db),
):
    """
    上传会议音视频文件
    ====================
    1. 验证文件格式和大小
    2. 保存到 storage/videos/
    3. 创建数据库记录
    4. 触发后台异步处理任务

    Args:
        file: 上传的音视频文件
        title: 会议标题
        db: 数据库会话

    Returns:
        MeetingResponse: 创建的会议记录
    """
    # 文件扩展名验证
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件格式: {file_ext}，请上传 {ALLOWED_EXTENSIONS} 格式"
        )

    # 文件大小验证（在上传前检查）
    content = await file.read()
    file_size = len(content)
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"文件大小超过限制 ({MAX_FILE_SIZE / (1024**3):.1f}GB)"
        )

    # 生成唯一文件名（防止冲突）
    unique_filename = f"{uuid.uuid4().hex}{file_ext}"
    video_path = VIDEO_DIR / unique_filename

    # 保存文件
    try:
        with open(video_path, "wb") as buffer:
            buffer.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件保存失败: {str(e)}")

    # 创建数据库记录
    meeting = Meeting(
        title=title,
        video_path=str(video_path.relative_to(BASE_DIR)),  # 存储相对路径
        video_size=file_size,
        status="pending",
        progress=0,
    )
    db.add(meeting)
    db.commit()
    db.refresh(meeting)

    # 添加后台处理任务（异步执行，不阻塞响应）
    background_tasks.add_task(
        process_meeting_task,
        meeting_id=meeting.id,
        video_path=str(video_path),
        db=db,
    )

    return meeting


@app.get("/api/history", response_model=List[MeetingResponse], tags=["会议管理"])
async def get_history(
    skip: int = 0,
    limit: int = 50,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    获取会议历史记录
    =================
    支持分页和关键词搜索

    Args:
        skip: 跳过记录数（分页偏移）
        limit: 返回记录数（默认 50）
        search: 搜索关键词（匹配会议标题）
        db: 数据库会话

    Returns:
        List[MeetingResponse]: 会议记录列表
    """
    query = db.query(Meeting)

    # 关键词搜索
    if search:
        query = query.filter(Meeting.title.contains(search))

    # 排序：最新优先
    query = query.order_by(Meeting.created_at.desc())

    # 分页
    meetings = query.offset(skip).limit(limit).all()

    return [m.to_dict() for m in meetings]


@app.get("/api/meetings/{meeting_id}", response_model=MeetingDetailResponse, tags=["会议管理"])
async def get_meeting_detail(meeting_id: int, db: Session = Depends(get_db)):
    """
    获取会议详情（包含处理结果）
    =============================
    Args:
        meeting_id: 会议 ID
        db: 数据库会话

    Returns:
        MeetingDetailResponse: 会议详情及结果
    """
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()

    if not meeting:
        raise HTTPException(status_code=404, detail="会议不存在")

    response_data = meeting.to_dict()
    response_data["results"] = [r.to_dict() for r in meeting.results]

    return response_data


@app.get("/api/meetings/{meeting_id}/status", tags=["会议管理"])
async def get_meeting_status(meeting_id: int, db: Session = Depends(get_db)):
    """
    获取会议处理状态（用于轮询）
    =========================
    Args:
        meeting_id: 会议 ID
        db: 数据库会话

    Returns:
        dict: {status, progress, error_message}
    """
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()

    if not meeting:
        raise HTTPException(status_code=404, detail="会议不存在")

    return {
        "meeting_id": meeting.id,
        "status": meeting.status,
        "progress": meeting.progress,
        "error_message": meeting.error_message,
        "updated_at": meeting.updated_at.isoformat() if meeting.updated_at else None,
    }


@app.delete("/api/meetings/{meeting_id}", tags=["会议管理"])
async def delete_meeting(meeting_id: int, db: Session = Depends(get_db)):
    """
    删除会议记录（级联删除关联结果）
    =============================
    Args:
        meeting_id: 会议 ID
        db: 数据库会话
    """
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()

    if not meeting:
        raise HTTPException(status_code=404, detail="会议不存在")

    # 删除视频文件
    video_full_path = BASE_DIR / meeting.video_path
    if video_full_path.exists():
        try:
            video_full_path.unlink()
        except Exception as e:
            print(f"警告：视频文件删除失败: {e}")

    # 删除数据库记录（级联删除结果）
    db.delete(meeting)
    db.commit()

    return {"message": f"会议 {meeting_id} 已删除"}


# ============================================================
# 模板管理 API
# ============================================================

class TemplateCreate(BaseModel):
    """创建模板请求模型"""
    name: str
    description: str


class TemplateResponse(BaseModel):
    """模板响应模型"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str
    is_system: int
    created_at: datetime
    updated_at: datetime


@app.get("/api/templates", response_model=List[TemplateResponse], tags=["模板管理"])
async def get_templates(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """
    获取所有模板
    =============
    Args:
        skip: 跳过记录数
        limit: 返回记录数
        db: 数据库会话

    Returns:
        List[TemplateResponse]: 模板列表
    """
    templates = db.query(Template).order_by(Template.created_at.desc()).offset(skip).limit(limit).all()
    return [t.to_dict() for t in templates]


@app.get("/api/templates/{template_id}", response_model=TemplateResponse, tags=["模板管理"])
async def get_template(template_id: int, db: Session = Depends(get_db)):
    """获取单个模板详情"""
    template = db.query(Template).filter(Template.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    return template.to_dict()


@app.post("/api/templates", response_model=TemplateResponse, tags=["模板管理"])
async def create_template(
    template_data: TemplateCreate,
    db: Session = Depends(get_db),
):
    """
    创建新模板
    ===========
    Args:
        template_data: 模板数据（名称、描述）
        db: 数据库会话

    Returns:
        TemplateResponse: 创建的模板
    """
    template = Template(
        name=template_data.name,
        description=template_data.description,
        is_system=0,  # 用户创建的模板
    )
    db.add(template)
    db.commit()
    db.refresh(template)
    return template.to_dict()


@app.put("/api/templates/{template_id}", response_model=TemplateResponse, tags=["模板管理"])
async def update_template(
    template_id: int,
    template_data: TemplateCreate,
    db: Session = Depends(get_db),
):
    """更新模板"""
    template = db.query(Template).filter(Template.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")

    template.name = template_data.name
    template.description = template_data.description
    db.commit()
    db.refresh(template)
    return template.to_dict()


@app.delete("/api/templates/{template_id}", tags=["模板管理"])
async def delete_template(template_id: int, db: Session = Depends(get_db)):
    """删除模板"""
    template = db.query(Template).filter(Template.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")

    db.delete(template)
    db.commit()
    return {"message": f"模板 {template_id} 已删除"}


# ============================================================
# 结果管理 API
# ============================================================

@app.get("/api/results/{result_id}", response_model=ResultResponse, tags=["结果管理"])
async def get_result(result_id: int, db: Session = Depends(get_db)):
    """获取处理结果详情"""
    result = db.query(Result).filter(Result.id == result_id).first()
    if not result:
        raise HTTPException(status_code=404, detail="结果不存在")
    return result.to_dict()


# ============================================================
# 简化的会议列表 API
# ============================================================

@app.get("/api/meetings", response_model=List[MeetingResponse], tags=["会议管理"])
async def get_all_meetings(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """
    获取所有会议（简化版，用于会议库）
    ====================================
    Args:
        skip: 跳过记录数
        limit: 返回记录数
        db: 数据库会话

    Returns:
        List[MeetingResponse]: 会议列表
    """
    meetings = db.query(Meeting).order_by(Meeting.created_at.desc()).offset(skip).limit(limit).all()
    return [m.to_dict() for m in meetings]


# ============================================================
# 转录 API（单独提取文字稿）
# ============================================================

@app.post("/api/meetings/{meeting_id}/transcribe", tags=["会议管理"])
async def transcribe_meeting(
    meeting_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    提取会议文字稿
    ==============
    Args:
        meeting_id: 会议 ID
        background_tasks: 后台任务
        db: 数据库会话

    Returns:
        dict: 处理状态
    """
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="会议不存在")

    # 检查是否已有结果
    if meeting.results:
        return {"message": "文字稿已存在", "meeting_id": meeting_id}

    # 触发后台处理
    background_tasks.add_task(
        process_meeting_task,
        meeting_id=meeting_id,
        video_path=str(BASE_DIR / meeting.video_path),
        db=db,
    )

    return {"message": "文字稿提取已启动", "meeting_id": meeting_id}


# ============================================================
# 总结 API（基于模板生成总结）
# ============================================================

@app.post("/api/meetings/{meeting_id}/summarize", tags=["会议管理"])
async def summarize_meeting(
    meeting_id: int,
    template_id: int = Query(..., description="模板 ID"),
    db: Session = Depends(get_db),
):
    """
    基于模板生成会议总结（使用真实 LLM）
    =====================================
    Args:
        meeting_id: 会议 ID
        template_id: 模板 ID
        db: 数据库会话

    Returns:
        dict: 生成的总结
    """
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="会议不存在")

    template = db.query(Template).filter(Template.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")

    # 获取文字稿
    if not meeting.results:
        raise HTTPException(status_code=400, detail="请先提取文字稿")

    result = meeting.results[0]
    transcript_text = result.transcript_raw

    try:
        # 创建 LLM Provider
        llm = create_llm_provider(os.environ.get("DEFAULT_LLM_PROVIDER", "mock"))

        # 构建 Prompt
        prompt = (
            f"你是一名专业会议分析助手。请从【{template.name}】的视角总结以下会议内容。\n"
            f"总结要求：{template.description}。\n"
            f"请使用结构化方式输出。\n\n"
            f"会议内容：\n{transcript_text}"
        )

        # 调用 LLM（使用 asyncio.to_thread 避免阻塞）
        messages = [LLMMessage(role="user", content=prompt)]
        response = await asyncio.to_thread(_llm_generate_sync, llm, messages, 0.3, 4000)

        summary_content = response.content if hasattr(response, 'content') else str(response)

        # 获取 LLM provider 信息
        llm_provider_name = str(getattr(llm, 'name', 'unknown'))
        llm_model_name = str(getattr(llm, 'model', 'unknown'))

        # 保存总结到数据库
        summary = Summary(
            meeting_id=meeting_id,
            template_id=template_id,
            content=summary_content,
            llm_provider=llm_provider_name,
            llm_model=llm_model_name,
        )
        db.add(summary)
        db.commit()

        return {
            "meeting_id": meeting_id,
            "template_id": template_id,
            "summary_id": summary.id,
            "summary": summary_content,
            "llm_provider": llm_provider_name,
            "llm_model": llm_model_name,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM 生成失败: {str(e)}")


@app.get("/api/meetings/{meeting_id}/summaries", tags=["会议管理"])
async def get_meeting_summaries(
    meeting_id: int,
    db: Session = Depends(get_db),
):
    """
    获取会议的所有总结
    ==================
    Args:
        meeting_id: 会议 ID
        db: 数据库会话

    Returns:
        list: 总结列表（包含模板信息）
    """
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="会议不存在")

    # 获取该会议的所有总结，并关联模板信息
    summaries = db.query(Summary).filter(Summary.meeting_id == meeting_id).order_by(Summary.created_at.desc()).all()

    result = []
    for summary in summaries:
        template = db.query(Template).filter(Template.id == summary.template_id).first()
        result.append({
            "id": summary.id,
            "template_id": summary.template_id,
            "template_name": template.name if template else "未知模板",
            "content": summary.content,
            "llm_provider": summary.llm_provider,
            "llm_model": summary.llm_model,
            "created_at": summary.created_at.isoformat() if summary.created_at else None,
        })

    return result


# ============================================================
# 启动入口
# ============================================================

if __name__ == "__main__":
    import uvicorn

    llm_provider = os.environ.get("DEFAULT_LLM_PROVIDER", "mock")
    whisper_model = os.environ.get("WHISPER_MODEL", "base")

    print(f"""
    ╔════════════════════════════════════════════════════════════╗
    ║           🧞 Jinni 会议精灵 - Web 后端服务                   ║
    ╠════════════════════════════════════════════════════════════╣
    ║  API 文档: http://localhost:8000/docs                        ║
    ║  ReDoc:   http://localhost:8000/redoc                        ║
    ║                                                               ║
    ║  🔧 ASR 模块: Whisper ({whisper_model}) + 模型缓存             ║
    ║  🤖 LLM Provider: {llm_provider:<12}                           ║
    ║  ⚡ 优化: 跳过文件 I/O，直接内存处理                          ║
    ╚════════════════════════════════════════════════════════════╝
    """)

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # 开发模式自动重载
    )
