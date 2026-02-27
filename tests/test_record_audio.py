"""
Unit tests for audio recording module
"""

import pytest
import time
from pathlib import Path

from input.record_audio import (
    start_recording,
    stop_recording,
    is_recording,
    get_recording_duration,
    get_max_duration_seconds
)
from input.types import MeetingInputResult


class TestAudioRecording:
    """音频录制功能测试"""

    def test_max_duration_setting(self):
        """测试最大录制时长设置"""
        assert get_max_duration_seconds() == 2 * 60 * 60  # 2小时

    def test_is_recording_initial_state(self):
        """测试初始状态：未在录制"""
        # 确保没有正在进行的录制
        if is_recording():
            stop_recording()
        assert is_recording() is False

    def test_get_recording_duration_when_not_recording(self):
        """测试未录制时获取时长"""
        # 确保没有正在进行的录制
        if is_recording():
            stop_recording()
        assert get_recording_duration() is None

    def test_start_recording_success(self):
        """测试成功开始录制"""
        # 确保没有正在进行的录制
        if is_recording():
            stop_recording()

        result = start_recording()
        assert result is True
        assert is_recording() is True

        # 清理：停止录制
        stop_recording()

    def test_start_recording_when_already_recording(self):
        """测试已在录制时再次开始"""
        # 确保没有正在进行的录制
        if is_recording():
            stop_recording()

        # 开始第一次录制
        start_recording()

        # 尝试再次开始（应该抛出异常）
        with pytest.raises(RuntimeError, match="录制已在进行中"):
            start_recording()

        # 清理
        stop_recording()

    def test_stop_recording_when_not_recording(self):
        """测试未录制时停止"""
        # 确保没有正在进行的录制
        if is_recording():
            stop_recording()

        result = stop_recording()
        assert result is None

    def test_start_stop_recording_flow(self):
        """测试完整的开始-停止录制流程"""
        # 确保没有正在进行的录制
        if is_recording():
            stop_recording()

        # 开始录制
        start_recording()
        assert is_recording() is True

        # 停止录制
        result = stop_recording()
        assert isinstance(result, MeetingInputResult)
        assert result.audio_path is not None
        assert result.video_path is None

        # 确认已停止
        assert is_recording() is False

    def test_recording_duration_increases(self):
        """测试录制时长递增"""
        # 确保没有正在进行的录制
        if is_recording():
            stop_recording()

        start_recording()
        time.sleep(0.1)  # 等待 100ms

        duration = get_recording_duration()
        assert duration is not None
        assert duration >= 0.1

        stop_recording()

    def test_stop_returns_meeting_input_result(self):
        """测试停止录制返回 MeetingInputResult"""
        # 确保没有正在进行的录制
        if is_recording():
            stop_recording()

        start_recording()
        result = stop_recording()

        assert isinstance(result, MeetingInputResult)
        assert result.audio_path is not None
        # 音频路径应该指向 .wav 文件
        assert result.audio_path.endswith(".wav")
        assert result.video_path is None

    # TODO: 添加以下测试（需要实际的音频捕获实现）
    # def test_max_duration_auto_stop(self):
    #     """测试超过最大时长自动停止"""
    #     pass
    #
    # def test_microphone_unavailable(self):
    #     """测试麦克风不可用时的错误处理"""
    #     pass
    #
    # def test_segmented_saving(self):
    #     """测试分段保存机制"""
    #     pass
