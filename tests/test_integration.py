"""
Integration tests for the meeting input module

验证所有输入方法返回一致的 MeetingInputResult 结构
"""

import pytest
import tempfile
from pathlib import Path

from input.upload_audio import upload_audio
from input.upload_video import upload_video
from input.record_audio import start_recording, stop_recording, is_recording
from input.types import MeetingInputResult


class TestUnifiedInterface:
    """统一接口集成测试"""

    def test_audio_upload_returns_consistent_structure(self, tmp_path):
        """测试音频上传返回一致的结构"""
        test_file = tmp_path / "test_audio.mp3"
        test_file.write_bytes(b"fake mp3 data")

        result = upload_audio(str(test_file))

        # 验证返回类型
        assert isinstance(result, MeetingInputResult)

        # 验证必填字段
        assert hasattr(result, "audio_path")
        assert hasattr(result, "video_path")

        # 验证字段类型
        assert isinstance(result.audio_path, str)
        assert result.video_path is None or isinstance(result.video_path, str)

        # 验证音频路径存在
        assert Path(result.audio_path).exists()

    def test_video_upload_returns_consistent_structure(self, tmp_path):
        """测试视频上传返回一致的结构"""
        test_file = tmp_path / "test_video.mp4"
        test_file.write_bytes(b"fake mp4 data")

        result = upload_video(str(test_file), extract_audio=False)

        # 验证返回类型
        assert isinstance(result, MeetingInputResult)

        # 验证字段
        assert result.audio_path is None  # 跳过音频提取
        assert result.video_path is not None
        assert Path(result.video_path).exists()

    def test_recording_returns_consistent_structure(self):
        """测试录音返回一致的结构"""
        # 确保没有正在进行的录制
        if is_recording():
            stop_recording()

        start_recording()
        result = stop_recording()

        # 验证返回类型
        assert isinstance(result, MeetingInputResult)

        # 验证字段
        assert result.audio_path is not None
        assert result.video_path is None

    def test_all_methods_return_same_type(self, tmp_path):
        """测试所有方法返回相同类型"""
        # 音频上传
        audio_file = tmp_path / "test_audio.mp3"
        audio_file.write_bytes(b"fake mp3 data")
        audio_result = upload_audio(str(audio_file))

        # 视频上传（跳过音频提取）
        video_file = tmp_path / "test_video.mp4"
        video_file.write_bytes(b"fake mp4 data")
        video_result = upload_video(str(video_file), extract_audio=False)

        # 录音
        if is_recording():
            stop_recording()
        start_recording()
        recording_result = stop_recording()

        # 验证所有结果都是 MeetingInputResult 类型
        assert type(audio_result) == type(video_result) == type(recording_result) == MeetingInputResult


class TestFilePathValidation:
    """文件路径验证集成测试"""

    def test_audio_upload_file_path_exists(self, tmp_path):
        """测试音频上传文件路径有效性"""
        test_file = tmp_path / "test_audio.wav"
        test_file.write_bytes(b"fake wav data")

        result = upload_audio(str(test_file))

        # 验证文件存在
        assert Path(result.audio_path).exists()

        # 验证文件可读
        assert Path(result.audio_path).stat().st_size > 0

    def test_video_upload_file_path_exists(self, tmp_path):
        """测试视频上传文件路径有效性"""
        test_file = tmp_path / "test_video.mkv"
        test_file.write_bytes(b"fake mkv data")

        result = upload_video(str(test_file), extract_audio=False)

        # 验证视频文件存在
        assert Path(result.video_path).exists()
        assert Path(result.video_path).stat().st_size > 0

    def test_recording_file_path_format(self):
        """测试录音文件路径格式"""
        if is_recording():
            stop_recording()

        start_recording()
        result = stop_recording()

        # 验证文件扩展名
        assert result.audio_path.endswith(".wav")


class TestErrorHandling:
    """错误处理集成测试"""

    def test_audio_upload_error_messages(self, tmp_path):
        """测试音频上传错误消息"""
        # 不支持的格式
        invalid_file = tmp_path / "test.ogg"
        invalid_file.write_bytes(b"data")
        with pytest.raises(ValueError) as exc_info:
            upload_audio(str(invalid_file))
        assert "不支持的音频格式" in str(exc_info.value)

        # 不存在的文件
        with pytest.raises(FileNotFoundError):
            upload_audio("/nonexistent/path.mp3")

    def test_video_upload_error_messages(self, tmp_path):
        """测试视频上传错误消息"""
        # 不支持的格式
        invalid_file = tmp_path / "test.avi"
        invalid_file.write_bytes(b"data")
        with pytest.raises(ValueError) as exc_info:
            upload_video(str(invalid_file))
        assert "不支持的视频格式" in str(exc_info.value)

        # 不存在的文件
        with pytest.raises(FileNotFoundError):
            upload_video("/nonexistent/path.mp4")

    def test_recording_error_messages(self):
        """测试录音错误消息"""
        # 重复开始录制
        if is_recording():
            stop_recording()

        start_recording()
        with pytest.raises(RuntimeError) as exc_info:
            start_recording()
        assert "录制已在进行中" in str(exc_info.value)

        stop_recording()


class TestEndToEndWorkflows:
    """端到端工作流测试"""

    def test_audio_upload_workflow(self, tmp_path):
        """测试完整的音频上传工作流"""
        # 创建测试文件
        test_file = tmp_path / "meeting.mp3"
        test_file.write_bytes(b"meeting audio data")

        # 上传
        result = upload_audio(str(test_file))

        # 验证结果
        assert result.audio_path is not None
        assert Path(result.audio_path).exists()
        assert result.video_path is None

    def test_video_upload_workflow(self, tmp_path):
        """测试完整的视频上传工作流"""
        # 创建测试文件
        test_file = tmp_path / "meeting.mp4"
        test_file.write_bytes(b"meeting video data")

        # 上传（跳过音频提取，因为 ffmpeg 可能未安装）
        result = upload_video(str(test_file), extract_audio=False)

        # 验证结果
        assert result.video_path is not None
        assert Path(result.video_path).exists()
        assert result.audio_path is None  # 跳过提取

    def test_recording_workflow(self):
        """测试完整的录音工作流"""
        # 确保没有正在进行的录制
        if is_recording():
            stop_recording()

        # 开始录制
        assert start_recording() is True
        assert is_recording() is True

        # 停止录制
        result = stop_recording()
        assert result is not None
        assert result.audio_path is not None
        assert is_recording() is False
