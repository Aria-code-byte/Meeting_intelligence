"""
Transcript module - 原始会议文档生成与格式化

从 ASR 结果生成结构化的原始会议文档，
并支持将碎片化 utterances 格式化为可读文稿，
以及使用 LLM 优化转录文本的可读性。
"""

from transcript.types import TranscriptDocument
from transcript.build import build_transcript
from transcript.load import load_transcript
from transcript.export import export_json, export_text, export_markdown
from transcript.formatter import (
    TranscriptFormatter,
    FormattedTranscript,
    FormatterConfig,
    FormatMethod,
    Paragraph,
    Section,
    format_transcript,
    format_utterances,
)
from transcript.refiner import (
    TranscriptRefiner,
    RefinerConfig,
    RefineMode,
    refine_transcript,
    refine_transcript_file,
    refine_with_rules,
)
from transcript.enhanced import EnhancedTranscriptConfig
from transcript.enhanced_builder import (
    EnhancedTranscript,
    EnhancedTranscriptConfig as EnhancedBuilderConfig,
    Sentence,
    Chunk,
    TimeWindow,
    build_enhanced_transcript,
    chunk_transcript_by_time,
    create_sentences_from_utterances,
)

__all__ = [
    "TranscriptDocument",
    "build_transcript",
    "load_transcript",
    "export_json",
    "export_text",
    "export_markdown",
    "TranscriptFormatter",
    "FormattedTranscript",
    "FormatterConfig",
    "FormatMethod",
    "Paragraph",
    "Section",
    "format_transcript",
    "format_utterances",
    "TranscriptRefiner",
    "RefinerConfig",
    "RefineMode",
    "refine_transcript",
    "refine_transcript_file",
    "refine_with_rules",
    "EnhancedTranscriptConfig",
    "EnhancedTranscript",
    "EnhancedBuilderConfig",
    "Sentence",
    "Chunk",
    "TimeWindow",
    "build_enhanced_transcript",
    "chunk_transcript_by_time",
    "create_sentences_from_utterances",
]
