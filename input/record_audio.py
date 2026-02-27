"""
应用内音频录制模块

支持从本地麦克风录制音频，分段保存以防止长时间崩溃。
"""

import threading
import time
from pathlib import Path
from typing import Optional
from datetime import datetime

from input.types import MeetingInputResult
from input.upload_audio import DATA_DIR


# 默认最大录制时长（2小时）
DEFAULT_MAX_DURATION_SECONDS = 2 * 60 * 60

# 录制状态
_recording_lock = threading.Lock()
_is_recording = False
_recording_start_time: Optional[datetime] = None
_audio_writer = None


def _ensure_data_dir() -> Path:
    """确保数据目录存在"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return DATA_DIR


def _generate_recording_filename() -> str:
    """
    生成录音文件名（基于时间戳）

    Returns:
        输出文件名（.wav 格式）
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"recording_{timestamp}.wav"


def _check_max_duration(max_duration_seconds: float) -> bool:
    """
    检查是否超过最大录制时长

    Args:
        max_duration_seconds: 最大录制时长（秒）

    Returns:
        True 如果超过最大时长
    """
    global _recording_start_time
    if _recording_start_time is None:
        return False

    elapsed = (datetime.now() - _recording_start_time).total_seconds()
    return elapsed >= max_duration_seconds


def start_recording(
    sample_rate: int = 16000,
    channels: int = 1,
    max_duration_seconds: int = DEFAULT_MAX_DURATION_SECONDS
) -> bool:
    """
    开始音频录制

    Args:
        sample_rate: 采样率（Hz），默认 16000
        channels: 声道数，默认 1（单声道）
        max_duration_seconds: 最大录制时长（秒）

    Returns:
        True 如果录制成功开始

    Raises:
        RuntimeError: 如果已经在录制中
        OSError: 如果没有可用的麦克风

    TODO:
        - 实现实际的音频捕获（使用 sounddevice 或 pyaudio）
        - 实现分段保存机制
        - 实现最大时长自动停止
    """
    global _is_recording, _recording_start_time

    with _recording_lock:
        if _is_recording:
            raise RuntimeError("录制已在进行中")

        # TODO: 检查麦克风可用性
        # 需要导入音频库（sounddevice 或 pyaudio）
        # import sounddevice as sd
        # devices = sd.query_devices()
        # if not any(device['max_input_channels'] > 0 for device in devices):
        #     raise OSError("没有可用的麦克风")

        _is_recording = True
        _recording_start_time = datetime.now()

        # TODO: 启动音频录制线程
        # def _record_audio():
        #     output_path = _ensure_data_dir() / _generate_recording_filename()
        #     with sd.OutputStream(samplerate=sample_rate, channels=channels) as stream:
        #         while _is_recording:
        #             if _check_max_duration(max_duration_seconds):
        #                 stop_recording()
        #                 break
        #             # 读取音频数据并写入文件
        #             ...
        #
        # thread = threading.Thread(target=_record_audio, daemon=True)
        # thread.start()

        return True


def stop_recording() -> Optional[MeetingInputResult]:
    """
    停止音频录制并保存

    Returns:
        MeetingInputResult: 包含录制的音频文件路径
        如果没有正在进行的录制，返回 None

    TODO:
        - 实现实际的停止逻辑
        - 返回正确的文件路径
    """
    global _is_recording, _recording_start_time

    with _recording_lock:
        if not _is_recording:
            return None

        _is_recording = False

        # TODO: 停止音频捕获并保存文件
        # output_path = _ensure_data_dir() / _generate_recording_filename()
        # ... 保存音频数据 ...

        # 占位符：创建一个空文件作为占位符（Phase 1 仅用于测试）
        output_path = _ensure_data_dir() / _generate_recording_filename()
        output_path.touch()  # 创建空文件

        return MeetingInputResult(
            audio_path=str(output_path.absolute()),
            video_path=None
        )


def is_recording() -> bool:
    """
    检查是否正在录制

    Returns:
        True 如果正在录制
    """
    with _recording_lock:
        return _is_recording


def get_recording_duration() -> Optional[float]:
    """
    获取当前录制时长（秒）

    Returns:
        录制时长（秒），如果没有正在录制则返回 None
    """
    global _recording_start_time

    with _recording_lock:
        if not _is_recording or _recording_start_time is None:
            return None

        elapsed = (datetime.now() - _recording_start_time).total_seconds()
        return elapsed


def get_max_duration_seconds() -> int:
    """获取默认最大录制时长（秒）"""
    return DEFAULT_MAX_DURATION_SECONDS
