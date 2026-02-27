"""
Summary loading and export.

提供总结结果的加载和导出功能。
"""

import json
from pathlib import Path
from typing import Union

from summarizer.types import SummaryResult


def load_summary(path: Union[str, Path]) -> SummaryResult:
    """
    从磁盘加载总结

    Args:
        path: 总结文件路径（.json）

    Returns:
        SummaryResult 实例

    Raises:
        FileNotFoundError: 如果文件不存在
        ValueError: 如果文件格式无效
    """
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"总结文件不存在: {path}")

    if path.suffix != ".json":
        raise ValueError(f"总结文件必须是 JSON 格式 (.json)，当前: {path.suffix}")

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"文件 JSON 格式无效: {e}") from e

    return SummaryResult.from_dict(data)


def export_json(summary: SummaryResult, output_path: str) -> str:
    """
    导出为 JSON 格式

    Args:
        summary: SummaryResult 实例
        output_path: 输出文件路径

    Returns:
        导出的文件路径
    """
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    with open(output, "w", encoding="utf-8") as f:
        json.dump(summary.to_dict(), f, ensure_ascii=False, indent=2)

    return str(output)


def export_text(summary: SummaryResult, output_path: str) -> str:
    """
    导出为纯文本格式

    Args:
        summary: SummaryResult 实例
        output_path: 输出文件路径

    Returns:
        导出的文件路径
    """
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    lines = []
    lines.append("=" * 60)
    lines.append(f"会议总结 ({summary.template_role})")
    lines.append("=" * 60)
    lines.append("")
    lines.append(f"模板: {summary.template_name}")
    lines.append(f"生成时间: {summary.created_at}")
    lines.append("")

    for section in summary.sections:
        lines.append(f"## {section.title}")
        lines.append("")
        lines.append(section.content)
        lines.append("")

    with open(output, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return str(output)


def export_markdown(summary: SummaryResult, output_path: str) -> str:
    """
    导出为 Markdown 格式

    Args:
        summary: SummaryResult 实例
        output_path: 输出文件路径

    Returns:
        导出的文件路径
    """
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    with open(output, "w", encoding="utf-8") as f:
        f.write(summary.to_markdown())

    return str(output)
