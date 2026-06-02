"""
核心数据模型
"""

from typing import Dict, List, Any, Optional
from datetime import datetime


class Meeting:
    """会议数据模型"""

    def __init__(
        self,
        meeting_id: str,
        title: str,
        file_name: Optional[str] = None,
        file_path: Optional[str] = None,
        audio_path: Optional[str] = None,
        file_size: Optional[int] = None,
        status: str = "uploaded"
    ):
        self.meeting_id = meeting_id
        self.title = title
        self.file_name = file_name
        self.file_path = file_path
        self.audio_path = audio_path
        self.file_size = file_size
        self.status = status
        self.uploaded_at = datetime.now().isoformat()

        # 转写相关
        self.transcript: Optional[str] = None
        self.transcript_turns: Optional[List[Dict[str, Any]]] = None
        self.segments: Optional[List[Dict[str, Any]]] = None
        self.transcription_completed_at: Optional[str] = None
        self.transcription_task_id: Optional[str] = None
        self.audio_duration: Optional[float] = None

        # LLM 增强相关
        self.enhanced_transcript_turns: Optional[List[Dict[str, Any]]] = None
        self.enhancement_provider: Optional[str] = None
        self.enhancement_model: Optional[str] = None
        self.enhancement_time: Optional[str] = None
        self.is_enhanced: bool = False

        # 总结相关
        self.summary: Optional[str] = None
        self.summary_markdown: Optional[str] = None
        self.template_id: Optional[str] = None
        self.summary_completed_at: Optional[str] = None
        self.summary_task_id: Optional[str] = None

        # 错误信息
        self.error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "meeting_id": self.meeting_id,
            "title": self.title,
            "file_name": self.file_name,
            "file_path": self.file_path,
            "audio_path": self.audio_path,
            "file_size": self.file_size,
            "status": self.status,
            "uploaded_at": self.uploaded_at,
            "transcript": self.transcript,
            "transcript_turns": self.transcript_turns,
            "segments": self.segments,
            "transcription_completed_at": self.transcription_completed_at,
            "transcription_task_id": self.transcription_task_id,
            "audio_duration": self.audio_duration,
            "enhanced_transcript_turns": self.enhanced_transcript_turns,
            "enhancement_provider": self.enhancement_provider,
            "enhancement_model": self.enhancement_model,
            "enhancement_time": self.enhancement_time,
            "is_enhanced": self.is_enhanced,
            "summary": self.summary,
            "summary_markdown": self.summary_markdown,
            "template_id": self.template_id,
            "summary_completed_at": self.summary_completed_at,
            "summary_task_id": self.summary_task_id,
            "error_message": self.error_message,
        }


class Task:
    """任务数据模型"""

    def __init__(
        self,
        task_id: str,
        meeting_id: str,
        task_type: str,
        status: str = "processing"
    ):
        self.task_id = task_id
        self.meeting_id = meeting_id
        self.task_type = task_type  # "transcription" or "summary" or "enhancement"
        self.status = status  # "processing", "completed", "failed"
        self.progress = 0
        self.current_step = "初始化中"
        self.created_at = datetime.now().isoformat()
        self.completed_at: Optional[str] = None
        self.error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "task_id": self.task_id,
            "meeting_id": self.meeting_id,
            "task_type": self.task_type,
            "status": self.status,
            "progress": self.progress,
            "current_step": self.current_step,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "error_message": self.error_message,
        }
