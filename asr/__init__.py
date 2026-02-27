"""
ASR (Automatic Speech Recognition) module.

Provides speech-to-text conversion with timestamp support.
"""

from asr.types import TranscriptionResult, Utterance
from asr.transcribe import (
    transcribe,
    load_transcript,
    export_text,
    get_provider
)

__all__ = [
    "TranscriptionResult",
    "Utterance",
    "transcribe",
    "load_transcript",
    "export_text",
    "get_provider"
]
