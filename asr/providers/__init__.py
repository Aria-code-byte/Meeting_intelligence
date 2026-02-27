"""
ASR providers module.
"""

from asr.providers.base import BaseASRProvider
from asr.providers.whisper import WhisperProvider

__all__ = ["BaseASRProvider", "WhisperProvider"]
