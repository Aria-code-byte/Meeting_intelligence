"""
Audio processing module.

Provides audio extraction and preprocessing capabilities:
- Extract audio from video files using ffmpeg
- Audio preprocessing (normalization, silence trimming)
"""

from audio.types import ProcessedAudio
from audio.extract_audio import extract_audio, is_ffmpeg_available
from audio.preprocess import preprocess_audio, PreprocessOptions

__all__ = [
    "ProcessedAudio",
    "extract_audio",
    "is_ffmpeg_available",
    "preprocess_audio",
    "PreprocessOptions"
]
