"""
Unit tests for audio preprocessing module
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from audio.preprocess import (
    preprocess_audio,
    PreprocessOptions
)
from audio.types import ProcessedAudio


class TestPreprocessOptions:
    """PreprocessOptions 数据类测试"""

    def test_default_options(self):
        """测试默认选项"""
        options = PreprocessOptions()
        assert options.normalize is True
        assert options.trim_silence is False
        assert options.silence_level == -50
        assert options.min_silence_duration == 0.5

    def test_custom_options(self):
        """测试自定义选项"""
        options = PreprocessOptions(
            normalize=False,
            trim_silence=True,
            silence_level=-40,
            min_silence_duration=1.0
        )
        assert options.normalize is False
        assert options.trim_silence is True
        assert options.silence_level == -40
        assert options.min_silence_duration == 1.0


class TestAudioPreprocessing:
    """音频预处理功能测试"""

    def test_preprocess_nonexistent_file(self):
        """测试处理不存在的文件"""
        with pytest.raises(FileNotFoundError):
            preprocess_audio("/nonexistent/audio.wav")

    def test_preprocess_skip_all(self, tmp_path):
        """测试跳过所有预处理"""
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"fake audio data")

        options = PreprocessOptions(normalize=False, trim_silence=False)

        with patch('audio.preprocess._get_audio_duration', return_value=10.5):
            result = preprocess_audio(str(audio_file), options)

        assert isinstance(result, ProcessedAudio)
        assert result.duration == 10.5

    @patch('subprocess.run')
    def test_preprocess_normalize_only(self, mock_run, tmp_path):
        """测试仅归一化"""
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"fake audio data")

        # 模拟 ffmpeg 成功运行
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        options = PreprocessOptions(normalize=True, trim_silence=False)

        # Mock the _normalize_audio to create a fake output file
        from input.upload_audio import DATA_DIR
        fake_output = DATA_DIR / "temp_test.wav"
        fake_output.write_bytes(b"RIFF" + b"\x00" * 1000)

        with patch('audio.preprocess._get_audio_duration', return_value=10.5):
            with patch('audio.preprocess._get_output_path', return_value=fake_output):
                result = preprocess_audio(str(audio_file), options)

        assert isinstance(result, ProcessedAudio)
        assert mock_run.call_count == 1  # 只调用一次（归一化）

    @patch('subprocess.run')
    def test_preprocess_normalize_and_trim(self, mock_run, tmp_path):
        """测试归一化 + 静音裁剪"""
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"fake audio data")

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        options = PreprocessOptions(normalize=True, trim_silence=True)

        # Create fake output files
        from input.upload_audio import DATA_DIR
        fake_temp = DATA_DIR / "temp_test.wav"
        fake_temp.write_bytes(b"RIFF" + b"\x00" * 1000)
        fake_output = DATA_DIR / "processed_test.wav"
        fake_output.write_bytes(b"RIFF" + b"\x00" * 1000)

        with patch('audio.preprocess._get_audio_duration', return_value=10.5):
            with patch('audio.preprocess._get_output_path', side_effect=[fake_temp, fake_output]):
                result = preprocess_audio(str(audio_file), options)

        assert isinstance(result, ProcessedAudio)
        assert mock_run.call_count >= 1  # 至少调用一次

    @patch('subprocess.run')
    def test_preprocess_default_options(self, mock_run, tmp_path):
        """测试使用默认选项（仅归一化）"""
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"fake audio data")

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        # Create fake output file
        from input.upload_audio import DATA_DIR
        fake_output = DATA_DIR / "temp_test2.wav"
        fake_output.write_bytes(b"RIFF" + b"\x00" * 1000)

        # 不传 options，使用默认值
        with patch('audio.preprocess._get_audio_duration', return_value=10.5):
            with patch('audio.preprocess._get_output_path', return_value=fake_output):
                result = preprocess_audio(str(audio_file))

        assert isinstance(result, ProcessedAudio)
        # 默认是归一化，所以应该调用 ffmpeg
        assert mock_run.call_count >= 1

    @patch('subprocess.run')
    def test_preprocess_ffmpeg_error(self, mock_run, tmp_path):
        """测试 ffmpeg 错误处理"""
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"fake audio data")

        # 模拟 ffmpeg 失败
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "FFmpeg error"
        mock_run.return_value = mock_result

        options = PreprocessOptions(normalize=True, trim_silence=False)

        with pytest.raises(RuntimeError, match="归一化失败"):
            preprocess_audio(str(audio_file), options)
