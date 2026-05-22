"""
Base ASR provider interface.

All ASR providers must implement this interface.
"""

from abc import ABC, abstractmethod
from typing import List

from asr.types import Utterance


class BaseASRProvider(ABC):
    """
    ASR 提供商基础接口

    所有 ASR 提供商必须继承此类并实现 transcribe 方法。
    """

    @abstractmethod
    def transcribe(
        self,
        audio_path: str,
        language: str = "auto"
    ) -> List[Utterance]:
        """
        转写音频文件

        Args:
            audio_path: 音频文件路径
            language: 语言代码（"auto" 自动检测，"zh" 中文，"en" 英文）

        Returns:
            识别结果列表（按时间顺序）

        Raises:
            FileNotFoundError: 音频文件不存在
            RuntimeError: 转写失败
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """提供商名称"""
        pass

    def _validate_audio_file(self, audio_path: str) -> None:
        """
        验证音频文件格式

        Args:
            audio_path: 音频文件路径

        Raises:
            FileNotFoundError: 文件不存在
            ValueError: 格式不支持
        """
        from pathlib import Path

        audio_file = Path(audio_path)
        if not audio_file.exists():
            raise FileNotFoundError(f"音频文件不存在: {audio_path}")

        # 支持的音频格式（Whisper内部使用ffmpeg处理这些格式）
        supported_formats = {".wav", ".mp3", ".mp4", ".m4a", ".webm", ".ogg", ".flac"}
        if audio_file.suffix.lower() not in supported_formats:
            raise ValueError(
                f"不支持的音频格式: {audio_file.suffix}. "
                f"支持的格式: {', '.join(supported_formats)}"
            )

        # TODO: 可以添加更详细的格式验证（采样率、声道数）
