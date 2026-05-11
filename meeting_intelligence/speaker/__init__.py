"""
发言人识别模块 (Speaker Diarization)

提供发言人分离、识别、聚类功能。
"""

from .types import SpeakerSegment, SpeakerInfo, DiarizationResult
from .diarization import SpeakerDiarization

__all__ = [
    "SpeakerSegment",
    "SpeakerInfo",
    "DiarizationResult",
    "SpeakerDiarization",
]
