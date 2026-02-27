"""
Shared types for the audio processing module.

This module defines the common data structures used across all audio processing operations.
"""

from dataclasses import dataclass
from pathlib import Path


@dataclass
class ProcessedAudio:
    """
    处理后的音频结果接口

    所有音频操作（提取、预处理）都返回此结构。

    Attributes:
        path: 处理后的音频文件绝对路径
        duration: 音频时长（秒）
    """
    path: str
    duration: float

    def __post_init__(self):
        """确保文件路径存在且可访问"""
        audio_file = Path(self.path)
        if not audio_file.exists():
            raise FileNotFoundError(f"音频文件不存在: {self.path}")

        if self.duration <= 0:
            raise ValueError(f"音频时长必须大于 0: {self.duration}")

    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "path": self.path,
            "duration": self.duration
        }
