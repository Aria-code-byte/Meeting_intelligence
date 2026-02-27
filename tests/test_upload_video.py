"""
Unit tests for video upload module
"""

import pytest
import tempfile
from pathlib import Path

from input.upload_video import upload_video, get_supported_formats, get_max_file_size_mb
from input.types import MeetingInputResult


class TestVideoUpload:
    """视频上传功能测试"""

    def test_supported_formats(self):
        """测试支持的格式"""
        formats = get_supported_formats()
        assert ".mp4" in formats
        assert ".mkv" in formats
        assert ".mov" in formats

    def test_max_file_size(self):
        """测试最大文件大小配置"""
        assert get_max_file_size_mb() == 2048  # 2GB

    def test_upload_valid_mp4(self, tmp_path):
        """测试上传有效的 MP4 文件"""
        test_file = tmp_path / "test_video.mp4"
        test_file.write_bytes(b"fake mp4 data")

        # 跳过音频提取（因为 ffmpeg 可能未安装）
        result = upload_video(str(test_file), extract_audio=False)

        assert isinstance(result, MeetingInputResult)
        assert result.video_path is not None
        assert Path(result.video_path).exists()
        # 跳过音频提取时，audio_path 应该是 None
        assert result.audio_path is None

    def test_upload_valid_mk(self, tmp_path):
        """测试上传有效的 MKV 文件"""
        test_file = tmp_path / "test_video.mkv"
        test_file.write_bytes(b"fake mkv data")

        result = upload_video(str(test_file), extract_audio=False)

        assert isinstance(result, MeetingInputResult)
        assert result.video_path is not None

    def test_upload_valid_mov(self, tmp_path):
        """测试上传有效的 MOV 文件"""
        test_file = tmp_path / "test_video.mov"
        test_file.write_bytes(b"fake mov data")

        result = upload_video(str(test_file), extract_audio=False)

        assert isinstance(result, MeetingInputResult)
        assert result.video_path is not None

    def test_upload_invalid_format(self, tmp_path):
        """测试上传不支持的格式"""
        test_file = tmp_path / "test_video.avi"
        test_file.write_bytes(b"fake avi data")

        with pytest.raises(ValueError, match="不支持的视频格式"):
            upload_video(str(test_file))

    def test_upload_nonexistent_file(self):
        """测试上传不存在的文件"""
        with pytest.raises(FileNotFoundError):
            upload_video("/nonexistent/file.mp4")

    def test_upload_custom_size_limit(self, tmp_path):
        """测试自定义大小限制"""
        test_file = tmp_path / "test_video.mp4"
        test_file.write_bytes(b"x" * 1000)  # 1KB 文件

        # 设置极小限制（1 byte）
        with pytest.raises(ValueError, match="文件过大"):
            upload_video(str(test_file), max_size_mb=0.000001)

    def test_video_file_preserved(self, tmp_path):
        """测试视频文件被保留（用于 V2 PPT 分析）"""
        test_file = tmp_path / "test_video.mp4"
        test_file.write_bytes(b"fake mp4 data")

        result = upload_video(str(test_file), extract_audio=False)

        # 验证原始视频文件被保存
        assert result.video_path is not None
        saved_video = Path(result.video_path)
        assert saved_video.exists()
        assert saved_video.suffix == ".mp4"


class TestVideoUploadAudioExtraction:
    """视频上传音频提取集成测试"""

    def test_upload_without_audio_extraction(self, tmp_path):
        """测试禁用音频提取"""
        test_file = tmp_path / "test_video.mp4"
        test_file.write_bytes(b"fake mp4 data")

        result = upload_video(str(test_file), extract_audio=False)

        assert isinstance(result, MeetingInputResult)
        assert result.video_path is not None
        assert result.audio_path is None  # 跳过提取

    def test_upload_with_audio_extraction_no_ffmpeg(self, tmp_path):
        """测试启用音频提取但 ffmpeg 未安装"""
        test_file = tmp_path / "test_video.mp4"
        test_file.write_bytes(b"fake mp4 data")

        # 如果 ffmpeg 未安装，应该抛出 RuntimeError
        try:
            result = upload_video(str(test_file), extract_audio=True)
            # 如果 ffmpeg 已安装，audio_path 应该存在
            assert result.audio_path is not None
        except RuntimeError as e:
            # ffmpeg 未安装时的预期行为
            assert "ffmpeg" in str(e).lower() or "提取失败" in str(e)
