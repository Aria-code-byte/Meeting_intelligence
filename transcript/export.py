"""
Transcript export - 导出原始会议文档到多种格式
"""

import json
from pathlib import Path
from typing import Union

from transcript.types import TranscriptDocument
from transcript.build import format_timestamp


def export_json(
    document: TranscriptDocument,
    output_path: Union[str, Path]
) -> str:
    """
    导出为 JSON 格式（完整的原始数据）

    Args:
        document: TranscriptDocument 实例
        output_path: 输出文件路径

    Returns:
        导出的文件路径
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(document.to_dict(), f, ensure_ascii=False, indent=2)

    return str(output_path)


def export_text(
    document: TranscriptDocument,
    output_path: Union[str, Path]
) -> str:
    """
    导出为纯文本格式（人类可读）

    Args:
        document: TranscriptDocument 实例
        output_path: 输出文件路径

    Returns:
        导出的文件路径
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    lines = []

    # 元数据头部
    lines.append("=" * 60)
    lines.append("原始会议文档")
    lines.append("=" * 60)
    lines.append(f"音频文件: {document.audio_path}")
    lines.append(f"时长: {format_timestamp(document.duration)}")
    lines.append(f"ASR 提供商: {document.asr_provider}")
    lines.append(f"创建时间: {document.created_at}")
    lines.append(f"语音片段数: {document.utterance_count}")
    lines.append("=" * 60)
    lines.append("")

    # 语音片段内容
    for u in document.utterances:
        ts = format_timestamp(u["start"])
        text = u["text"].strip()
        lines.append(f"{ts} {text}")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return str(output_path)


def export_markdown(
    document: TranscriptDocument,
    output_path: Union[str, Path]
) -> str:
    """
    导出为 Markdown 格式（带格式化）

    Args:
        document: TranscriptDocument 实例
        output_path: 输出文件路径

    Returns:
        导出的文件路径
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    lines = []

    # YAML frontmatter (元数据)
    lines.append("---")
    lines.append(f"audio_path: {document.audio_path}")
    lines.append(f"duration: {document.duration}")
    lines.append(f"duration_formatted: {format_timestamp(document.duration)}")
    lines.append(f"asr_provider: {document.asr_provider}")
    lines.append(f"created_at: {document.created_at}")
    lines.append(f"utterance_count: {document.utterance_count}")
    lines.append("---")
    lines.append("")

    # 标题
    lines.append("# 原始会议文档")
    lines.append("")

    # 元数据表格
    lines.append("## 元数据")
    lines.append("")
    lines.append("| 字段 | 值 |")
    lines.append("|------|-----|")
    lines.append(f"| 音频文件 | `{document.audio_path}` |")
    lines.append(f"| 时长 | {format_timestamp(document.duration)} ({document.duration:.1f}秒) |")
    lines.append(f"| ASR 提供商 | {document.asr_provider} |")
    lines.append(f"| 创建时间 | {document.created_at} |")
    lines.append(f"| 语音片段数 | {document.utterance_count} |")
    lines.append("")

    # 内容
    lines.append("## 内容")
    lines.append("")

    for u in document.utterances:
        start_ts = format_timestamp(u["start"])
        end_ts = format_timestamp(u["end"])
        text = u["text"].strip()
        lines.append(f"- **{start_ts} - {end_ts}** {text}")

    lines.append("")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return str(output_path)


def export_auto(
    document: TranscriptDocument,
    output_path: Union[str, Path]
) -> str:
    """
    根据文件扩展名自动选择导出格式

    Args:
        document: TranscriptDocument 实例
        output_path: 输出文件路径

    Returns:
        导出的文件路径

    Raises:
        ValueError: 如果不支持该格式
    """
    output_path = Path(output_path)
    suffix = output_path.suffix.lower()

    exporters = {
        ".json": export_json,
        ".txt": export_text,
        ".md": export_markdown
    }

    if suffix not in exporters:
        raise ValueError(
            f"不支持的导出格式: {suffix}。"
            f"支持的格式: {', '.join(exporters.keys())}"
        )

    return exporters[suffix](document, output_path)
