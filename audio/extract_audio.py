"""
音频提取模块

使用 ffmpeg 从视频文件中提取音轨并转换为标准格式。
"""

import subprocess
import tempfile
from pathlib import Path
from typing import Optional

from audio.types import ProcessedAudio
from input.upload_audio import DATA_DIR


# 标准音频输出格式
OUTPUT_SAMPLE_RATE = 16000  # 16kHz
OUTPUT_CHANNELS = 1  # 单声道
OUTPUT_CODEC = "pcm_s16le"  # 16-bit PCM


def _check_ffmpeg_available() -> bool:
    """
    检查 ffmpeg 是否可用

    Returns:
        True 如果 ffmpeg 已安装
    """
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            timeout=5
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def _get_output_path(input_path: str) -> Path:
    """
    生成输出文件路径

    Args:
        input_path: 输入文件路径

    Returns:
        输出文件路径（WAV 格式）
    """
    from input.upload_audio import _get_timestamp
    timestamp = _get_timestamp()
    filename = f"extracted_{timestamp}.wav"
    return DATA_DIR / filename


def _extract_audio_ffmpeg(
    video_path: str,
    output_path: Path
) -> float:
    """
    使用 ffmpeg 提取音频

    Args:
        video_path: 视频文件路径
        output_path: 输出音频文件路径

    Returns:
        音频时长（秒）

    Raises:
        RuntimeError: ffmpeg 不可用或提取失败
    """
    if not _check_ffmpeg_available():
        raise RuntimeError(
            "ffmpeg 未安装。请安装 ffmpeg: sudo apt-get install ffmpeg"
        )

    # ffmpeg 命令：提取音频并转换为标准格式
    # -i: 输入文件
    # -vn: 不处理视频
    # -ar: 采样率
    # -ac: 声道数
    # -c:a: 音频编解码器
    # -y: 覆盖输出文件
    cmd = [
        "ffmpeg",
        "-i", video_path,
        "-vn",
        "-ar", str(OUTPUT_SAMPLE_RATE),
        "-ac", str(OUTPUT_CHANNELS),
        "-c:a", OUTPUT_CODEC,
        "-y",
        str(output_path)
    ]

    try:
        # 运行 ffmpeg
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5分钟超时
        )

        if result.returncode != 0:
            error_msg = result.stderr.strip()
            # 检查是否是"没有音轨"错误
            if "Stream #0:0: Audio: not found" in error_msg or "Audio: none" in error_msg:
                raise ValueError("视频文件不包含音轨")
            raise RuntimeError(f"ffmpeg 提取失败: {error_msg}")

        # 获取音频时长
        duration = _get_audio_duration(str(output_path))
        return duration

    except subprocess.TimeoutExpired:
        raise RuntimeError("音频提取超时（超过5分钟）")
    except ValueError:
        raise
    except Exception as e:
        raise RuntimeError(f"音频提取失败: {e}")


def _get_audio_duration(audio_path: str) -> float:
    """
    获取音频文件时长（使用 ffprobe）

    Args:
        audio_path: 音频文件路径

    Returns:
        音频时长（秒）

    Raises:
        RuntimeError: 无法获取时长
    """
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(audio_path)
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode != 0:
            # 如果 ffprobe 失败，使用简单的文件大小估算
            # 16kHz, 16-bit, mono = 32000 bytes/second
            file_size = Path(audio_path).stat().st_size
            return file_size / 32000.0

        duration = float(result.stdout.strip())
        return duration

    except (subprocess.TimeoutExpired, ValueError, Exception):
        # 降级方案：使用文件大小估算
        file_size = Path(audio_path).stat().st_size
        return file_size / 32000.0


def extract_audio(video_path: str) -> ProcessedAudio:
    """
    从视频文件中提取音频

    Args:
        video_path: 视频文件路径（支持 mp4, mkv, mov）

    Returns:
        ProcessedAudio: 包含提取的音频文件路径和时长

    Raises:
        FileNotFoundError: 视频文件不存在
        RuntimeError: ffmpeg 不可用或提取失败
        ValueError: 视频文件不包含音轨

    Example:
        >>> audio = extract_audio("/path/to/video.mp4")
        >>> print(f"提取的音频: {audio.path}, 时长: {audio.duration}秒")
    """
    # 验证输入文件
    video_file = Path(video_path)
    if not video_file.exists():
        raise FileNotFoundError(f"视频文件不存在: {video_path}")

    # 确保输出目录存在
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # 生成输出路径
    output_path = _get_output_path(video_path)

    # 提取音频
    duration = _extract_audio_ffmpeg(str(video_file), output_path)

    return ProcessedAudio(
        path=str(output_path.absolute()),
        duration=duration
    )


def is_ffmpeg_available() -> bool:
    """
    检查 ffmpeg 是否可用

    Returns:
        True 如果 ffmpeg 已安装且可用
    """
    return _check_ffmpeg_available()
