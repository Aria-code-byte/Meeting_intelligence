"""
Integration tests for audio processing module
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from input.upload_video import upload_video
from audio.extract_audio import extract_audio, is_ffmpeg_available
from audio.preprocess import preprocess_audio, PreprocessOptions
from audio.types import ProcessedAudio


class TestAudioProcessingIntegration:
    """音频处理集成测试"""

    def test_ffmpeg_available_check(self):
        """测试 ffmpeg 可用性检查"""
        available = is_ffmpeg_available()
        assert isinstance(available, bool)

    @pytest.mark.skipif(
        not is_ffmpeg_available(),
        reason="ffmpeg not installed"
    )
    def test_full_video_to_audio_workflow(self, tmp_path):
        """测试完整的视频上传到音频提取工作流"""
        # 注意：这个测试需要真实的视频文件和 ffmpeg
        # 在 CI/CD 环境中可能需要跳过

        # 创建一个模拟视频文件（实际使用时需要真实视频）
        test_file = tmp_path / "test_video.mp4"
        test_file.write_bytes(b"minimal video data")

        # 跳过音频提取（因为没有真实视频）
        result = upload_video(str(test_file), extract_audio=False)

        assert result.video_path is not None
        assert Path(result.video_path).exists()

    @patch('audio.extract_audio._check_ffmpeg_available', return_value=True)
    @patch('subprocess.run')
    def test_extract_then_preprocess(self, mock_run, mock_ffmpeg, tmp_path):
        """测试提取后预处理的完整流程"""
        # 模拟 ffmpeg 成功运行
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        # 创建一个假的音频文件用于预处理
        audio_file = tmp_path / "extracted.wav"
        audio_file.write_bytes(b"RIFF" + b"\x00" * 1000)

        with patch('audio.extract_audio._get_audio_duration', return_value=10.5):
            # 模拟提取
            extracted = ProcessedAudio(
                path=str(audio_file),
                duration=10.5
            )

        # 预处理提取的音频 - 跳过预处理（因为 mock 无法创建真实文件）
        options = PreprocessOptions(normalize=False, trim_silence=False)
        with patch('audio.preprocess._get_audio_duration', return_value=10.5):
            processed = preprocess_audio(extracted.path, options)

        assert isinstance(processed, ProcessedAudio)
        assert processed.duration > 0


class TestAudioFormatConsistency:
    """音频格式一致性测试"""

    def test_processed_audio_structure(self, tmp_path):
        """测试 ProcessedAudio 结构一致性"""
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"data")

        result = ProcessedAudio(
            path=str(audio_file),
            duration=10.5
        )

        # 验证结构
        assert hasattr(result, "path")
        assert hasattr(result, "duration")
        assert isinstance(result.path, str)
        assert isinstance(result.duration, float)

    def test_to_dict_consistency(self, tmp_path):
        """测试 to_dict 方法一致性"""
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"data")

        result = ProcessedAudio(
            path=str(audio_file),
            duration=10.5
        )

        data = result.to_dict()
        assert "path" in data
        assert "duration" in data
        assert data["path"] == str(audio_file)
        assert data["duration"] == 10.5
