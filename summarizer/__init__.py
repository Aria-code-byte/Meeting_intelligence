"""
Summarizer module - LLM 总结引擎

整合转录文档和用户模板，生成结构化总结。
这是项目的核心价值实现。
"""

from summarizer.types import SummaryResult, SummarySection, SectionFormat
from summarizer.generate import generate_summary
from summarizer.export import load_summary, export_json, export_text, export_markdown
from summarizer.pipeline import audio_to_summary, video_to_summary, quick_summary

__all__ = [
    # Types
    "SummaryResult",
    "SummarySection",
    "SectionFormat",
    # Generate
    "generate_summary",
    # Export
    "load_summary",
    "export_json",
    "export_text",
    "export_markdown",
    # Pipeline
    "audio_to_summary",
    "video_to_summary",
    "quick_summary",
]
