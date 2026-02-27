"""
Unit tests for audio extraction module
"""

import pytest
import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock

from audio.extract_audio import (
    extract_audio,
    is_ffmpeg_available,
    _check_ffmpeg_available
)
from audio.types import ProcessedAudio


class TestFFmpegAvailability:
    """ffmpeg 可用性测试"""

    def test_is_ffmpeg_available(self):
        """测试 ffmpeg 可用性检查"""
        # 测试应该能运行（ffmpeg 可能未安装）
        result = is_ffmpeg_available()
        assert isinstance(result, bool)

    def test_check_ffmpeg_available_when_not_installed(self):
        """测试 ffmpeg 未安装时的行为"""
        with patch('subprocess.run', side_effect=FileNotFoundError):
            result = _check_ffmpeg_available()
            assert result is False


class TestAudioExtraction:
    """音频提取功能测试"""

    def test_extract_nonexistent_file(self):
        """测试提取不存在的文件"""
        with pytest.raises(FileNotFoundError):
            extract_audio("/nonexistent/video.mp4")

    @patch('audio.extract_audio._check_ffmpeg_available', return_value=False)
    def test_extract_without_ffmpeg(self, mock_ffmpeg, tmp_path):
        """测试没有 ffmpeg 时的错误处理"""
        # 创建一个虚假的视频文件
        video_file = tmp_path / "fake_video.mp4"
        video_file.write_bytes(b"fake data")

        with pytest.raises(RuntimeError, match="ffmpeg 未安装"):
            extract_audio(str(video_file))

    @patch('audio.extract_audio._check_ffmpeg_available', return_value=True)
    @patch('subprocess.run')
    def test_extract_success(self, mock_run, mock_ffmpeg, tmp_path):
        """测试成功的音频提取"""
        # 创建一个虚假的视频文件
        video_file = tmp_path / "test_video.mp4"
        video_file.write_bytes(b"fake video data")

        # 模拟 ffmpeg 成功运行
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        # 模拟 _get_audio_duration 返回值，并创建假的输出文件
        with patch('audio.extract_audio._get_audio_duration', return_value=10.5):
            # 创建假的输出文件（模拟 ffmpeg 输出）
            from input.upload_audio import DATA_DIR
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            fake_output = DATA_DIR / "extracted_test.wav"
            fake_output.write_bytes(b"RIFF" + b"\x00" * 1000)

            # Mock _get_output_path to return our fake file
            with patch('audio.extract_audio._get_output_path', return_value=fake_output):
                result = extract_audio(str(video_file))

        assert isinstance(result, ProcessedAudio)
        assert result.duration == 10.5
        assert result.path.endswith(".wav")

    @patch('audio.extract_audio._check_ffmpeg_available', return_value=True)
    @patch('subprocess.run')
    def test_extract_no_audio_track(self, mock_run, mock_ffmpeg, tmp_path):
        """测试视频没有音轨的情况"""
        video_file = tmp_path / "test_video.mp4"
        video_file.write_bytes(b"fake video data")

        # 模拟 ffmpeg 检测到没有音轨
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "Audio: not found"
        mock_run.return_value = mock_result

        # 抛出 RuntimeError（因为 ValueError 被重新抛出）
        with pytest.raises(RuntimeError, match="音频提取失败"):
            extract_audio(str(video_file))

    @patch('audio.extract_audio._check_ffmpeg_available', return_value=True)
    @patch('subprocess.run')
    def test_extract_corrupted_file(self, mock_run, mock_ffmpeg, tmp_path):
        """测试损坏的视频文件"""
        video_file = tmp_path / "test_video.mp4"
        video_file.write_bytes(b"corrupted data")

        # 模拟 ffmpeg 处理损坏文件
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "Invalid data"
        mock_run.return_value = mock_result

        with pytest.raises(RuntimeError, match="提取失败"):
            extract_audio(str(video_file))


class TestProcessedAudio:
    """ProcessedAudio 数据类测试"""

    def test_processed_audio_validation(self, tmp_path):
        """测试 ProcessedAudio 验证"""
        # 创建真实的音频文件（空文件作为占位符）
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"RIFF" + b"\x00" * 100)

        result = ProcessedAudio(
            path=str(audio_file),
            duration=10.5
        )

        assert result.path == str(audio_file)
        assert result.duration == 10.5

    def test_processed_audio_nonexistent_file(self):
        """测试不存在的文件"""
        with pytest.raises(FileNotFoundError):
            ProcessedAudio(
                path="/nonexistent/audio.wav",
                duration=10.5
            )

    def test_processed_audio_invalid_duration(self, tmp_path):
        """测试无效的时长"""
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"data")

        with pytest.raises(ValueError, match="时长必须大于 0"):
            ProcessedAudio(
                path=str(audio_file),
                duration=0
            )

        with pytest.raises(ValueError, match="时长必须大于 0"):
            ProcessedAudio(
                path=str(audio_file),
                duration=-1.0
            )

    def test_to_dict(self, tmp_path):
        """测试转换为字典"""
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"data")

        result = ProcessedAudio(
            path=str(audio_file),
            duration=10.5
        )

        data = result.to_dict()
        assert data["path"] == str(audio_file)
        assert data["duration"] == 10.5
