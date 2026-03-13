"""
ASR providers module.
"""

from asr.providers.base import BaseASRProvider
from asr.providers.whisper import WhisperProvider
from asr.providers.faster_whisper import FasterWhisperProvider

__all__ = ["BaseASRProvider", "WhisperProvider", "FasterWhisperProvider"]
