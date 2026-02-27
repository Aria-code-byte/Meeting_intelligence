"""
Integration tests for ASR module
"""

import pytest
import json
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open

from asr.transcribe import transcribe
from asr.types import TranscriptionResult, Utterance
from asr.providers.whisper import WhisperProvider


class TestASRIntegration:
    """ASR 集成测试"""

    @patch('asr.providers.whisper.WhisperProvider._check_local_whisper', return_value=False)
    def test_whisper_not_available(self, mock_check, tmp_path):
        """测试 Whisper 未安装时的行为"""
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"RIFF" + b"\x00" * 1000)

        provider = WhisperProvider()

        with pytest.raises(RuntimeError, match="本地 Whisper 未安装"):
            provider.transcribe(str(audio_file))

    def test_full_transcription_flow(self, tmp_path):
        """测试完整的转写流程（使用 mock transcribe_local）"""
        # 创建音频文件
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"RIFF" + b"\x00" * 1000)

        # 直接 mock _transcribe_local 方法
        with patch.object(WhisperProvider, '_transcribe_local') as mock_transcribe:
            mock_transcribe.return_value = [
                Utterance(start=0.0, end=2.5, text="大家好"),
                Utterance(start=2.6, end=5.0, text="今天讨论项目")
            ]

            provider = WhisperProvider()
            utterances = provider.transcribe(str(audio_file))

            assert len(utterances) == 2
            assert utterances[0].text == "大家好"
            assert utterances[1].text == "今天讨论项目"


class TestTimestampAccuracy:
    """时间戳准确性测试"""

    def test_timestamp_monotonicity(self, tmp_path):
        """测试时间戳单调性"""
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"data")

        output_file = tmp_path / "transcript.json"
        output_file.write_bytes(b'{}')

        # 非单调时间戳
        utterances = [
            Utterance(start=0.0, end=2.5, text="first"),
            Utterance(start=5.0, end=7.0, text="third"),
            Utterance(start=3.0, end=4.5, text="second")  # 违反单调性
        ]

        with pytest.raises(ValueError, match="时间戳不单调"):
            TranscriptionResult(
                utterances=utterances,
                audio_path=str(audio_file),
                duration=10.0,
                output_path=str(output_file),
                asr_provider="whisper",
                timestamp="2024-01-01"
            )

    def test_timestamp_within_duration(self, tmp_path):
        """测试时间戳在音频时长内"""
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"data")

        output_file = tmp_path / "transcript.json"
        output_file.write_bytes(b'{}')

        # 超出音频时长
        utterances = [
            Utterance(start=0.0, end=15.0, text="beyond duration")
        ]

        with pytest.raises(ValueError, match="utterance 时间超出音频时长"):
            TranscriptionResult(
                utterances=utterances,
                audio_path=str(audio_file),
                duration=10.0,
                output_path=str(output_file),
                asr_provider="whisper",
                timestamp="2024-01-01"
            )

    def test_valid_timestamps(self, tmp_path):
        """测试有效的时间戳"""
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"data")

        output_file = tmp_path / "transcript.json"
        output_file.write_bytes(b'{}')

        # 有效时间戳
        utterances = [
            Utterance(start=0.0, end=2.5, text="first"),
            Utterance(start=2.5, end=5.0, text="second"),
            Utterance(start=5.0, end=10.0, text="third")
        ]

        result = TranscriptionResult(
            utterances=utterances,
            audio_path=str(audio_file),
            duration=10.0,
            output_path=str(output_file),
            asr_provider="whisper",
            timestamp="2024-01-01"
        )

        assert len(result.utterances) == 3
        assert result.utterances[0].start == 0.0
        assert result.utterances[-1].end == 10.0


class TestResultPersistence:
    """结果持久化测试"""

    def test_json_result_format(self, tmp_path):
        """测试 JSON 结果格式"""
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"data")

        utterances = [
            Utterance(start=0.0, end=2.5, text="大家好")
        ]

        # 保存结果
        from asr.transcribe import _save_result

        output_path = _save_result(
            utterances=utterances,
            audio_path=str(audio_file),
            duration=10.0,
            asr_provider="whisper"
        )

        # 验证文件存在
        assert Path(output_path).exists()

        # 验证 JSON 格式
        with open(output_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert "utterances" in data
        assert "audio_path" in data
        assert "duration" in data
        assert "asr_provider" in data
        assert "timestamp" in data

        # 验证 utterances 格式
        assert len(data["utterances"]) == 1
        assert data["utterances"][0]["start"] == 0.0
        assert data["utterances"][0]["end"] == 2.5
        assert data["utterances"][0]["text"] == "大家好"
