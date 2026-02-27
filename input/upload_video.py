"""
视频文件上传模块

支持用户上传视频文件（mp4, mkv, mov）并提取音轨。
"""

import os
import shutil
from pathlib import Path
from typing import Optional

from input.types import MeetingInputResult
from input.upload_audio import _get_timestamp, DATA_DIR


# 支持的视频格式
SUPPORTED_VIDEO_FORMATS = {".mp4", ".mkv", ".mov"}

# 默认文件大小限制（2GB - 视频文件通常较大）
DEFAULT_MAX_VIDEO_SIZE_MB = 2048
MAX_VIDEO_SIZE_BYTES = DEFAULT_MAX_VIDEO_SIZE_MB * 1024 * 1024


def _ensure_data_dir() -> Path:
    """确保数据目录存在"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return DATA_DIR


def _validate_video_format(file_path: Path) -> None:
    """
    验证视频文件格式

    Args:
        file_path: 视频文件路径

    Raises:
        ValueError: 文件格式不支持
    """
    if file_path.suffix.lower() not in SUPPORTED_VIDEO_FORMATS:
        raise ValueError(
            f"不支持的视频格式: {file_path.suffix}. "
            f"支持的格式: {', '.join(SUPPORTED_VIDEO_FORMATS)}"
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
    if file_size > MAX_VIDEO_SIZE_BYTES:
        size_mb = file_size / (1024 * 1024)
        raise ValueError(
            f"文件过大: {size_mb:.1f}MB. "
            f"最大支持: {DEFAULT_MAX_VIDEO_SIZE_MB}MB"
        )


def _generate_output_filename(original_filename: str, suffix: str) -> str:
    """
    生成输出文件名

    Args:
        original_filename: 原始文件名
        suffix: 文件扩展名

    Returns:
        输出文件名
    """
    timestamp = _get_timestamp()
    return f"video_{timestamp}{suffix}"


def upload_video(
    source_path: str,
    max_size_mb: Optional[int] = None,
    extract_audio: bool = True
) -> MeetingInputResult:
    """
    上传视频文件并提取音轨

    Args:
        source_path: 源视频文件路径
        max_size_mb: 可选的文件大小限制（MB），默认使用 DEFAULT_MAX_VIDEO_SIZE_MB
        extract_audio: 是否提取音频（默认 True）

    Returns:
        MeetingInputResult: 包含保存的视频文件路径和提取的音频路径

    Raises:
        FileNotFoundError: 源文件不存在
        ValueError: 文件格式不支持或文件过大
        RuntimeError: 音频提取失败（需要 ffmpeg）
    """
    source = Path(source_path)

    # 验证源文件存在
    if not source.exists():
        raise FileNotFoundError(f"源文件不存在: {source_path}")

    # 验证文件格式
    _validate_video_format(source)

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
    output_filename = _generate_output_filename(source.name, source.suffix)
    output_path = output_dir / output_filename

    # 复制视频文件到目标位置（保留用于 V2 的 PPT 分析）
    shutil.copy2(source, output_path)

    # 提取音频
    audio_path: Optional[str] = None
    if extract_audio:
        try:
            # 延迟导入以避免循环依赖
            from audio.extract_audio import extract_audio as extract
            result = extract(str(output_path))
            audio_path = result.path
        except Exception as e:
            raise RuntimeError(f"音频提取失败: {e}")

    return MeetingInputResult(
        audio_path=audio_path,
        video_path=str(output_path.absolute())
    )


def get_supported_formats() -> set[str]:
    """获取支持的视频格式集合"""
    return SUPPORTED_VIDEO_FORMATS.copy()


def get_max_file_size_mb() -> int:
    """获取默认最大文件大小（MB）"""
    return DEFAULT_MAX_VIDEO_SIZE_MB
