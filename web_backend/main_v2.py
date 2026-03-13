#!/usr/bin/env python3
"""
Jinni 会议精灵 - FastAPI 后端服务器（CLI 逻辑强制对齐版）
=================================================================

架构原则：
1. **逻辑注入而非重写** - 直接调用 CLI 核心函数
2. **参数完全对应** - Web API 参数与 CLI argparse 参数一一对应
3. **流式状态同步** - SSE 实时推送 CLI 处理进度

单一真理来源: meeting_intelligence/__main__.py

启动方式：
    uvicorn main:app --reload --host 0.0.0.0 --port 8000
"""

import asyncio
import json
import os
import shutil
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional, AsyncIterator

# 加载 .env 文件
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

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
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from models import Base, Meeting, Result, Template, Summary

# ============================================================
# 导入 CLI 包装层（核心逻辑）
# ============================================================
from cli_wrapper import (
    ProcessRequest,
    ProcessResult,
    CLIMeetingProcessor,
    CLIStepProcessor,
    ProgressEvent,
)
from sse import sse_event_stream, StreamingProcessor, task_manager

# ============================================================
# 配置与初始化
# ============================================================

# 项目路径配置
BASE_DIR = Path(__file__).parent
STORAGE_DIR = BASE_DIR / "storage"
VIDEO_DIR = STORAGE_DIR / "videos"
DB_DIR = STORAGE_DIR / "db"

# 创建必要目录
for dir_path in [STORAGE_DIR, VIDEO_DIR, DB_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# SQLite 数据库配置
DATABASE_URL = f"sqlite:///{DB_DIR}/jinni.db"
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建表
Base.metadata.create_all(bind=engine)

# FastAPI 应用初始化
app = FastAPI(
    title="Jinni 会议精灵 API (CLI 逻辑对齐版)",
    description="基于 CLI 核心逻辑的 Web API - 100% 保留原有业务逻辑",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS 中间件配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 支持的文件格式和大小限制
ALLOWED_EXTENSIONS = {".mp4", ".mp3", ".wav", ".m4a", ".m4v", ".avi", ".mov", ".mkv"}
MAX_FILE_SIZE = int(1024 * 1024 * 1024 * 2.5)  # 2.5GB


# ============================================================
# 数据库依赖注入
# ============================================================

def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============================================================
# Pydantic 模型（与 CLI 参数一一对应）
# ============================================================

class ProcessRequestModel(BaseModel):
    """
    处理请求模型（对应 CLI argparse 参数）

    CLI 参数对应:
        input          -> file (上传文件)
        --template -t  -> template (默认: general)
        --provider -p  -> provider (默认: mock)
        --model -m     -> model (可选)
        --no-save      -> no_save (默认: False)
    """
    template: str = Field(
        default="general",
        description="模板名称（对应 CLI --template）",
    )
    provider: str = Field(
        default="mock",
        description="LLM 提供商（对应 CLI --provider）",
    )
    model: Optional[str] = Field(
        default=None,
        description="LLM 模型名称（对应 CLI --model）",
    )
    no_save: bool = Field(
        default=False,
        description="不保存结果到文件（对应 CLI --no-save）",
    )


class TaskResponse(BaseModel):
    """任务响应"""
    task_id: str
    status: str
    message: str


class ProgressEventModel(BaseModel):
    """进度事件模型（对应 SSE 推送）"""
    stage: str
    step: int
    progress: int
    message: str
    data: Optional[dict] = None
    timestamp: str


# ============================================================
# 辅助函数
# ============================================================

async def save_upload_file(upload_file: UploadFile) -> Path:
    """
    保存上传文件

    Args:
        upload_file: 上传的文件

    Returns:
        Path: 保存的文件路径
    """
    file_ext = Path(upload_file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件格式: {file_ext}"
        )

    unique_filename = f"{uuid.uuid4().hex}{file_ext}"
    file_path = VIDEO_DIR / unique_filename

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)

    return file_path


# ============================================================
# API 路由端点（与 CLI 流程一一对应）
# ============================================================

@app.get("/", tags=["根路径"])
async def root():
    """根路径：返回 API 信息"""
    return {
        "name": "Jinni 会议精灵 API (CLI 逻辑对齐版)",
        "version": "2.0.0",
        "status": "running",
        "docs": "/docs",
        "architecture": "单一真理来源: meeting_intelligence/__main__.py",
    }


@app.post("/api/process", response_model=TaskResponse, tags=["会议处理"])
async def process_meeting(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="音视频文件"),
    title: str = Form(..., description="会议标题"),
    template: str = Form("general", description="模板名称（CLI --template）"),
    provider: str = Form("mock", description="LLM 提供商（CLI --provider）"),
    model: Optional[str] = Form(None, description="LLM 模型（CLI --model）"),
    no_save: bool = Form(False, description="不保存文件（CLI --no-save）"),
    db: Session = Depends(get_db),
):
    """
    处理会议文件（完整流程，对应 CLI main() 函数）

    流程：
        1. 上传文件
        2. 创建后台任务
        3. 返回 task_id 用于 SSE 订阅进度

    CLI 对应：
        python -m meeting_intelligence input.mp4 --template general --provider mock
    """
    # 保存文件
    file_path = await save_upload_file(file)

    # 创建处理请求（对应 CLI 参数）
    request = ProcessRequest(
        input_path=str(file_path),
        template=template,
        provider=provider,
        model=model,
        no_save=no_save,
    )

    # 创建任务
    task_id = task_manager.create_task(request)

    # 创建数据库记录
    meeting = Meeting(
        title=title,
        video_path=str(file_path.relative_to(BASE_DIR)),
        video_size=file_path.stat().st_size,
        status="pending",
        progress=0,
    )
    db.add(meeting)
    db.commit()
    db.refresh(meeting)

    # 启动后台任务（异步执行）
    progress_queue = asyncio.Queue()
    background_tasks.add_task(
        task_manager.start_task,
        task_id,
        request,
        progress_queue,
    )

    return TaskResponse(
        task_id=task_id,
        status="pending",
        message=f"任务已创建，使用 /api/process/{task_id}/stream 订阅进度"
    )


@app.get("/api/process/{task_id}/stream", tags=["会议处理"])
async def process_stream(task_id: str):
    """
    SSE 流式进度推送（对应 CLI 控制台输出）

    实时推送处理进度，格式：
        data: {"stage": "asr", "step": 1, "progress": 50, "message": "处理中..."}

    CLI 对应输出：
        [1/3] 原始转录中...
        ✓ 识别了 120 个片段
        [2/3] 增强文稿（书面化）中...
    """
    status = task_manager.get_task_status(task_id)
    if status == "unknown":
        raise HTTPException(status_code=404, detail="任务不存在")

    return StreamingResponse(
        sse_event_stream(task_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@app.get("/api/process/{task_id}/result", tags=["会议处理"])
async def get_process_result(task_id: str):
    """
    获取处理结果

    Args:
        task_id: 任务 ID

    Returns:
        处理结果（完整数据）
    """
    result = task_manager.get_task_result(task_id)
    status = task_manager.get_task_status(task_id)

    if status == "unknown":
        raise HTTPException(status_code=404, detail="任务不存在")

    if status == "pending" or status == "running":
        return {
            "task_id": task_id,
            "status": status,
            "message": "任务尚未完成"
        }

    if status == "failed":
        return {
            "task_id": task_id,
            "status": "failed",
            "error": result.get("error", "未知错误")
        }

    # 转换结果为 JSON 可序列化格式
    return {
        "task_id": task_id,
        "status": "completed",
        "result": {
            "timestamp": result.timestamp,
            "processing_time": result.processing_time,
            "utterance_count": result.utterance_count,
            "enhanced_text": result.enhanced_text,
            "refined_text": result.refined_text,
            "transcript_doc": {
                "utterances": result.transcript_doc.get("utterances", [])[:10],  # 限制返回数量
                "duration": result.transcript_doc.get("duration"),
                "asr_provider": result.transcript_doc.get("asr_provider"),
            }
        }
    }


# ============================================================
# 分步处理 API（对应 CLI 各步骤函数）
# ============================================================

class Step1Request(BaseModel):
    """步骤 1 请求（对应 CLI transcribe 函数）"""
    # 参数从文件上传获取

class Step1Response(BaseModel):
    """步骤 1 响应"""
    utterances: List[dict]
    duration: float
    asr_provider: str
    utterance_count: int


class Step2Request(BaseModel):
    """步骤 2 请求（对应 CLI enhance_transcript 函数）"""
    transcript_doc: dict
    template: str = "general"
    provider: str = "mock"
    model: Optional[str] = None


class Step2Response(BaseModel):
    """步骤 2 响应"""
    enhanced_text: str


class Step3Request(BaseModel):
    """步骤 3 请求（对应 CLI refine_transcript_with_timestamps 函数）"""
    transcript_doc: dict
    provider: str = "mock"
    model: Optional[str] = None
    block_duration_minutes: int = 3


class Step3Response(BaseModel):
    """步骤 3 响应"""
    refined_text: str


@app.post("/api/steps/1/transcribe", response_model=Step1Response, tags=["分步处理"])
async def step_1_transcribe(
    file: UploadFile = File(...),
    language: str = Form("auto"),
    model_size: str = Form("base"),
):
    """
    步骤 1: ASR 转写（对应 CLI __main__.py:478-501）

    CLI 对应：
        from asr.transcribe import transcribe
        asr_result = transcribe(str(input_path))
    """
    file_path = await save_upload_file(file)

    result = await CLIStepProcessor.step_1_transcribe(str(file_path))

    return Step1Response(
        utterances=result.get("utterances", []),
        duration=result.get("duration", 0),
        asr_provider=result.get("asr_provider", ""),
        utterance_count=len(result.get("utterances", [])),
    )


@app.post("/api/steps/2/enhance", response_model=Step2Response, tags=["分步处理"])
async def step_2_enhance(request: Step2Request):
    """
    步骤 2: 增强文稿（对应 CLI __main__.py:504-528）

    CLI 对应：
        enhanced_text = enhance_transcript(transcript_doc, llm, args.template)
    """
    enhanced_text = await CLIStepProcessor.step_2_enhance(
        transcript_doc=request.transcript_doc,
        provider=request.provider,
        model=request.model,
        template=request.template,
    )

    return Step2Response(enhanced_text=enhanced_text)


@app.post("/api/steps/3/refine", response_model=Step3Response, tags=["分步处理"])
async def step_3_refine(request: Step3Request):
    """
    步骤 3: 带时间戳实录（对应 CLI __main__.py:531-560）

    CLI 对应：
        refined_text = refine_transcript_with_timestamps(
            transcript_doc, llm, block_duration_minutes=3
        )
    """
    refined_text = await CLIStepProcessor.step_3_refine(
        transcript_doc=request.transcript_doc,
        provider=request.provider,
        model=request.model,
        block_duration_minutes=request.block_duration_minutes,
    )

    return Step3Response(refined_text=refined_text)


# ============================================================
# 模板管理 API（保持原有功能）
# ============================================================

class TemplateCreate(BaseModel):
    name: str
    description: str


@app.get("/api/templates", tags=["模板管理"])
async def get_templates(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """获取所有模板"""
    templates = db.query(Template).order_by(Template.created_at.desc()).offset(skip).limit(limit).all()
    return [t.to_dict() for t in templates]


@app.post("/api/templates", tags=["模板管理"])
async def create_template(
    template_data: TemplateCreate,
    db: Session = Depends(get_db),
):
    """创建新模板"""
    template = Template(
        name=template_data.name,
        description=template_data.description,
        is_system=0,
    )
    db.add(template)
    db.commit()
    db.refresh(template)
    return template.to_dict()


# ============================================================
# 健康检查
# ============================================================

@app.get("/health", tags=["系统"])
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "cli_wrapper": "loaded",
        "architecture": "logic_injection_no_rewrite",
    }


# ============================================================
# 启动入口
# ============================================================

if __name__ == "__main__":
    import uvicorn

    print(f"""
    ╔════════════════════════════════════════════════════════════╗
    ║     🧞 Jinni 会议精灵 - Web 后端 (CLI 逻辑对齐版)          ║
    ╠════════════════════════════════════════════════════════════╣
    ║  架构原则:                                                  ║
    ║  - 逻辑注入而非重写（直接调用 CLI 函数）                     ║
    ║  - 参数完全对应（Web API = CLI argparse）                   ║
    ║  - SSE 流式状态同步                                         ║
    ╠════════════════════════════════════════════════════════════╣
    ║  API 文档: http://localhost:8000/docs                        ║
    ║  单一真理来源: meeting_intelligence/__main__.py              ║
    ╚════════════════════════════════════════════════════════════╝
    """)

    uvicorn.run(
        "main_v2:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
