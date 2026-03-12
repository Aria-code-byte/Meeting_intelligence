"""
Jinni 会议精灵 - FastAPI 后端服务器
===============================
架构设计：
1. FastAPI 提供高性能异步 REST API
2. BackgroundTasks 处理长时任务（无需 Redis）
3. SQLAlchemy ORM 管理数据库
4. subprocess 调用 C++ 核心引擎

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

from fastapi import (
    FastAPI,
    UploadFile,
    File,
    Form,
    HTTPException,
    BackgroundTasks,
    Depends,
)
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict
from sqlalchemy import create_engine, or_
from sqlalchemy.orm import Session, sessionmaker

from models import Base, Meeting, Result, Template, Summary

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
    description="基于 C++ 核心引擎与 DeepSeek LLM 的智能会议处理平台",
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
MAX_FILE_SIZE = 1024 * 1024 * 1024  # 1GB


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
# C++ 核心引擎调用（底层高性能处理）
# ============================================================

async def call_cpp_engine(video_path: str, output_dir: str) -> dict:
    """
    🔥 底层 C++ 高性能引擎调用 🔥
    ===============================
    调用 C++ 编写的 jinni_engine 执行：
    1. FFmpeg 音频提取（C++ 直接调用 libav）
    2. Whisper 浮点量化推理（C++ 实现，比 Python 快 3-5 倍）
    3. DeepSeek LLM API 调用（C++ libcurl，连接池复用）
    4. 多模板并行总结（C++ 线程池）

    Args:
        video_path: 输入视频文件路径
        output_dir: 输出目录（JSON 结果文件）

    Returns:
        dict: C++ 引擎输出的处理结果
        {
            "transcript_raw": "原始转录文本",
            "transcript_enhanced": "增强转录文本",
            "summaries": [
                {"role": "产品经理", "content": "..."},
                {"role": "开发者", "content": "..."}
            ],
            "metadata": {
                "duration": 1800.5,
                "word_count": 5000,
                "processing_time": 45.2,
                "llm_provider": "deepseek",
                "llm_model": "deepseek-chat"
            }
        }

    Raises:
        RuntimeError: C++ 引擎执行失败
    """
    output_file = Path(output_dir) / f"result_{uuid.uuid4().hex[:8]}.json"

    # 构建命令：C++ 引擎接收视频路径和输出文件路径
    cmd = [
        str(CPP_ENGINE_PATH),
        "--input", video_path,
        "--output", str(output_file),
        "--llm", "deepseek",  # 使用 DeepSeek API（高性价比）
        "--templates", "auto",  # 自动应用所有模板
    ]

    try:
        # ⚡ 异步执行 C++ 程序（不阻塞事件循环）
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        # 等待 C++ 引擎完成（实时输出进度信息）
        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            error_msg = stderr.decode("utf-8", errors="ignore")
            raise RuntimeError(f"C++ 引擎执行失败: {error_msg}")

        # 读取 C++ 引擎输出的 JSON 结果文件
        if not output_file.exists():
            raise RuntimeError("C++ 引擎未生成输出文件")

        with open(output_file, "r", encoding="utf-8") as f:
            result = json.load(f)

        # 清理临时文件（可选，竞赛环境可保留用于调试）
        # output_file.unlink()

        return result

    except FileNotFoundError:
        raise RuntimeError(
            f"❌ C++ 核心引擎未找到: {CPP_ENGINE_PATH}\n"
            f"请确保已编译 jinni_engine 并放置在 {CPP_ENGINE_PATH} 目录下"
        )
    except json.JSONDecodeError as e:
        raise RuntimeError(f"C++ 引擎输出 JSON 格式错误: {e}")
    except Exception as e:
        raise RuntimeError(f"C++ 引擎调用异常: {str(e)}")


# ============================================================
# 异步任务处理
# ============================================================

async def process_meeting_task(
    meeting_id: int,
    video_path: str,
    db: Session
):
    """
    异步会议处理任务
    ================
    流程：
    1. 更新状态为 processing
    2. 调用 C++ 核心引擎处理视频
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
        # 更新状态：处理中
        meeting.status = "processing"
        meeting.progress = 10
        db.commit()

        # 🚀 调用 C++ 核心引擎（底层高性能处理）
        meeting.progress = 30
        db.commit()

        cpp_result = await call_cpp_engine(
            video_path=video_path,
            output_dir=str(TRANSCRIPT_DIR)
        )

        meeting.progress = 80
        db.commit()

        # 解析 C++ 引擎输出并存储结果
        result = Result(
            meeting_id=meeting_id,
            transcript_raw=cpp_result.get("transcript_raw", ""),
            transcript_enhanced=cpp_result.get("transcript_enhanced"),
            summary_json={"templates": cpp_result.get("summaries", [])},
            llm_provider=cpp_result.get("metadata", {}).get("llm_provider"),
            llm_model=cpp_result.get("metadata", {}).get("llm_model"),
            processing_time=cpp_result.get("metadata", {}).get("processing_time"),
            word_count=cpp_result.get("metadata", {}).get("word_count"),
        )
        db.add(result)

        # 更新会议元数据
        meeting.duration = cpp_result.get("metadata", {}).get("duration")
        meeting.status = "completed"
        meeting.progress = 100
        db.commit()

    except Exception as e:
        # 处理失败
        meeting.status = "failed"
        meeting.error_message = str(e)
        meeting.progress = 0
        db.commit()
        print(f"❌ 会议处理失败 (ID: {meeting_id}): {e}")


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
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "cpp_engine_exists": CPP_ENGINE_PATH.exists(),
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

    # 生成唯一文件名（防止冲突）
    unique_filename = f"{uuid.uuid4().hex}{file_ext}"
    video_path = VIDEO_DIR / unique_filename

    # 保存文件
    try:
        with open(video_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        file_size = video_path.stat().st_size
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
    template_id: int,
    db: Session = Depends(get_db),
):
    """
    基于模板生成会议总结
    ====================
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

    # TODO: 调用 LLM 生成总结
    # 这里暂时返回模拟数据
    summary_content = f"""# {meeting.title} - {template.name}

## 概述
（基于模板「{template.name}」生成的总结）

## 详细内容
{transcript_text[:500]}...
"""

    return {
        "meeting_id": meeting_id,
        "template_id": template_id,
        "summary": summary_content,
    }


# ============================================================
# 启动入口
# ============================================================

if __name__ == "__main__":
    import uvicorn

    print("""
    ╔════════════════════════════════════════════════════════════╗
    ║           🧞 Jinni 会议精灵 - Web 后端服务                   ║
    ╠════════════════════════════════════════════════════════════╣
    ║  API 文档: http://localhost:8000/docs                        ║
    ║  ReDoc:   http://localhost:8000/redoc                        ║
    ║                                                               ║
    ║  🚀 底层 C++ 引擎: 提供高性能音视频处理                       ║
    ║  🤖 DeepSeek LLM: 高性价比智能总结                           ║
    ╚════════════════════════════════════════════════════════════╝
    """)

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # 开发模式自动重载
    )
