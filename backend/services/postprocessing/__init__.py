"""
后处理模块
================
提供转录结果的后处理功能

模块：
- hotword_corrector: 热词纠错
- speaker_role_mapper: 发言人角色映射
- filler_cleaner: 口癖清理
- traditional_simplified: 繁简体统一
- readable_generator: 可读转录文本生成
"""

from .hotword_corrector import HotwordCorrector, create_domain_hotword_dict
from .speaker_role_mapper import SpeakerRoleMapper
from .filler_cleaner import FillerWordCleaner
from .traditional_simplified import TraditionalSimplifiedNormalizer
from .readable_generator import ReadableTranscriptGenerator

__all__ = [
    "HotwordCorrector",
    "create_domain_hotword_dict",
    "SpeakerRoleMapper",
    "FillerWordCleaner",
    "TraditionalSimplifiedNormalizer",
    "ReadableTranscriptGenerator"
]
