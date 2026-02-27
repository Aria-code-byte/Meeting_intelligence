"""
Shared types for the meeting input module.

This module defines the common data structures used across all input methods.
"""

from dataclasses import dataclass
from typing import Optional
from pathlib import Path


@dataclass
class MeetingInputResult:
    """
    统一的会议输入结果接口

    所有输入方法（音频上传、视频上传、录音）都返回此结构。

    Attributes:
        audio_path: 音频文件路径（可选，Phase 1 中视频上传时为 None）
        video_path: 视频文件路径（可选，仅视频上传时有值）
    """
    audio_path: Optional[str] = None
    video_path: Optional[str] = None

    def __post_init__(self):
        """确保文件路径存在且可访问（仅验证非 None 的路径）"""
        if self.audio_path is not None:
            audio_file = Path(self.audio_path)
            if not audio_file.exists():
                raise FileNotFoundError(f"音频文件不存在: {self.audio_path}")

        if self.video_path is not None:
            video_file = Path(self.video_path)
            if not video_file.exists():
                raise FileNotFoundError(f"视频文件不存在: {self.video_path}")

    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "audio_path": self.audio_path,
            "video_path": self.video_path
        }
