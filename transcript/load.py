"""
Transcript loading - 从磁盘加载原始会议文档
"""

import json
from pathlib import Path
from typing import Union

from transcript.types import TranscriptDocument


def load_transcript(path: Union[str, Path]) -> TranscriptDocument:
    """
    从磁盘加载原始会议文档

    Args:
        path: 文档文件路径（.json）

    Returns:
        TranscriptDocument 实例

    Raises:
        FileNotFoundError: 如果文件不存在
        ValueError: 如果文件格式无效或数据不完整
    """
    path = Path(path)

    # 检查文件存在
    if not path.exists():
        raise FileNotFoundError(f"文档文件不存在: {path}")

    # 检查文件类型
    if path.suffix != ".json":
        raise ValueError(
            f"文档文件必须是 JSON 格式 (.json)，当前: {path.suffix}"
        )

    # 读取并解析 JSON
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"文件 JSON 格式无效: {e}") from e

    # 验证数据结构
    if not isinstance(data, dict):
        raise ValueError("文档数据必须是对象（字典）")

    if "metadata" not in data:
        raise ValueError("文档数据缺少 metadata 字段")

    if "utterances" not in data:
        raise ValueError("文档数据缺少 utterances 字段")

    # 从字典创建文档
    document = TranscriptDocument.from_dict(data)

    # 设置文档路径
    document.document_path = str(path)

    return document


def list_transcripts(directory: Union[str, Path] = "data/transcripts") -> list:
    """
    列出目录中的所有 transcript 文档

    Args:
        directory: 文档目录路径

    Returns:
        文档路径列表，按修改时间排序（最新的在前）
    """
    dir_path = Path(directory)

    if not dir_path.exists():
        return []

    # 获取所有 JSON 文件
    json_files = list(dir_path.glob("transcript_*.json"))

    # 按修改时间排序（最新的在前）
    json_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)

    return [str(f) for f in json_files]


def get_latest_transcript(directory: Union[str, Path] = "data/transcripts"):
    """
    获取最新的 transcript 文档

    Args:
        directory: 文档目录路径

    Returns:
        最新文档的 TranscriptDocument 实例，如果没有则返回 None

    Raises:
        ValueError: 如果文档加载失败
    """
    transcripts = list_transcripts(directory)

    if not transcripts:
        return None

    return load_transcript(transcripts[0])


def validate_transcript_file(path: Union[str, Path]) -> dict:
    """
    验证 transcript 文档文件的有效性

    Args:
        path: 文档文件路径

    Returns:
        验证结果字典 {valid: bool, errors: list, warnings: list}
    """
    result = {
        "valid": True,
        "errors": [],
        "warnings": []
    }

    path = Path(path)

    # 检查文件存在
    if not path.exists():
        result["valid"] = False
        result["errors"].append("文件不存在")
        return result

    # 检查文件扩展名
    if path.suffix != ".json":
        result["warnings"].append(f"非标准扩展名: {path.suffix}")

    # 尝试解析 JSON
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        result["valid"] = False
        result["errors"].append(f"JSON 解析失败: {e}")
        return result

    # 验证数据结构
    if not isinstance(data, dict):
        result["valid"] = False
        result["errors"].append("根元素不是对象")
        return result

    if "metadata" not in data:
        result["valid"] = False
        result["errors"].append("缺少 metadata 字段")

    if "utterances" not in data:
        result["valid"] = False
        result["errors"].append("缺少 utterances 字段")

    # 验证 metadata 字段
    if "metadata" in data:
        meta = data["metadata"]
        required_meta_fields = ["audio_path", "duration", "asr_provider"]
        for field in required_meta_fields:
            if field not in meta:
                result["valid"] = False
                result["errors"].append(f"metadata 缺少字段: {field}")

    # 验证 utterances 结构
    if "utterances" in data:
        utterances = data["utterances"]
        if not isinstance(utterances, list):
            result["valid"] = False
            result["errors"].append("utterances 不是列表")
        else:
            for i, u in enumerate(utterances):
                if not isinstance(u, dict):
                    result["errors"].append(f"utterance[{i}] 不是对象")
                    continue

                required_fields = ["start", "end", "text"]
                for field in required_fields:
                    if field not in u:
                        result["valid"] = False
                        result["errors"].append(f"utterance[{i}] 缺少字段: {field}")

    return result
