"""
Unit tests for audio upload module
"""

import pytest
import tempfile
from pathlib import Path

from input.upload_audio import upload_audio, get_supported_formats, get_max_file_size_mb
from input.types import MeetingInputResult


class TestAudioUpload:
    """音频上传功能测试"""

    def test_supported_formats(self):
        """测试支持的格式"""
        formats = get_supported_formats()
        assert ".mp3" in formats
        assert ".wav" in formats
        assert ".m4a" in formats

    def test_max_file_size(self):
        """测试最大文件大小配置"""
        assert get_max_file_size_mb() == 500

    def test_upload_valid_mp3(self, tmp_path):
        """测试上传有效的 MP3 文件"""
        # 创建临时测试文件
        test_file = tmp_path / "test_audio.mp3"
        test_file.write_bytes(b"fake mp3 data")

        result = upload_audio(str(test_file))

        assert isinstance(result, MeetingInputResult)
        assert result.audio_path is not None
        assert result.video_path is None
        assert Path(result.audio_path).exists()

    def test_upload_valid_wav(self, tmp_path):
        """测试上传有效的 WAV 文件"""
        test_file = tmp_path / "test_audio.wav"
        test_file.write_bytes(b"fake wav data")

        result = upload_audio(str(test_file))

        assert isinstance(result, MeetingInputResult)
        assert result.audio_path is not None
        assert result.video_path is None

    def test_upload_valid_m4a(self, tmp_path):
        """测试上传有效的 M4A 文件"""
        test_file = tmp_path / "test_audio.m4a"
        test_file.write_bytes(b"fake m4a data")

        result = upload_audio(str(test_file))

        assert isinstance(result, MeetingInputResult)
        assert result.audio_path is not None

    def test_upload_invalid_format(self, tmp_path):
        """测试上传不支持的格式"""
        test_file = tmp_path / "test_audio.ogg"
        test_file.write_bytes(b"fake ogg data")

        with pytest.raises(ValueError, match="不支持的音频格式"):
            upload_audio(str(test_file))

    def test_upload_nonexistent_file(self):
        """测试上传不存在的文件"""
        with pytest.raises(FileNotFoundError):
            upload_audio("/nonexistent/file.mp3")

    def test_upload_custom_size_limit(self, tmp_path):
        """测试自定义大小限制"""
        test_file = tmp_path / "test_audio.mp3"
        test_file.write_bytes(b"x" * 1000)  # 1KB 文件

        # 设置极小限制（1 byte）
        with pytest.raises(ValueError, match="文件过大"):
            upload_audio(str(test_file), max_size_mb=0.000001)


class TestMeetingInputResult:
    """MeetingInputResult 数据类测试"""

    def test_to_dict(self, tmp_path):
        """测试转换为字典"""
        # 创建实际的临时文件
        audio_file = tmp_path / "audio.mp3"
        video_file = tmp_path / "video.mp4"
        audio_file.write_bytes(b"fake audio")
        video_file.write_bytes(b"fake video")

        result = MeetingInputResult(
            audio_path=str(audio_file),
            video_path=str(video_file)
        )
        data = result.to_dict()
        assert data["audio_path"] == str(audio_file)
        assert data["video_path"] == str(video_file)

    def test_to_dict_with_null_video(self, tmp_path):
        """测试视频路径为 None 时转换为字典"""
        # 创建实际的临时文件
        audio_file = tmp_path / "audio.mp3"
        audio_file.write_bytes(b"fake audio")

        result = MeetingInputResult(audio_path=str(audio_file))
        data = result.to_dict()
        assert data["audio_path"] == str(audio_file)
        assert data["video_path"] is None
