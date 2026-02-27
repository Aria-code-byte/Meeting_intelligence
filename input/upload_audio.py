"""
音频文件上传模块

支持用户上传音频文件（mp3, wav, m4a）并保存到存储。
"""

import os
import shutil
from pathlib import Path
from typing import Optional

from input.types import MeetingInputResult


# 支持的音频格式
SUPPORTED_AUDIO_FORMATS = {".mp3", ".wav", ".m4a"}

# 默认文件大小限制（500MB）
DEFAULT_MAX_FILE_SIZE_MB = 500
MAX_FILE_SIZE_BYTES = DEFAULT_MAX_FILE_SIZE_MB * 1024 * 1024

# 数据存储目录
DATA_DIR = Path(__file__).parent.parent / "data" / "raw_audio"


def _ensure_data_dir() -> Path:
    """确保数据目录存在"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return DATA_DIR


def _validate_audio_format(file_path: Path) -> None:
    """
    验证音频文件格式

    Args:
        file_path: 音频文件路径

    Raises:
        ValueError: 文件格式不支持
    """
    if file_path.suffix.lower() not in SUPPORTED_AUDIO_FORMATS:
        raise ValueError(
            f"不支持的音频格式: {file_path.suffix}. "
            f"支持的格式: {', '.join(SUPPORTED_AUDIO_FORMATS)}"
        )


def _validate_file_size(file_path: Path) -> None:
    """
    验证文件大小

    Args:
        file_path: 文件路径

    Raises:
        ValueError: 文件超出大小限制
    """
    file_size = file_path.stat().st_size
    if file_size > MAX_FILE_SIZE_BYTES:
        size_mb = file_size / (1024 * 1024)
        raise ValueError(
            f"文件过大: {size_mb:.1f}MB. "
            f"最大支持: {DEFAULT_MAX_FILE_SIZE_MB}MB"
        )


def _generate_output_filename(original_filename: str) -> str:
    """
    生成输出文件名（保持原始扩展名）

    Args:
        original_filename: 原始文件名

    Returns:
        输出文件名
    """
    original_path = Path(original_filename)
    timestamp = _get_timestamp()
    return f"audio_{timestamp}{original_path.suffix}"


def _get_timestamp() -> str:
    """获取当前时间戳字符串"""
    from datetime import datetime
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def upload_audio(
    source_path: str,
    max_size_mb: Optional[int] = None
) -> MeetingInputResult:
    """
    上传音频文件

    Args:
        source_path: 源音频文件路径
        max_size_mb: 可选的文件大小限制（MB），默认使用 DEFAULT_MAX_FILE_SIZE_MB

    Returns:
        MeetingInputResult: 包含保存的音频文件路径

    Raises:
        FileNotFoundError: 源文件不存在
        ValueError: 文件格式不支持或文件过大
    """
    source = Path(source_path)

    # 验证源文件存在
    if not source.exists():
        raise FileNotFoundError(f"源文件不存在: {source_path}")

    # 验证文件格式
    _validate_audio_format(source)

    # 验证文件大小
    if max_size_mb is not None:
        custom_max_bytes = max_size_mb * 1024 * 1024
        file_size = source.stat().st_size
        if file_size > custom_max_bytes:
            size_mb = file_size / (1024 * 1024)
            raise ValueError(
                f"文件过大: {size_mb:.1f}MB. 最大支持: {max_size_mb}MB"
            )
    else:
        _validate_file_size(source)

    # 确保目标目录存在
    output_dir = _ensure_data_dir()

    # 生成输出文件名
    output_filename = _generate_output_filename(source.name)
    output_path = output_dir / output_filename

    # 复制文件到目标位置
    shutil.copy2(source, output_path)

    return MeetingInputResult(
        audio_path=str(output_path.absolute()),
        video_path=None
    )


def get_supported_formats() -> set[str]:
    """获取支持的音频格式集合"""
    return SUPPORTED_AUDIO_FORMATS.copy()


def get_max_file_size_mb() -> int:
    """获取默认最大文件大小（MB）"""
    return DEFAULT_MAX_FILE_SIZE_MB
