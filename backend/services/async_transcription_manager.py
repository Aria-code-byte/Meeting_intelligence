"""
异步转录任务管理器
===================
阶段 10B-5-Q4：实现轻量级异步转录任务系统

功能：
- 创建转录任务
- 查询任务状态
- 取消任务
- 自动清理过期任务
"""

import os
import uuid
import time
import threading
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from pathlib import Path
from enum import Enum

# 导入转录服务
from services.whisperx_service import transcribe_with_whisperx


class TranscriptionStatus(str, Enum):
    """转录任务状态"""
    QUEUED = "queued"
    PREPROCESSING = "preprocessing"
    TRANSCRIBING = "transcribing"
    ALIGNING = "aligning"
    DIARIZING = "diarizing"
    BUILDING_TURNS = "building_turns"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TranscriptionJob:
    """转录任务"""

    def __init__(
        self,
        job_id: str,
        audio_path: str,
        model_size: str = "base",
        language: str = "zh",
        device: str = "auto",
        **kwargs
    ):
        self.job_id = job_id
        self.audio_path = audio_path
        self.model_size = model_size
        self.language = language
        self.device = device
        self.kwargs = kwargs

        # 状态
        self.status = TranscriptionStatus.QUEUED
        self.progress = 0
        self.stage = "任务已创建"
        self.message = ""
        self.result = None
        self.error = None

        # 时间统计
        self.created_at = datetime.now()
        self.started_at = None
        self.completed_at = None
        self.timings = {
            "audioPreprocessTime": 0,
            "whisperTranscribeTime": 0,
            "alignTime": 0,
            "diarizationTime": 0,
            "buildTurnsTime": 0,
            "totalTime": 0
        }

        # 取消标志
        self._cancelled = False

    def cancel(self):
        """取消任务"""
        self._cancelled = True
        self.status = TranscriptionStatus.CANCELLED
        self.message = "用户已取消处理"

    def is_cancelled(self) -> bool:
        """检查任务是否已取消"""
        return self._cancelled

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典（用于 API 响应）"""
        return {
            "jobId": self.job_id,
            "status": self.status.value,
            "stage": self.stage,
            "progress": self.progress,
            "message": self.message,
            "result": self.result,
            "error": self.error,
            "timings": self.timings,
            "createdAt": self.created_at.isoformat(),
            "startedAt": self.started_at.isoformat() if self.started_at else None,
            "completedAt": self.completed_at.isoformat() if self.completed_at else None
        }


class AsyncTranscriptionManager:
    """异步转录任务管理器"""

    def __init__(self, max_jobs: int = 100, job_ttl_seconds: int = 3600):
        """
        初始化任务管理器

        Args:
            max_jobs: 最大任务数
            job_ttl_seconds: 任务生存时间（秒）
        """
        self.jobs: Dict[str, TranscriptionJob] = {}
        self.max_jobs = max_jobs
        self.job_ttl_seconds = job_ttl_seconds
        self.lock = threading.Lock()

        # 启动清理线程
        self._start_cleanup_thread()

    def _start_cleanup_thread(self):
        """启动后台清理线程"""
        def cleanup_worker():
            while True:
                try:
                    time.sleep(60)  # 每分钟清理一次
                    self._cleanup_expired_jobs()
                except Exception as e:
                    print(f"[AsyncTranscriptionManager] Cleanup worker error: {e}")

        thread = threading.Thread(target=cleanup_worker, daemon=True)
        thread.start()
        print("[AsyncTranscriptionManager] Cleanup worker started")

    def _cleanup_expired_jobs(self):
        """清理过期任务"""
        with self.lock:
            now = datetime.now()
            expired_jobs = []

            for job_id, job in self.jobs.items():
                # 清理已完成且过期的任务
                if job.status in (TranscriptionStatus.COMPLETED, TranscriptionStatus.FAILED, TranscriptionStatus.CANCELLED):
                    if job.completed_at and (now - job.completed_at).total_seconds() > self.job_ttl_seconds:
                        expired_jobs.append(job_id)

            for job_id in expired_jobs:
                del self.jobs[job_id]
                print(f"[AsyncTranscriptionManager] Cleaned up expired job: {job_id}")

            if expired_jobs:
                print(f"[AsyncTranscriptionManager] Cleaned up {len(expired_jobs)} expired jobs, {len(self.jobs)} active")

    def create_job(
        self,
        audio_path: str,
        model_size: str = "base",
        language: str = "zh",
        device: str = "auto",
        **kwargs
    ) -> TranscriptionJob:
        """
        创建转录任务

        Args:
            audio_path: 音频文件路径
            model_size: 模型大小
            language: 语言
            device: 设备
            **kwargs: 其他参数

        Returns:
            TranscriptionJob: 创建的任务
        """
        with self.lock:
            # 检查任务数限制
            if len(self.jobs) >= self.max_jobs:
                raise RuntimeError(f"任务数已达上限 ({self.max_jobs})，请稍后重试")

            # 生成任务 ID
            job_id = uuid.uuid4().hex[:12]

            # 创建任务
            job = TranscriptionJob(
                job_id=job_id,
                audio_path=audio_path,
                model_size=model_size,
                language=language,
                device=device,
                **kwargs
            )

            self.jobs[job_id] = job
            print(f"[AsyncTranscriptionManager] Created job {job_id} for {audio_path}")

            # 启动后台处理
            thread = threading.Thread(target=self._process_job, args=(job,), daemon=True)
            thread.start()

            return job

    def get_job(self, job_id: str) -> Optional[TranscriptionJob]:
        """
        获取任务

        Args:
            job_id: 任务 ID

        Returns:
            TranscriptionJob or None
        """
        with self.lock:
            return self.jobs.get(job_id)

    def cancel_job(self, job_id: str) -> bool:
        """
        取消任务

        Args:
            job_id: 任务 ID

        Returns:
            bool: 是否成功取消
        """
        with self.lock:
            job = self.jobs.get(job_id)
            if not job:
                return False

            # 只能取消未完成的任务
            if job.status in (TranscriptionStatus.COMPLETED, TranscriptionStatus.FAILED, TranscriptionStatus.CANCELLED):
                return False

            job.cancel()
            print(f"[AsyncTranscriptionManager] Cancelled job {job_id}")
            return True

    def _process_job(self, job: TranscriptionJob):
        """
        后台处理任务

        Args:
            job: 要处理的任务
        """
        try:
            job.started_at = datetime.now()

            # 检查取消
            if job.is_cancelled():
                return

            # 阶段 1: 音频预处理 (10-20%)
            job.status = TranscriptionStatus.PREPROCESSING
            job.stage = "正在提取音频"
            job.progress = 10
            job.message = "正在预处理音频..."

            preprocess_start = time.time()

            # 音频预处理在 transcribe_with_whisperx 内部处理
            time.sleep(0.1)  # 模拟预处理

            job.timings["audioPreprocessTime"] = round((time.time() - preprocess_start) * 1000)

            # 检查取消
            if job.is_cancelled():
                return

            # 阶段 2: 转录 (20-70%)
            job.status = TranscriptionStatus.TRANSCRIBING
            job.stage = "正在语音转文字"
            job.progress = 20
            job.message = "WhisperX 正在转写音频..."

            # 调用 WhisperX 转录
            # 阶段 10B-5-Q5：确保传递与同步路径相同的参数
            result = transcribe_with_whisperx(
                audio_path=job.audio_path,
                model=job.model_size,
                language=job.language,
                device=job.device,
                compute_type=None,  # 让 WhisperX 内部自动选择
                batch_size=16,      # 使用默认 batch_size
                skip_align=False,   # 启用对齐
                diarization_enabled=True,  # 启用说话人分离
                hf_token=None,      # 从环境变量读取
                initial_prompt=None # 从环境变量读取
            )

            # 检查取消
            if job.is_cancelled():
                return

            # 阶段 3: 完成 (100%)
            job.status = TranscriptionStatus.COMPLETED
            job.stage = "处理完成"
            job.progress = 100
            job.message = "转录成功"

            # 构建结果
            job.result = {
                "transcript": result.get("text", ""),
                "transcriptTurns": result.get("turns", []),
                "segments": result.get("segments", []),
                "language": result.get("language", job.language),
                "transcriptionProvider": "whisperx",
                "transcriptionModel": job.model_size,
                "diarizationEnabled": result.get("diarizationEnabled", False),
                "diarizationProvider": result.get("diarizationProvider"),
                "diarizationModel": result.get("diarizationModel"),
                "alignmentStatus": result.get("alignmentStatus"),
                "alignmentError": result.get("alignmentError"),
                "audioDuration": result.get("raw", {}).get("audioDuration", 0),
                "raw": result.get("raw", {})
            }

            # 更新时间统计
            total_time = (datetime.now() - job.started_at).total_seconds()
            job.timings["totalTime"] = round(total_time * 1000)

            # 从 raw 数据中提取详细时间统计
            raw_data = result.get("raw", {})
            if "processingTimeSeconds" in raw_data:
                job.timings["whisperTranscribeTime"] = round(raw_data["processingTimeSeconds"] * 1000)

        except Exception as e:
            print(f"[AsyncTranscriptionManager] Job {job.job_id} failed: {e}")
            job.status = TranscriptionStatus.FAILED
            job.stage = "处理失败"
            job.progress = 100
            job.error = str(e)
            job.message = f"转录失败: {str(e)}"

        finally:
            job.completed_at = datetime.now()


# 全局单例
_transcription_manager = None


def get_transcription_manager() -> AsyncTranscriptionManager:
    """获取全局转录任务管理器"""
    global _transcription_manager
    if _transcription_manager is None:
        _transcription_manager = AsyncTranscriptionManager()
    return _transcription_manager
