"""
Backend Services Module
====================
各种后端服务的实现（WhisperX、pyannote 等）
"""

from .whisperx_service import transcribe_with_whisperx

__all__ = ["transcribe_with_whisperx"]
