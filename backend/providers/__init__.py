"""
Provider Adapter Layer
====================
统一的AI服务提供商适配层，提供一致的API接口
"""
from .base import BaseProvider, ProviderResult, ProviderType
from .transcription import TranscriptionProvider, FallbackTranscriptionProvider
from .summary import SummaryProvider, FallbackSummaryProvider

__all__ = [
    'BaseProvider',
    'ProviderResult',
    'ProviderType',
    'TranscriptionProvider',
    'FallbackTranscriptionProvider',
    'SummaryProvider',
    'FallbackSummaryProvider',
]
