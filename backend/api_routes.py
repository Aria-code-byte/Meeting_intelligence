"""
Unified API Routes
==================
使用提供商适配层的统一API接口
"""
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime
from pathlib import Path
import uuid
import os
import sys

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 从 backend.providers 导入
from backend.providers import TranscriptionProvider, SummaryProvider, ProviderType


# 配置
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "./uploads"))
UPLOAD_DIR.mkdir(exist_ok=True)
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "500"))
ALLOWED_EXTENSIONS = {'mp3', 'wav', 'mp4', 'm4a', 'webm'}

# 读取转录 provider 配置
TRANSCRIPTION_PROVIDER_TYPE = os.getenv("AI_TRANSCRIPTION_PROVIDER", "fallback").lower()
WHISPER_MODEL_SIZE = os.getenv("WHISPER_MODEL_SIZE", "base")
WHISPER_LANGUAGE = os.getenv("WHISPER_LANGUAGE", "zh")
WHISPER_DEVICE = os.getenv("WHISPER_DEVICE", "auto")

# API Router
api_router = APIRouter(prefix="/api/v1", tags=["ai-services"])


# Request/Response Models
class TranscribeRequest(BaseModel):
    """转录请求（用于文档生成，实际使用文件上传）"""
    audio_path: str
    model_size: Optional[str] = "base"
    language: Optional[str] = "zh"


class TranscribeResponse(BaseModel):
    """转录响应（阶段 10B-4：扩展支持 WhisperX 字段）"""
    success: bool
    transcript: Optional[str] = None
    # 阶段 10B-4：新增 transcriptTurns 字段
    transcriptTurns: Optional[List[Dict[str, Any]]] = None
    segments: Optional[List[Dict[str, Any]]] = None
    provider: str
    isFallback: bool
    error: Optional[str] = None
    processingTimeMs: Optional[int] = None
    # 阶段 10B-4：新增 provider metadata 字段
    transcriptionModel: Optional[str] = None
    diarizationEnabled: Optional[bool] = None
    diarizationProvider: Optional[str] = None
    diarizationModel: Optional[str] = None
    alignmentStatus: Optional[str] = None
    alignmentError: Optional[str] = None
    # 阶段 10B-5-Q4：新增 audioDuration 字段
    audioDuration: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


class SummarizeRequest(BaseModel):
    """总结请求"""
    transcript: str
    template_name: str
    template_description: Optional[str] = ""
    template_sections: List[str]
    template_prompt: str


class SummarizeResponse(BaseModel):
    """总结响应"""
    success: bool
    summary: Optional[str] = None
    provider: str
    isFallback: bool
    templateId: Optional[str] = None
    templateName: Optional[str] = None
    error: Optional[str] = None
    processingTimeMs: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None


class ProviderInfoResponse(BaseModel):
    """提供商信息响应"""
    transcription: Dict[str, Any]
    summary: Dict[str, Any]


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str
    service: str
    version: str
    transcriptionFallback: bool
    summaryFallback: bool
    apiBasePath: str


# Initialize providers (with configuration)
transcription_config = {
    "model_size": WHISPER_MODEL_SIZE,
    "language": WHISPER_LANGUAGE,
    "device": WHISPER_DEVICE,
}
transcription_provider = TranscriptionProvider(transcription_config)
summary_provider = SummaryProvider()


def validate_file_format(filename: str) -> bool:
    """验证文件格式"""
    if not filename:
        return False
    ext = filename.split('.')[-1].lower() if '.' in filename else ''
    return ext in ALLOWED_EXTENSIONS


def cleanup_temp_file(file_path: Path):
    """清理临时文件"""
    try:
        if file_path.exists():
            os.remove(file_path)
    except Exception as e:
        print(f"[WARNING] Failed to cleanup temp file {file_path}: {e}")


@api_router.post("/transcribe", response_model=TranscribeResponse)
async def transcribe_audio(
    file: UploadFile = File(...),
    model_size: str = Form("base"),
    language: str = Form("zh")
) -> TranscribeResponse:
    """
    统一转录接口（文件上传版本）

    使用提供商适配层进行音频转录，自动选择最佳提供商：
    - 优先使用 Whisper ASR（如果可用）
    - 回退到模拟转录

    Args:
        file: 音频文件
        model_size: Whisper模型大小
        language: 语言代码

    Returns:
        TranscribeResponse: 转录结果
    """
    temp_file_path = None
    start_time = datetime.now()

    # 1. 验证文件格式
    if not validate_file_format(file.filename):
        return TranscribeResponse(
            success=False,
            provider="fallback",
            isFallback=True,
            error=f"不支持的文件格式: {file.filename}。支持格式: {', '.join(ALLOWED_EXTENSIONS)}",
            processingTimeMs=0,
            metadata={"processedAt": start_time.isoformat()}
        )

    # 2. 读取文件并检查大小
    try:
        file_content = await file.read()
        file_size_mb = len(file_content) / (1024 * 1024)

        if file_size_mb > MAX_FILE_SIZE_MB:
            return TranscribeResponse(
                success=False,
                provider="fallback",
                isFallback=True,
                error=f"文件过大: {file_size_mb:.2f}MB，最大支持 {MAX_FILE_SIZE_MB}MB",
                processingTimeMs=0,
                metadata={"processedAt": start_time.isoformat()}
            )

        if file_size_mb == 0:
            return TranscribeResponse(
                success=False,
                provider="fallback",
                isFallback=True,
                error="文件为空，请上传有效的音频文件",
                processingTimeMs=0,
                metadata={"processedAt": start_time.isoformat()}
            )

    except Exception as e:
        return TranscribeResponse(
            success=False,
            provider="fallback",
            isFallback=True,
            error=f"文件读取失败: {str(e)}",
            processingTimeMs=0,
            metadata={"processedAt": start_time.isoformat()}
        )

    # 3. 保存临时文件
    try:
        temp_file_name = f"temp_{uuid.uuid4().hex[:12]}_{file.filename}"
        temp_file_path = UPLOAD_DIR / temp_file_name

        with open(temp_file_path, "wb") as f:
            f.write(file_content)

    except Exception as e:
        return TranscribeResponse(
            success=False,
            provider="fallback",
            isFallback=True,
            error=f"文件保存失败: {str(e)}",
            processingTimeMs=0,
            metadata={"processedAt": start_time.isoformat()}
        )

    # 4. 调用转录提供商
    try:
        result = transcription_provider.transcribe(
            audio_path=str(temp_file_path),
            model_size=model_size,
            language=language
        )

        processing_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)

        if result.success:
            # 阶段 10B-4：提取 WhisperX 特定字段
            data = result.data
            return TranscribeResponse(
                success=True,
                transcript=data.get("transcript"),
                # 阶段 10B-4：返回 transcriptTurns
                transcriptTurns=data.get("transcriptTurns"),
                segments=data.get("segments"),
                provider=data.get("transcriptionProvider", result.provider.value),
                isFallback=result.is_fallback,
                processingTimeMs=result.processing_time_ms or processing_time_ms,
                # 阶段 10B-4：返回 provider metadata
                transcriptionModel=data.get("transcriptionModel"),
                diarizationEnabled=data.get("diarizationEnabled"),
                diarizationProvider=data.get("diarizationProvider"),
                diarizationModel=data.get("diarizationModel"),
                alignmentStatus=data.get("alignmentStatus"),
                alignmentError=data.get("alignmentError"),
                # 阶段 10B-5-Q4：返回 audioDuration
                audioDuration=data.get("audioDuration"),
                metadata={
                    "processedAt": datetime.now().isoformat(),
                    "duration": data.get("duration"),
                    "wordCount": data.get("word_count"),
                    "language": data.get("language", language),
                    "model": data.get("transcriptionModel") or (model_size if result.provider.value == "backend" else "fallback")
                }
            )
        else:
            return TranscribeResponse(
                success=False,
                provider=result.provider.value,
                isFallback=result.is_fallback,
                error=result.error or "转录失败",
                processingTimeMs=result.processing_time_ms or processing_time_ms,
                metadata={"processedAt": datetime.now().isoformat()}
            )

    except Exception as e:
        processing_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
        return TranscribeResponse(
            success=False,
            provider="fallback",
            isFallback=True,
            error=f"转录处理异常: {str(e)}",
            processingTimeMs=processing_time_ms,
            metadata={"processedAt": datetime.now().isoformat()}
        )

    finally:
        # 5. 清理临时文件
        if temp_file_path:
            cleanup_temp_file(temp_file_path)


@api_router.post("/summarize", response_model=SummarizeResponse)
async def generate_summary(request: SummarizeRequest) -> SummarizeResponse:
    """
    统一总结生成接口

    使用提供商适配层生成会议总结，自动选择最佳提供商：
    - 优先使用配置的 LLM（OpenAI/Ollama等）
    - 回退到基于模板的简单总结

    Args:
        request: 总结请求

    Returns:
        SummarizeResponse: 总结结果
    """
    start_time = datetime.now()

    # 1. 验证 transcript 非空
    transcript = request.transcript.strip()
    if not transcript:
        return SummarizeResponse(
            success=False,
            provider="fallback",
            isFallback=True,
            error="当前会议暂无文字稿，无法生成总结。请先上传音频进行转录或手动输入文字稿。",
            processingTimeMs=0,
            metadata={"processedAt": start_time.isoformat()}
        )

    if len(transcript) < 10:
        return SummarizeResponse(
            success=False,
            provider="fallback",
            isFallback=True,
            error="文字稿内容过少，无法生成有效的总结。请补充更多内容。",
            processingTimeMs=0,
            metadata={"processedAt": start_time.isoformat()}
        )

    # 2. 调用总结提供商
    try:
        result = summary_provider.generate_summary(
            transcript=transcript,
            template_name=request.template_name,
            template_description=request.template_description or "",
            template_sections=request.template_sections,
            template_prompt=request.template_prompt
        )

        processing_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)

        if result.success:
            # 使用真实的模型名
            actual_model = result.data.get("model", "fallback")
            return SummarizeResponse(
                success=True,
                summary=result.data.get("summary"),
                provider=result.provider.value,
                isFallback=result.is_fallback,
                templateId=None,  # 由前端提供
                templateName=request.template_name,
                processingTimeMs=result.processing_time_ms or processing_time_ms,
                metadata={
                    "processedAt": datetime.now().isoformat(),
                    "model": actual_model,
                    "transcriptLength": len(transcript),
                    "templateSections": len(request.template_sections)
                }
            )
        else:
            return SummarizeResponse(
                success=False,
                provider=result.provider.value,
                isFallback=result.is_fallback,
                error=result.error or "总结生成失败",
                processingTimeMs=result.processing_time_ms or processing_time_ms,
                metadata={"processedAt": datetime.now().isoformat()}
            )

    except Exception as e:
        processing_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
        return SummarizeResponse(
            success=False,
            provider="fallback",
            isFallback=True,
            error=f"总结处理异常: {str(e)}",
            processingTimeMs=processing_time_ms,
            metadata={"processedAt": datetime.now().isoformat()}
        )


@api_router.get("/providers/info", response_model=ProviderInfoResponse)
async def get_provider_info() -> ProviderInfoResponse:
    """
    获取AI服务提供商信息

    Returns:
        ProviderInfoResponse: 提供商信息（不包含敏感信息）
    """
    transcription_info = transcription_provider.get_provider_info()
    summary_info = summary_provider.get_provider_info()

    # 添加额外的状态信息
    transcription_status = {
        **transcription_info,
        "available": not transcription_provider.is_using_fallback(),
        "configured": not transcription_provider.is_using_fallback(),
        "provider_type": os.getenv("AI_TRANSCRIPTION_PROVIDER", "fallback"),
        "whisper_model": WHISPER_MODEL_SIZE if not transcription_provider.is_using_fallback() else None,
    }

    summary_status = {
        **summary_info,
        "available": not summary_provider.is_using_fallback(),
        "configured": not summary_provider.is_using_fallback(),
        "provider_type": os.getenv("AI_SUMMARY_PROVIDER", "fallback"),
        "note": "Summary provider 当前保持 fallback 模式" if summary_provider.is_using_fallback() else None,
    }

    # 添加真实模型信息（如果使用 LLM）
    if not summary_provider.is_using_fallback():
        if hasattr(summary_provider.provider, 'llm_client') and summary_provider.provider.llm_client:
            llm = summary_provider.provider.llm_client
            if llm.provider == "deepseek":
                summary_status["model"] = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
            else:
                summary_status["model"] = "unknown"
        else:
            summary_status["model"] = "unknown"
    else:
        summary_status["model"] = "fallback"

    return ProviderInfoResponse(
        transcription=transcription_status,
        summary=summary_status
    )


@api_router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """健康检查"""
    return HealthResponse(
        status="ok",
        service="jinni-ai-services",
        version="1.0.0",
        transcriptionFallback=transcription_provider.is_using_fallback(),
        summaryFallback=summary_provider.is_using_fallback(),
        apiBasePath="/api/v1"
    )


# ============================================================
# 阶段 10B-5-Q4：异步转录任务 API
# ============================================================

# 导入异步任务管理器
try:
    from services.async_transcription_manager import get_transcription_manager, TranscriptionStatus
    ASYNC_TRANSCRIPTION_AVAILABLE = True
except ImportError:
    print("[WARNING] async_transcription_manager not available, async transcription disabled")
    ASYNC_TRANSCRIPTION_AVAILABLE = False


class CreateJobResponse(BaseModel):
    """创建任务响应"""
    success: bool
    jobId: Optional[str] = None
    status: Optional[str] = None
    error: Optional[str] = None


class JobStatusResponse(BaseModel):
    """任务状态响应"""
    success: bool
    jobId: Optional[str] = None
    status: Optional[str] = None
    stage: Optional[str] = None
    progress: Optional[int] = None
    message: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    timings: Optional[Dict[str, Any]] = None
    createdAt: Optional[str] = None
    startedAt: Optional[str] = None
    completedAt: Optional[str] = None


class CancelJobResponse(BaseModel):
    """取消任务响应"""
    success: bool
    message: Optional[str] = None


if ASYNC_TRANSCRIPTION_AVAILABLE:
    @api_router.get("/transcriptions/jobs")
    async def list_transcription_jobs():
        """
        列出所有转录任务

        Returns:
            包含所有任务的列表
        """
        try:
            manager = get_transcription_manager()

            # 获取所有任务
            jobs = []
            for job_id, job in manager.jobs.items():
                jobs.append({
                    "jobId": job.job_id,
                    "status": job.status.value,
                    "stage": job.stage,
                    "progress": job.progress,
                    "message": job.message,
                    "createdAt": job.created_at.isoformat() if job.created_at else None,
                    "startedAt": job.started_at.isoformat() if job.started_at else None,
                    "completedAt": job.completed_at.isoformat() if job.completed_at else None,
                    "error": job.error
                })

            # 按创建时间排序（最新的在前）
            jobs.sort(key=lambda x: x.get("createdAt", ""), reverse=True)

            return {
                "success": True,
                "jobs": jobs,
                "total": len(jobs)
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "jobs": [],
                "total": 0
            }

    @api_router.post("/transcriptions/jobs", response_model=CreateJobResponse)
    async def create_transcription_job(
        file: UploadFile = File(...),
        model_size: str = Form("base"),
        language: str = Form("zh")
    ) -> CreateJobResponse:
        """
        创建异步转录任务

        上传文件后立即返回 jobId，不等待转录完成。
        使用 GET /api/v1/transcriptions/jobs/{jobId} 查询任务状态。

        Args:
            file: 音频文件
            model_size: Whisper 模型大小
            language: 语言代码

        Returns:
            CreateJobResponse: 包含 jobId 的响应
        """
        temp_file_path = None

        # 1. 验证文件格式
        if not validate_file_format(file.filename):
            return CreateJobResponse(
                success=False,
                error=f"不支持的文件格式: {file.filename}。支持格式: {', '.join(ALLOWED_EXTENSIONS)}"
            )

        # 2. 读取文件并检查大小
        try:
            file_content = await file.read()
            file_size_mb = len(file_content) / (1024 * 1024)

            if file_size_mb > MAX_FILE_SIZE_MB:
                return CreateJobResponse(
                    success=False,
                    error=f"文件过大: {file_size_mb:.2f}MB，最大支持 {MAX_FILE_SIZE_MB}MB"
                )

            if file_size_mb == 0:
                return CreateJobResponse(
                    success=False,
                    error="文件为空，请上传有效的音频文件"
                )

        except Exception as e:
            return CreateJobResponse(
                success=False,
                error=f"文件读取失败: {str(e)}"
            )

        # 3. 保存临时文件
        try:
            temp_file_name = f"temp_{uuid.uuid4().hex[:12]}_{file.filename}"
            temp_file_path = UPLOAD_DIR / temp_file_name

            with open(temp_file_path, "wb") as f:
                f.write(file_content)

        except Exception as e:
            return CreateJobResponse(
                success=False,
                error=f"文件保存失败: {str(e)}"
            )

        # 4. 创建异步任务
        try:
            manager = get_transcription_manager()
            job = manager.create_job(
                audio_path=str(temp_file_path),
                model_size=model_size,
                language=language
            )

            return CreateJobResponse(
                success=True,
                jobId=job.job_id,
                status=job.status.value
            )

        except Exception as e:
            # 清理临时文件
            if temp_file_path and temp_file_path.exists():
                cleanup_temp_file(temp_file_path)

            return CreateJobResponse(
                success=False,
                error=f"创建任务失败: {str(e)}"
            )


    @api_router.get("/transcriptions/jobs/{job_id}", response_model=JobStatusResponse)
    async def get_transcription_job(job_id: str) -> JobStatusResponse:
        """
        查询异步转录任务状态

        Args:
            job_id: 任务 ID

        Returns:
            JobStatusResponse: 任务状态
        """
        try:
            manager = get_transcription_manager()
            job = manager.get_job(job_id)

            if not job:
                return JobStatusResponse(
                    success=False,
                    error=f"任务不存在: {job_id}"
                )

            job_dict = job.to_dict()

            return JobStatusResponse(
                success=True,
                jobId=job_dict["jobId"],
                status=job_dict["status"],
                stage=job_dict["stage"],
                progress=job_dict["progress"],
                message=job_dict["message"],
                result=job_dict["result"],
                error=job_dict["error"],
                timings=job_dict["timings"],
                createdAt=job_dict["createdAt"],
                startedAt=job_dict["startedAt"],
                completedAt=job_dict["completedAt"]
            )

        except Exception as e:
            return JobStatusResponse(
                success=False,
                error=f"查询任务状态失败: {str(e)}"
            )


    @api_router.post("/transcriptions/jobs/{job_id}/cancel", response_model=CancelJobResponse)
    async def cancel_transcription_job(job_id: str) -> CancelJobResponse:
        """
        取消异步转录任务

        Args:
            job_id: 任务 ID

        Returns:
            CancelJobResponse: 取消结果
        """
        try:
            manager = get_transcription_manager()
            cancelled = manager.cancel_job(job_id)

            if cancelled:
                return CancelJobResponse(
                    success=True,
                    message="任务已取消"
                )
            else:
                return CancelJobResponse(
                    success=False,
                    message="任务无法取消（可能已完成或不存在）"
                )

        except Exception as e:
            return CancelJobResponse(
                success=False,
                message=f"取消任务失败: {str(e)}"
            )
