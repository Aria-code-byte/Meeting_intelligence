"""
Jinni Meeting Intelligence - Backend API
==========================================
最小可用后端服务 - 支持 P0 + P1 接口

启动方式:
    python -m uvicorn main:app --reload --port 8000
"""

import os
import time
import uuid
import asyncio
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Any

# 加载 .env 文件
# 阶段 10B-5-Q5-R2：修复环境变量加载路径
try:
    from dotenv import load_dotenv
    from pathlib import Path

    # 获取项目根目录和backend目录
    current_file = Path(__file__).resolve()
    backend_dir = current_file.parent
    project_root = backend_dir.parent

    # 按优先级加载 .env 文件
    # 1. 项目根目录 .env（优先级最高）
    # 2. backend/.env（可以覆盖项目配置）
    # 3. 当前工作目录 .env（最低优先级，避免冲突）

    env_files = [
        project_root / ".env",
        backend_dir / ".env",
        Path(".env"),  # 当前工作目录
    ]

    for env_file in env_files:
        if env_file.exists():
            print(f"[Config] Loading .env from: {env_file}")
            load_dotenv(env_file, override=False)
        else:
            print(f"[Config] .env not found: {env_file}")

    # 阶段 10B-5-Q5-R2：输出 HF token 配置状态（安全日志）
    hf_token = os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_TOKEN") or os.getenv("HUGGINGFACEHUB_API_TOKEN")
    if hf_token:
        # 只显示前4位和后4位
        masked_token = f"{hf_token[:4]}...{hf_token[-4:]}" if len(hf_token) > 8 else f"{hf_token[:4]}..."
        print(f"[Config] HF token found: true, source: masked={masked_token}")
    else:
        print(f"[Config] HF token found: false, diarization may be skipped")

except ImportError:
    print("[Config] python-dotenv not available, using system environment variables only")
    pass  # 如果没有 python-dotenv，跳过环境变量加载

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import sys
from pathlib import Path

# 添加项目根目录到Python路径，以便导入asr模块
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "backend"))

from backend.llm_client import LLMClient

# 添加项目根目录到Python路径，以便导入asr模块
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from asr.transcribe import transcribe

# 导入提供商适配层（新的API路由）
try:
    from api_routes import api_router
    API_ROUTES_AVAILABLE = True
except ImportError:
    print("[WARNING] api_routes not available, provider adapter layer disabled")
    API_ROUTES_AVAILABLE = False

# ============================================================
# 配置
# ============================================================

BASE_DIR = Path(__file__).parent.parent
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

# 允许的文件格式
ALLOWED_EXTENSIONS = {'mp3', 'wav', 'mp4', 'm4a', 'webm'}

# 文件大小限制 (3GB)
MAX_FILE_SIZE = 3 * 1024 * 1024 * 1024

# ============================================================
# 内存存储（本阶段使用，后续替换为数据库）
# ============================================================

MEETINGS: Dict[str, Dict[str, Any]] = {}
TRANSCRIPTION_TASKS: Dict[str, Dict[str, Any]] = {}
SUMMARY_TASKS: Dict[str, Dict[str, Any]] = {}

# ============================================================
# FastAPI 应用
# ============================================================

llm_client = LLMClient()

app = FastAPI(
    title="Jinni Meeting Intelligence API",
    description="AI 会议智能后端服务",
    version="1.0.0"
)

# 注册新的API路由（提供商适配层）
if API_ROUTES_AVAILABLE:
    app.include_router(api_router)  # api_router 已经定义了 prefix="/api/v1"
    print("[INFO] Provider adapter API routes registered at /api/v1/*")

# 注册优化服务路由
try:
    from backend.enhancement_service import router as enhancement_router
    app.include_router(enhancement_router)
    print("[INFO] Enhancement service routes registered at /api/v1/enhancement/*")
except ImportError:
    print("[WARNING] enhancement_service not available")

# ============================================================
# CORS 配置
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8501",  # Streamlit 前端
        "http://127.0.0.1:8501",
        # Vite React 前端（支持多个端口）
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:5175",
        "http://127.0.0.1:5175",
        "http://localhost:5176",
        "http://127.0.0.1:5176",
        "http://localhost:5177",
        "http://127.0.0.1:5177",
        "http://localhost:5178",
        "http://127.0.0.1:5178",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# Pydantic 模型
# ============================================================

class TranscribeRequest(BaseModel):
    """启动转录请求"""
    pass  # 当前无需参数

class SummarizeRequest(BaseModel):
    """启动总结生成请求"""
    template_id: str
    template: Optional[Dict[str, Any]] = None
    transcript: Optional[str] = None
    output_format: str = "markdown"

# ============================================================
# 工具函数
# ============================================================

def validate_file_format(filename: str) -> bool:
    """验证文件格式"""
    ext = filename.split('.')[-1].lower() if '.' in filename else ''
    return ext in ALLOWED_EXTENSIONS

def format_file_size(size_bytes: int) -> str:
    """格式化文件大小"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.2f} TB"

def generate_meeting_id() -> str:
    """生成会议 ID"""
    return f"meeting_{uuid.uuid4().hex[:12]}"

def generate_task_id(task_type: str) -> str:
    """生成任务 ID"""
    return f"{task_type}_{uuid.uuid4().hex[:12]}"

# ============================================================
# 后台任务模拟
# ============================================================

def real_transcription_task(meeting_id: str, task_id: str, audio_path: str):
    """真实转录任务 - 使用 Whisper ASR"""
    task = TRANSCRIPTION_TASKS.get(task_id)
    if not task:
        return

    print(f"[BACKEND] using real ASR for transcription")
    print(f"[BACKEND] audio file: {audio_path}")

    try:
        # 更新进度
        task["progress"] = 20
        task["current_step"] = "正在加载ASR模型"

        # 调用ASR转录
        print(f"[BACKEND] calling ASR API...")
        result = transcribe(
            audio_path=audio_path,
            provider="whisper",  # 使用whisper或faster-whisper
            language="zh",  # 中文
            model_size="base",  # 模型大小: tiny/base/small/medium/large
            enable_postprocess=True  # 启用后处理
        )

        # 更新进度
        task["progress"] = 70
        task["current_step"] = "正在整理文字稿"

        # 格式化转录结果
        utterances = result.utterances

        # 构建完整转录文本
        transcript_lines = []
        segments = []

        for utterance in utterances:
            timestamp = utterance.start_time
            speaker = getattr(utterance, 'speaker', 'Speaker')
            text = utterance.text

            # 格式化时间戳
            minutes = int(timestamp // 60)
            seconds = int(timestamp % 60)
            time_str = f"{minutes:02d}:{seconds:02d}"

            # 添加到完整转录
            transcript_lines.append(f"[{time_str}] {speaker}：{text}")

            # 添加到分段
            segments.append({
                "start": time_str,
                "speaker": speaker,
                "text": text
            })

        full_transcript = "\n".join(transcript_lines)

        # 保存转录结果
        print(f"[BACKEND] transcription completed: {len(utterances)} segments")
        MEETINGS[meeting_id]["transcript"] = full_transcript
        MEETINGS[meeting_id]["segments"] = segments
        MEETINGS[meeting_id]["transcription_completed_at"] = datetime.now().isoformat()
        MEETINGS[meeting_id]["audio_duration"] = result.duration

        # 完成任务
        task["progress"] = 100
        task["current_step"] = "转录完成"
        task["status"] = "completed"

        print(f"[BACKEND] transcription task completed")

    except Exception as e:
        print(f"[BACKEND] ERROR: transcription failed: {str(e)}")
        task["status"] = "failed"
        task["current_step"] = f"转录失败: {str(e)}"


def simulate_transcription_task(meeting_id: str, task_id: str):
    """模拟转录任务进度"""
    print(f"[BACKEND] using mock transcription (no real ASR)")
    task = TRANSCRIPTION_TASKS.get(task_id)
    if not task:
        return

    # 模拟进度：0% → 20% → 45% → 70% → 90% → 100%
    progress_steps = [20, 45, 70, 90, 100]
    step_messages = {
        20: "正在分析音频文件",
        45: "正在识别语音内容",
        70: "正在分离发言人",
        90: "正在整理文字稿",
        100: "转录完成"
    }

    for progress in progress_steps:
        time.sleep(4)  # 每 4 秒更新一次进度
        task["progress"] = progress
        task["current_step"] = step_messages.get(progress, "处理中")
        task["status"] = "completed" if progress >= 100 else "processing"

    # 生成 Mock 转录结果
    mock_transcript = """[00:00:01] 老师：同学们好，今天我们来讲线性代数中的矩阵运算。
[00:00:15] 老师：首先，我们回顾一下上节课讲过的矩阵加法和数乘运算。
[00:00:45] 老师：矩阵加法要求两个矩阵的维度相同，对应位置元素相加即可。
[00:01:20] 学生A：老师，那矩阵乘法呢？是不是也是这样对应位置相乘？
[00:01:35] 老师：这是个很好的问题！矩阵乘法不是对应位置相乘，而是行乘以列的运算。
[00:02:10] 老师：比如一个 2x3 矩阵乘以一个 3x2 矩阵，结果是 2x2 矩阵。
[00:02:45] 学生B：老师，能再举个例子吗？这个概念有点抽象。
[00:03:15] 老师：当然可以。假设矩阵 A 是 [[1,2],[3,4]]，矩阵 B 是 [[5,6],[7,8]]...
[00:04:00] 老师：好了，今天的内容就讲到这里。课后作业是课本第 45 页的练习题 1-5。
[00:04:30] 学生C：老师，下节课会讲矩阵的逆运算吗？
[00:04:45] 老师：是的，下节课我们专门讲解矩阵的逆运算和行列式。"""

    mock_segments = [
        {"start": "00:00:01", "speaker": "老师", "text": "同学们好，今天我们来讲线性代数中的矩阵运算。"},
        {"start": "00:00:15", "speaker": "老师", "text": "首先，我们回顾一下上节课讲过的矩阵加法和数乘运算。"},
        {"start": "00:00:45", "speaker": "老师", "text": "矩阵加法要求两个矩阵的维度相同，对应位置元素相加即可。"},
        {"start": "00:01:20", "speaker": "学生A", "text": "老师，那矩阵乘法呢？是不是也是这样对应位置相乘？"},
        {"start": "00:01:35", "speaker": "老师", "text": "这是个很好的问题！矩阵乘法不是对应位置相乘，而是行乘以列的运算。"},
        {"start": "00:02:10", "speaker": "老师", "text": "比如一个 2x3 矩阵乘以一个 3x2 矩阵，结果是 2x2 矩阵。"},
        {"start": "00:02:45", "speaker": "学生B", "text": "老师，能再举个例子吗？这个概念有点抽象。"},
        {"start": "00:03:15", "speaker": "老师", "text": "当然可以。假设矩阵 A 是 [[1,2],[3,4]]，矩阵 B 是 [[5,6],[7,8]]..."},
        {"start": "00:04:00", "speaker": "老师", "text": "好了，今天的内容就讲到这里。课后作业是课本第 45 页的练习题 1-5。"},
        {"start": "00:04:30", "speaker": "学生C", "text": "老师，下节课会讲矩阵的逆运算吗？"},
        {"start": "00:04:45", "speaker": "老师", "text": "是的，下节课我们专门讲解矩阵的逆运算和行列式。"}
    ]

    # 保存转录结果到会议记录
    MEETINGS[meeting_id]["transcript"] = mock_transcript
    MEETINGS[meeting_id]["segments"] = mock_segments
    MEETINGS[meeting_id]["transcription_completed_at"] = datetime.now().isoformat()

def real_summary_task(meeting_id: str, task_id: str, template_id: str):
    """真实总结生成任务 - 使用 LLM"""
    task = SUMMARY_TASKS.get(task_id)
    if not task:
        return

    print(f"[BACKEND] ========== REAL SUMMARY TASK STARTED ==========")
    print(f"[BACKEND] using real LLM for summary")
    print(f"[BACKEND] meeting_id: {meeting_id}")
    print(f"[BACKEND] template_id: {template_id}")
    print(f"[BACKEND] llm_provider: {llm_client.provider}")

    meeting = MEETINGS.get(meeting_id)
    if not meeting:
        print(f"[BACKEND] ERROR: meeting {meeting_id} not found")
        return

    transcript = meeting.get("transcript", "")
    if not transcript:
        print(f"[BACKEND] ERROR: no transcript for meeting {meeting_id}")
        return

    print(f"[BACKEND] transcript length: {len(transcript)}")
    print(f"[BACKEND] transcript preview: {transcript[:200]}...")

    # 获取模板信息
    template = get_template_by_id(template_id)
    if not template:
        print(f"[BACKEND] WARNING: template {template_id} not found, using default")
        template = {
            "name": "通用会议纪要",
            "description": "默认通用模板",
            "sections": ["会议摘要", "关键讨论", "决策结论", "待办事项"],
            "prompt": "请总结本次会议的要点。"
        }

    print(f"[BACKEND] template_name: {template.get('name', '')}")
    print(f"[BACKEND] template_sections: {template.get('sections', [])}")

    try:
        # 更新进度
        task["progress"] = 25
        task["current_step"] = "正在分析会议内容"

        # 调用 LLM 生成总结
        print(f"[BACKEND] calling LLM API...")
        print(f"[BACKEND] LLM provider: {llm_client.provider}")
        if llm_client.provider == "ollama":
            print(f"[BACKEND] Ollama URL: {llm_client.ollama_base_url}")
            print(f"[BACKEND] Ollama model: {llm_client.ollama_model}")
        elif llm_client.provider == "openai":
            print(f"[BACKEND] OpenAI URL: {llm_client.base_url}")
            print(f"[BACKEND] OpenAI model: {llm_client.model}")

        summary = llm_client.generate_summary(
            transcript=transcript,
            template_name=template.get("name", ""),
            template_description=template.get("description", ""),
            template_sections=template.get("sections", []),
            template_prompt=template.get("prompt", "")
        )

        # 更新进度
        task["progress"] = 75
        task["current_step"] = "正在整理总结格式"

        # 保存总结
        print(f"[BACKEND] summary generated successfully: length={len(summary)}")
        print(f"[BACKEND] summary preview: {summary[:300]}...")
        MEETINGS[meeting_id]["summary"] = summary
        MEETINGS[meeting_id]["summary_markdown"] = summary
        MEETINGS[meeting_id]["template_id"] = template_id
        MEETINGS[meeting_id]["summary_completed_at"] = datetime.now().isoformat()

        # 完成任务
        task["progress"] = 100
        task["current_step"] = "总结生成完成"
        task["status"] = "completed"

        print(f"[BACKEND] ========== REAL SUMMARY TASK COMPLETED ==========")

    except Exception as e:
        print(f"[BACKEND] ========== REAL SUMMARY TASK FAILED ==========")
        print(f"[BACKEND] ERROR: summary generation failed: {str(e)}")
        task["status"] = "failed"
        task["current_step"] = f"总结生成失败: {str(e)}"


def get_template_by_id(template_id: str) -> Optional[dict]:
    """根据ID获取模板（包含自定义模板）"""
    # 从所有模板中查找（包括自定义模板）
    all_templates = get_all_templates()
    template = next((t for t in all_templates if t["id"] == template_id), None)

    if template:
        return {
            "name": template.get("name", ""),
            "description": template.get("description", ""),
            "sections": template.get("sections", []),
            "prompt": template.get("prompt", "")
        }

    return None


def simulate_summary_task(meeting_id: str, task_id: str, template_id: str):
    """模拟总结生成任务进度"""
    print(f"[BACKEND] using mock summary (no real LLM)")
    task = SUMMARY_TASKS.get(task_id)
    if not task:
        return

    # 模拟进度：0% → 25% → 50% → 75% → 100%
    progress_steps = [25, 50, 75, 100]
    step_messages = {
        25: "正在分析会议主题",
        50: "正在提取关键讨论",
        75: "正在识别决策结论",
        100: "总结生成完成"
    }

    for progress in progress_steps:
        time.sleep(5)  # 每 5 秒更新一次进度
        task["progress"] = progress
        task["current_step"] = step_messages.get(progress, "处理中")
        task["status"] = "completed" if progress >= 100 else "processing"

    # 根据 template_id 生成对应的总结
    template_summaries = {
        "general_meeting": """# 会议总结

## 一、会议摘要

本次会议主要围绕产品需求、开发计划与后续风险展开讨论。团队确认了第一版原型的交付目标，并明确了前后端分工。

## 二、关键讨论内容

- 产品第一版原型需要在下周前完成
- 前端与后端需要并行推进
- 后续需要持续同步开发进度

## 三、决策结论

- 确认下周前完成第一版原型
- 前端开发由 Speaker 2 负责
- 后端 API 由 Speaker 1 负责

## 四、待办事项

- Speaker 2：完成前端页面开发
- Speaker 1：完成后端 API 开发
- 全体：明天同步开发进度

## 五、风险与问题

- 开发时间较紧，需要控制需求范围
- 前后端接口需要尽早对齐

## 六、会议结论

团队已明确下一步开发目标与责任分工，后续将通过每日同步推进项目进展。""",

        "weekly_meeting": """# 周会总结

## 本周亮点

- 完成了第一版原型设计
- 确定了前后端技术栈
- 制定了下周开发计划

## 遇到的问题

- 开发时间较为紧张
- 需求范围还需要进一步明确
- 团队协作流程需要优化

## 下周计划

- Speaker 2：前端页面开发
- Speaker 1：后端 API 开发
- 全体：每日进度同步会议""",

        "project_review": """# 项目评审总结

## 项目进展

- 已完成需求分析和原型设计
- 开发团队已组建完成
- 技术方案已确定

## 关键里程碑

- 第一版原型：下周交付
- Beta 测试：两周后启动
- 正式发布：一个月后上线

## 风险评估

- 开发时间紧张 ⚠️
- 需求变更频繁 ⚠️
- 团队协作待优化

## 下一步计划

- 按优先级排定需求
- 建立每日站会制度
- 设立每周里程碑检查点""",

        "default": """# 会议总结

## 一、会议摘要

本次会议圆满结束，团队明确了下一步工作方向。

## 二、关键讨论内容

- 确认了项目目标和时间表
- 分配了团队成员责任
- 讨论了潜在风险和解决方案

## 三、决策结论

- 确认项目按计划推进
- 建立定期沟通机制

## 四、待办事项

- 按照分配的任务推进工作
- 定期同步项目进度
- 及时处理遇到的问题"""
    }

    # 获取模板对应的总结，如果没有则使用默认模板
    mock_summary = template_summaries.get(template_id, template_summaries["default"])

    # 保存总结结果到会议记录
    print(f"[BACKEND] summary generated (mock): length={len(mock_summary)}")
    MEETINGS[meeting_id]["summary"] = mock_summary
    MEETINGS[meeting_id]["summary_markdown"] = mock_summary
    MEETINGS[meeting_id]["template_id"] = template_id
    MEETINGS[meeting_id]["summary_completed_at"] = datetime.now().isoformat()

# ============================================================
# 1. 健康检查
# ============================================================

@app.get("/health")
async def health_check():
    """健康检查接口"""
    return {
        "status": "ok",
        "service": "meeting-intelligence-api",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }

# ============================================================
# 2. 文件上传
# ============================================================

@app.post("/api/upload")
async def upload_meeting_file(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None)
):
    """
    上传会议文件

    Args:
        file: 会议文件（支持 mp3, wav, mp4, m4a, webm）
        title: 可选的会议标题

    Returns:
        meeting_id: 会议 ID
        file_name: 文件名
        file_size: 文件大小
    """
    # 验证文件格式
    if not validate_file_format(file.filename):
        return {
            "success": False,
            "message": f"不支持的文件格式，支持格式: {', '.join(ALLOWED_EXTENSIONS)}"
        }

    # 读取文件内容
    file_content = await file.read()
    file_size = len(file_content)

    # 验证文件大小
    if file_size > MAX_FILE_SIZE:
        return {
            "success": False,
            "message": f"文件过大（{format_file_size(file_size)}），最大支持 3GB"
        }

    # 生成会议 ID
    meeting_id = generate_meeting_id()

    # 保存文件到本地
    file_path = UPLOAD_DIR / f"{meeting_id}_{file.filename}"
    with open(file_path, "wb") as f:
        f.write(file_content)

    # 存储会议信息
    meeting_title = title if title else file.filename
    MEETINGS[meeting_id] = {
        "meeting_id": meeting_id,
        "title": meeting_title,
        "file_name": file.filename,
        "file_path": str(file_path),
        "audio_path": str(file_path),  # 添加audio_path字段，供ASR使用
        "file_size": file_size,
        "uploaded_at": datetime.now().isoformat(),
        "status": "uploaded"
    }

    print(f"[BACKEND] file uploaded: meeting_id={meeting_id}, file_path={file_path}")

    return {
        "success": True,
        "meeting_id": meeting_id,
        "file_name": file.filename,
        "file_size": file_size,
        "message": "上传成功"
    }

# ============================================================
# 3. 转录任务
# ============================================================

@app.post("/api/meetings/{meeting_id}/transcribe")
async def start_transcription(meeting_id: str, background_tasks: BackgroundTasks):
    """
    启动会议转录任务

    Args:
        meeting_id: 会议 ID

    Returns:
        task_id: 转录任务 ID
        status: 任务状态
    """
    # 检查会议是否存在
    if meeting_id not in MEETINGS:
        return {
            "success": False,
            "message": "会议不存在"
        }

    # 检查是否已有转录任务
    if MEETINGS[meeting_id].get("transcription_task_id"):
        return {
            "success": False,
            "message": "转录任务已存在"
        }

    # 生成任务 ID
    task_id = generate_task_id("transcribe")

    # 创建转录任务
    TRANSCRIPTION_TASKS[task_id] = {
        "task_id": task_id,
        "meeting_id": meeting_id,
        "status": "processing",
        "progress": 0,
        "current_step": "正在准备转录",
        "created_at": datetime.now().isoformat()
    }

    # 更新会议记录
    MEETINGS[meeting_id]["transcription_task_id"] = task_id
    MEETINGS[meeting_id]["transcription_started_at"] = datetime.now().isoformat()

    # 获取音频文件路径
    audio_path = MEETINGS[meeting_id].get("audio_path", "")
    print(f"[BACKEND] transcription called: meeting_id={meeting_id}")
    print(f"[BACKEND] audio_path: {audio_path}")

    # 检查是否使用真实ASR
    use_real_asr = False
    if audio_path:
        # 临时禁用真实ASR，因为需要 ffmpeg
        # TODO: 安装 ffmpeg 后可以重新启用
        print(f"[BACKEND] WARNING: Real ASR disabled (ffmpeg not installed)")
        print(f"[BACKEND] Using mock transcription for testing")

        # 检查whisper和ffmpeg是否可用
        try:
            import whisper
            import subprocess
            # 检查 ffmpeg 是否可用
            result = subprocess.run(['ffmpeg', '-version'],
                                  capture_output=True,
                                  text=True,
                                  timeout=5)
            if result.returncode == 0:
                use_real_asr = True
                print(f"[BACKEND] whisper and ffmpeg available, will use real ASR")
            else:
                print(f"[BACKEND] ffmpeg not available, using mock transcription")
        except (ImportError, FileNotFoundError, subprocess.TimeoutExpired) as e:
            print(f"[BACKEND] ASR not available: {str(e)}, using mock transcription")

    # 启动后台任务
    if use_real_asr:
        print(f"[BACKEND] using real ASR for transcription")
        target_func = real_transcription_task
        target_args = (meeting_id, task_id, audio_path)
    else:
        print(f"[BACKEND] using mock transcription")
        target_func = simulate_transcription_task
        target_args = (meeting_id, task_id)

    thread = threading.Thread(
        target=target_func,
        args=target_args
    )
    thread.daemon = True
    thread.start()

    return {
        "success": True,
        "task_id": task_id,
        "status": "processing",
        "message": "转录任务已启动"
    }

@app.get("/api/meetings/{meeting_id}/transcription-status")
async def get_transcription_status(meeting_id: str):
    """
    查询转录任务状态

    Args:
        meeting_id: 会议 ID

    Returns:
        status: 任务状态
        progress: 进度百分比
        current_step: 当前步骤描述
    """
    # 检查会议是否存在
    if meeting_id not in MEETINGS:
        return {
            "success": False,
            "message": "会议不存在"
        }

    # 获取转录任务 ID
    task_id = MEETINGS[meeting_id].get("transcription_task_id")
    if not task_id:
        return {
            "success": False,
            "message": "转录任务未启动"
        }

    # 获取任务状态
    task = TRANSCRIPTION_TASKS.get(task_id)
    if not task:
        return {
            "success": False,
            "message": "转录任务不存在"
        }

    return {
        "success": True,
        "status": task["status"],
        "progress": task["progress"],
        "current_step": task["current_step"],
        "message": "转录进行中"
    }

@app.get("/api/meetings/{meeting_id}/transcript")
async def get_transcript(meeting_id: str):
    """
    获取完整转录文字稿

    Args:
        meeting_id: 会议 ID

    Returns:
        transcript: 完整文字稿
        segments: 分段文字稿
    """
    # 检查会议是否存在
    if meeting_id not in MEETINGS:
        return {
            "success": False,
            "message": "会议不存在"
    }

    # 检查转录是否完成
    transcript = MEETINGS[meeting_id].get("transcript")
    if not transcript:
        return {
            "success": False,
            "message": "转录未完成"
        }

    return {
        "success": True,
        "transcript": transcript,
        "segments": MEETINGS[meeting_id].get("segments", []),
        "message": "获取成功"
    }

# ============================================================
# 4. 总结生成任务
# ============================================================

@app.post("/api/meetings/{meeting_id}/summarize")
async def generate_summary(
    meeting_id: str,
    request: SummarizeRequest,
    background_tasks: BackgroundTasks
):
    """
    启动 AI 总结生成任务

    Args:
        meeting_id: 会议 ID
        template_id: 模板 ID
        template: 模板详情（可选）
        transcript: 完整文字稿（可选）
        output_format: 输出格式

    Returns:
        task_id: 总结任务 ID
        status: 任务状态
    """
    print(f"[BACKEND] summarize called: meeting_id={meeting_id}")
    print(f"[BACKEND] template_id: {request.template_id}")

    # 检查会议是否存在
    if meeting_id not in MEETINGS:
        return {
            "success": False,
            "message": "会议不存在"
        }

    # 检查转录是否完成
    transcript = MEETINGS[meeting_id].get("transcript", "")
    if not transcript:
        return {
            "success": False,
            "message": "转录未完成，无法生成总结"
        }

    print(f"[BACKEND] transcript length: {len(transcript)}")

    # 检查是否已有总结任务
    if MEETINGS[meeting_id].get("summary_task_id"):
        return {
            "success": False,
            "message": "总结任务已存在"
        }

    # 生成任务 ID
    task_id = generate_task_id("summary")

    # 创建总结任务
    SUMMARY_TASKS[task_id] = {
        "task_id": task_id,
        "meeting_id": meeting_id,
        "template_id": request.template_id,
        "status": "processing",
        "progress": 0,
        "current_step": "正在准备总结生成",
        "created_at": datetime.now().isoformat()
    }

    # 更新会议记录
    MEETINGS[meeting_id]["summary_task_id"] = task_id
    MEETINGS[meeting_id]["summary_started_at"] = datetime.now().isoformat()
    MEETINGS[meeting_id]["template_id"] = request.template_id

    # 启动后台任务
    # 根据LLM配置选择真实还是模拟
    use_real_llm = llm_client.is_configured()

    print(f"[BACKEND] ========== SUMMARIZE TASK STARTED ==========")
    print(f"[BACKEND] meeting_id: {meeting_id}")
    print(f"[BACKEND] template_id: {request.template_id}")
    print(f"[BACKEND] transcript length: {len(transcript)}")
    print(f"[BACKEND] llm_provider: {llm_client.provider}")
    print(f"[BACKEND] llm_configured: {use_real_llm}")

    if use_real_llm:
        print(f"[BACKEND] using REAL LLM for summary generation")
        target_func = real_summary_task
    else:
        print(f"[BACKEND] LLM not configured, using MOCK summary")
        target_func = simulate_summary_task

    thread = threading.Thread(
        target=target_func,
        args=(meeting_id, task_id, request.template_id)
    )
    thread.daemon = True
    thread.start()

    return {
        "success": True,
        "task_id": task_id,
        "status": "processing",
        "message": "总结生成任务已启动"
    }

@app.get("/api/meetings/{meeting_id}/summary-status")
async def get_summary_status(meeting_id: str):
    """
    查询总结生成状态

    Args:
        meeting_id: 会议 ID

    Returns:
        status: 任务状态
        progress: 进度百分比
        current_step: 当前步骤描述
    """
    # 检查会议是否存在
    if meeting_id not in MEETINGS:
        return {
            "success": False,
            "message": "会议不存在"
        }

    # 获取总结任务 ID
    task_id = MEETINGS[meeting_id].get("summary_task_id")
    if not task_id:
        return {
            "success": False,
            "message": "总结任务未启动"
        }

    # 获取任务状态
    task = SUMMARY_TASKS.get(task_id)
    if not task:
        return {
            "success": False,
            "message": "总结任务不存在"
        }

    return {
        "success": True,
        "status": task["status"],
        "progress": task["progress"],
        "current_step": task["current_step"],
        "message": "总结生成中"
    }

@app.get("/api/meetings/{meeting_id}/summary")
async def get_summary(meeting_id: str):
    """
    获取生成的 AI 总结

    Args:
        meeting_id: 会议 ID

    Returns:
        summary: AI 总结文本
        markdown: Markdown 格式总结
        template_id: 使用的模板 ID
        template_name: 模板名称
    """
    # 检查会议是否存在
    if meeting_id not in MEETINGS:
        return {
            "success": False,
            "message": "会议不存在"
        }

    # 检查总结是否完成
    summary = MEETINGS[meeting_id].get("summary")
    if not summary:
        return {
            "success": False,
            "message": "总结未完成"
        }

    template_id = MEETINGS[meeting_id].get("template_id", "unknown")

    # 模板名称映射
    template_names = {
        "general_meeting": "通用会议纪要",
        "weekly_meeting": "周会总结",
        "project_review": "项目评审",
        "default": "默认模板"
    }

    return {
        "success": True,
        "summary": summary,
        "markdown": summary,
        "template_id": template_id,
        "template_name": template_names.get(template_id, "未知模板"),
        "message": "获取成功"
    }

# ============================================================
# 5. 模板管理模块（完整版）
# ============================================================

# 临时存储自定义模板
CUSTOM_TEMPLATES = []

def get_builtin_templates():
    """获取内置模板"""
    return [
        {
            "id": "general_meeting",
            "name": "通用会议纪要",
            "description": "适合大多数会议场景，包含摘要、决策与待办事项",
            "category": "default",
            "sections": ["会议摘要", "关键讨论", "决策结论", "待办事项"],
            "prompt": "请总结本次会议，重点关注会议摘要、关键讨论内容、决策结论和待办事项。",
            "output_format": "markdown",
            "is_builtin": True
        },
        {
            "id": "custom_1778838491",
            "name": "大学生课程",
            "description": "大学生课程总结",
            "category": "education",
            "sections": ["课程内容分段总结", "课程知识点", "课后任务"],
            "prompt": "请从课程助教和大学生的视角，根据输出结构总结课程内容。重点关注课程的主要知识点、学习要点和课后作业要求。",
            "output_format": "markdown",
            "is_builtin": False  # 标记为自定义模板，允许修改删除
        }
    ]

def get_all_templates():
    """获取所有模板（内置 + 自定义）"""
    return get_builtin_templates() + CUSTOM_TEMPLATES

@app.get("/api/templates")
async def get_templates():
    """
    获取所有模板列表

    Returns:
        templates: 模板列表
        message: 成功信息
    """
    # DEBUG: Print to show this endpoint is being called
    print("[DEBUG] get_templates() called - returning 2 templates")

    # 只返回2个模板：通用会议纪要 + 大学生课程
    templates = [
        {
            "id": "general_meeting",
            "name": "通用会议纪要",
            "description": "适合大多数会议场景，包含摘要、决策与待办事项",
            "category": "default",
            "sections": ["会议摘要", "关键讨论", "决策结论", "待办事项"],
            "prompt": "请总结本次会议，重点关注会议摘要、关键讨论内容、决策结论和待办事项。",
            "output_format": "markdown",
            "is_builtin": True
        },
        {
            "id": "custom_1778838491",
            "name": "大学生课程",
            "description": "大学生课程总结",
            "category": "education",
            "sections": ["课程内容分段总结", "课程知识点", "课后任务"],
            "prompt": "请从课程助教和大学生的视角，根据输出结构总结课程内容。重点关注课程的主要知识点、学习要点和课后作业要求。",
            "output_format": "markdown",
            "is_builtin": False
        }
    ]

    print(f"[DEBUG] Returning {len(templates)} templates")
    return {
        "success": True,
        "templates": templates,
        "message": "获取成功"
    }

@app.get("/api/templates/{template_id}")
async def get_template_detail(template_id: str):
    """
    获取单个模板详情

    Args:
        template_id: 模板 ID

    Returns:
        template: 模板详情
    """
    all_templates = get_all_templates()
    template = next((t for t in all_templates if t["id"] == template_id), None)

    if not template:
        return {
            "success": False,
            "message": "模板不存在"
        }

    return {
        "success": True,
        "template": template,
        "message": "获取成功"
    }

@app.post("/api/templates")
async def create_template(request: dict):
    """
    创建新模板

    Args:
        request: {
            "name": "模板名称",
            "description": "模板描述",
            "sections": ["输出结构1", "输出结构2"],
            "prompt": "模板提示词",
            "output_format": "markdown"
        }

    Returns:
        template_id: 新模板ID
        template: 模板详情
    """
    try:
        # 验证必填字段
        required_fields = ["name", "description", "sections", "prompt"]
        for field in required_fields:
            if field not in request or not request[field]:
                return {
                    "success": False,
                    "message": f"缺少必填字段: {field}"
                }

        # 生成模板ID
        import time
        template_id = f"custom_{int(time.time())}"

        # 创建新模板
        new_template = {
            "id": template_id,
            "name": request["name"],
            "description": request["description"],
            "category": "custom",
            "sections": request["sections"],
            "prompt": request["prompt"],
            "output_format": request.get("output_format", "markdown"),
            "is_builtin": False
        }

        # 添加到自定义模板列表
        CUSTOM_TEMPLATES.append(new_template)

        print(f"[BACKEND] Template created: {template_id} - {request['name']}")

        return {
            "success": True,
            "template_id": template_id,
            "template": new_template,
            "message": "模板创建成功"
        }

    except Exception as e:
        print(f"[BACKEND] ERROR: Template creation failed: {str(e)}")
        return {
            "success": False,
            "message": f"模板创建失败: {str(e)}"
        }

@app.put("/api/templates/{template_id}")
async def update_template(template_id: str, request: dict):
    """
    更新模板

    Args:
        template_id: 模板ID
        request: 更新的数据

    Returns:
        template: 更新后的模板
    """
    try:
        # 查找模板
        all_templates = get_all_templates()
        template = next((t for t in all_templates if t["id"] == template_id), None)

        if not template:
            return {
                "success": False,
                "message": "模板不存在"
            }

        # 检查是否为内置模板
        if template.get("is_builtin", False):
            return {
                "success": False,
                "message": "不允许修改内置模板"
            }

        # 查找并更新自定义模板
        for i, t in enumerate(CUSTOM_TEMPLATES):
            if t["id"] == template_id:
                # 更新字段
                if "description" in request:
                    CUSTOM_TEMPLATES[i]["description"] = request["description"]
                if "sections" in request:
                    CUSTOM_TEMPLATES[i]["sections"] = request["sections"]
                if "prompt" in request:
                    CUSTOM_TEMPLATES[i]["prompt"] = request["prompt"]

                print(f"[BACKEND] Template updated: {template_id}")

                return {
                    "success": True,
                    "template": CUSTOM_TEMPLATES[i],
                    "message": "模板更新成功"
                }

        return {
            "success": False,
            "message": "模板不存在"
        }

    except Exception as e:
        print(f"[BACKEND] ERROR: Template update failed: {str(e)}")
        return {
            "success": False,
            "message": f"模板更新失败: {str(e)}"
        }

@app.delete("/api/templates/{template_id}")
async def delete_template(template_id: str):
    """
    删除模板

    Args:
        template_id: 模板ID

    Returns:
        message: 删除结果
    """
    try:
        # 查找模板
        all_templates = get_all_templates()
        template = next((t for t in all_templates if t["id"] == template_id), None)

        if not template:
            return {
                "success": False,
                "message": "模板不存在"
            }

        # 检查是否为内置模板
        if template.get("is_builtin", False):
            return {
                "success": False,
                "message": "不允许删除内置模板"
            }

        # 从自定义模板中删除
        for i, t in enumerate(CUSTOM_TEMPLATES):
            if t["id"] == template_id:
                deleted_template = CUSTOM_TEMPLATES.pop(i)
                print(f"[BACKEND] Template deleted: {template_id} - {deleted_template['name']}")

                return {
                    "success": True,
                    "message": "模板删除成功"
                }

        return {
            "success": False,
            "message": "模板不存在"
        }

    except Exception as e:
        print(f"[BACKEND] ERROR: Template deletion failed: {str(e)}")
        return {
            "success": False,
            "message": f"模板删除失败: {str(e)}"
        }

# ============================================================
# 模板管理扩展接口（支持创建、更新、删除）
# ============================================================

# 临时存储自定义模板
CUSTOM_TEMPLATES = []

def get_all_templates():
    """获取所有模板（内置 + 自定义）"""
    builtin_templates = [
        {
            "id": "general_meeting",
            "name": "通用会议纪要",
            "description": "适合大多数会议场景，包含摘要、决策与待办事项",
            "category": "default",
            "sections": ["会议摘要", "关键讨论", "决策结论", "待办事项"],
            "prompt": "请总结本次会议，重点关注会议摘要、关键讨论内容、决策结论和待办事项。",
            "output_format": "markdown",
            "is_builtin": True
        },
        {
            "id": "custom_1778838491",
            "name": "大学生课程",
            "description": "大学生课程总结",
            "category": "education",
            "sections": ["课程内容分段总结", "课程知识点", "课后任务"],
            "prompt": "请从课程助教和大学生的视角，根据输出结构总结课程内容。重点关注课程的主要知识点、学习要点和课后作业要求。",
            "output_format": "markdown",
            "is_builtin": False
        }
    ]
    return builtin_templates + CUSTOM_TEMPLATES

@app.post("/api/templates")
async def create_template(request: dict):
    """
    创建新模板

    Args:
        request: {
            "name": "模板名称",
            "description": "模板描述",
            "sections": ["输出结构1", "输出结构2"],
            "prompt": "模板提示词",
            "output_format": "markdown"
        }

    Returns:
        template_id: 新模板ID
        template: 模板详情
    """
    try:
        # 验证必填字段
        required_fields = ["name", "description", "sections", "prompt"]
        for field in required_fields:
            if field not in request or not request[field]:
                return {
                    "success": False,
                    "message": f"缺少必填字段: {field}"
                }

        # 生成模板ID
        import time
        template_id = f"custom_{int(time.time())}"

        # 创建新模板
        new_template = {
            "id": template_id,
            "name": request["name"],
            "description": request["description"],
            "category": "custom",
            "sections": request["sections"],
            "prompt": request["prompt"],
            "output_format": request.get("output_format", "markdown"),
            "is_builtin": False
        }

        # 添加到自定义模板列表
        CUSTOM_TEMPLATES.append(new_template)

        print(f"[BACKEND] Template created: {template_id} - {request['name']}")

        return {
            "success": True,
            "template_id": template_id,
            "template": new_template,
            "message": "模板创建成功"
        }

    except Exception as e:
        print(f"[BACKEND] ERROR: Template creation failed: {str(e)}")
        return {
            "success": False,
            "message": f"模板创建失败: {str(e)}"
        }

@app.put("/api/templates/{template_id}")
async def update_template(template_id: str, request: dict):
    """
    更新模板

    Args:
        template_id: 模板ID
        request: 更新的数据

    Returns:
        template: 更新后的模板
    """
    try:
        # 查找模板
        all_templates = get_all_templates()
        template = next((t for t in all_templates if t["id"] == template_id), None)

        if not template:
            return {
                "success": False,
                "message": "模板不存在"
            }

        # 检查是否为内置模板
        if template.get("is_builtin", False):
            return {
                "success": False,
                "message": "不允许修改内置模板"
            }

        # 查找并更新自定义模板
        for i, t in enumerate(CUSTOM_TEMPLATES):
            if t["id"] == template_id:
                # 更新字段
                if "description" in request:
                    CUSTOM_TEMPLATES[i]["description"] = request["description"]
                if "sections" in request:
                    CUSTOM_TEMPLATES[i]["sections"] = request["sections"]
                if "prompt" in request:
                    CUSTOM_TEMPLATES[i]["prompt"] = request["prompt"]

                print(f"[BACKEND] Template updated: {template_id}")

                return {
                    "success": True,
                    "template": CUSTOM_TEMPLATES[i],
                    "message": "模板更新成功"
                }

        return {
            "success": False,
            "message": "模板不存在"
        }

    except Exception as e:
        print(f"[BACKEND] ERROR: Template update failed: {str(e)}")
        return {
            "success": False,
            "message": f"模板更新失败: {str(e)}"
        }

@app.delete("/api/templates/{template_id}")
async def delete_template(template_id: str):
    """
    删除模板

    Args:
        template_id: 模板ID

    Returns:
        message: 删除结果
    """
    try:
        # 查找模板
        all_templates = get_all_templates()
        template = next((t for t in all_templates if t["id"] == template_id), None)

        if not template:
            return {
                "success": False,
                "message": "模板不存在"
            }

        # 检查是否为内置模板
        if template.get("is_builtin", False):
            return {
                "success": False,
                "message": "不允许删除内置模板"
            }

        # 从自定义模板中删除
        for i, t in enumerate(CUSTOM_TEMPLATES):
            if t["id"] == template_id:
                deleted_template = CUSTOM_TEMPLATES.pop(i)
                print(f"[BACKEND] Template deleted: {template_id} - {deleted_template['name']}")

                return {
                    "success": True,
                    "message": "模板删除成功"
                }

        return {
            "success": False,
            "message": "模板不存在"
        }

    except Exception as e:
        print(f"[BACKEND] ERROR: Template deletion failed: {str(e)}")
        return {
            "success": False,
            "message": f"模板删除失败: {str(e)}"
        }

# Duplicate endpoints removed - using the earlier versions that return only 2 templates

# ============================================================
# 启动入口
# ============================================================

if __name__ == "__main__":
    print("Jinni Meeting Intelligence API")
    print(f"Upload directory: {UPLOAD_DIR}")
    print(f"Server: http://localhost:8000")
    print(f"Docs: http://localhost:8000/docs")
    print()

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
