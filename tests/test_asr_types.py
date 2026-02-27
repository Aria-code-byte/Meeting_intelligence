"""
Unit tests for ASR types module
"""

import pytest
import json
from pathlib import Path

from asr.types import Utterance, TranscriptionResult


class TestUtterance:
    """Utterance 数据类测试"""

    def test_utterance_creation(self):
        """测试创建有效的 Utterance"""
        utterance = Utterance(
            start=0.0,
            end=2.5,
            text="大家好"
        )

        assert utterance.start == 0.0
        assert utterance.end == 2.5
        assert utterance.text == "大家好"

    def test_utterance_to_dict(self):
        """测试转换为字典"""
        utterance = Utterance(
            start=1.0,
            end=3.5,
            text="测试文本"
        )

        data = utterance.to_dict()
        assert data["start"] == 1.0
        assert data["end"] == 3.5
        assert data["text"] == "测试文本"

    def test_utterance_negative_start(self):
        """测试负的开始时间"""
        with pytest.raises(ValueError, match="开始时间不能为负数"):
            Utterance(start=-1.0, end=2.0, text="test")

    def test_utterance_end_before_start(self):
        """测试结束时间小于开始时间"""
        with pytest.raises(ValueError, match="结束时间必须大于开始时间"):
            Utterance(start=5.0, end=2.0, text="test")

    def test_utterance_empty_text(self):
        """测试空文本"""
        with pytest.raises(ValueError, match="文本内容不能为空"):
            Utterance(start=0.0, end=2.0, text="")


class TestTranscriptionResult:
    """TranscriptionResult 数据类测试"""

    def test_transcription_result_creation(self, tmp_path):
        """测试创建有效的 TranscriptionResult"""
        # 创建音频和输出文件
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"RIFF" + b"\x00" * 1000)

        output_file = tmp_path / "transcript.json"
        output_file.write_bytes(b'{"utterances": [], "audio_path": "test.wav", "duration": 10.0, "asr_provider": "whisper", "timestamp": "2024-01-01"}')

        utterances = [
            Utterance(start=0.0, end=2.5, text="大家好"),
            Utterance(start=2.6, end=5.0, text="今天讨论项目")
        ]

        result = TranscriptionResult(
            utterances=utterances,
            audio_path=str(audio_file),
            duration=10.0,
            output_path=str(output_file),
            asr_provider="whisper",
            timestamp="2024-01-01T00:00:00"
        )

        assert len(result.utterances) == 2
        assert result.duration == 10.0
        assert result.asr_provider == "whisper"

    def test_transcription_result_to_dict(self, tmp_path):
        """测试转换为字典"""
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"data")

        output_file = tmp_path / "transcript.json"
        output_file.write_bytes(b'{}')

        utterances = [Utterance(start=0.0, end=2.5, text="test")]

        result = TranscriptionResult(
            utterances=utterances,
            audio_path=str(audio_file),
            duration=10.0,
            output_path=str(output_file),
            asr_provider="whisper",
            timestamp="2024-01-01"
        )

        data = result.to_dict()
        assert "utterances" in data
        assert "audio_path" in data
        assert "duration" in data

    def test_transcription_result_nonexistent_audio(self, tmp_path):
        """测试音频文件不存在"""
        output_file = tmp_path / "transcript.json"
        output_file.write_bytes(b'{}')

        with pytest.raises(FileNotFoundError, match="音频文件不存在"):
            TranscriptionResult(
                utterances=[],
                audio_path="/nonexistent/audio.wav",
                duration=10.0,
                output_path=str(output_file),
                asr_provider="whisper",
                timestamp="2024-01-01"
            )

    def test_transcription_result_invalid_duration(self, tmp_path):
        """测试无效时长"""
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"data")

        output_file = tmp_path / "transcript.json"
        output_file.write_bytes(b'{}')

        with pytest.raises(ValueError, match="音频时长必须大于 0"):
            TranscriptionResult(
                utterances=[],
                audio_path=str(audio_file),
                duration=0.0,
                output_path=str(output_file),
                asr_provider="whisper",
                timestamp="2024-01-01"
            )

    def test_transcription_result_non_monotonic_timestamps(self, tmp_path):
        """测试非单调时间戳"""
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"data")

        output_file = tmp_path / "transcript.json"
        output_file.write_bytes(b'{}')

        utterances = [
            Utterance(start=5.0, end=7.0, text="second"),
            Utterance(start=1.0, end=3.0, text="first")  # 时间戳倒退
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

    def test_get_full_text(self, tmp_path):
        """测试获取完整文本"""
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"data")

        output_file = tmp_path / "transcript.json"
        output_file.write_bytes(b'{}')

        utterances = [
            Utterance(start=0.0, end=2.5, text="大家好，"),
            Utterance(start=2.6, end=5.0, text="今天讨论项目")
        ]

        result = TranscriptionResult(
            utterances=utterances,
            audio_path=str(audio_file),
            duration=10.0,
            output_path=str(output_file),
            asr_provider="whisper",
            timestamp="2024-01-01"
        )

        full_text = result.get_full_text()
        assert full_text == "大家好，今天讨论项目"

    def test_transcription_result_enhanced_path_optional(self, tmp_path):
        """测试 enhanced_transcript_path 是可选字段"""
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"data")

        output_file = tmp_path / "transcript.json"
        output_file.write_bytes(b'{}')

        utterances = [Utterance(start=0.0, end=2.5, text="test")]

        result = TranscriptionResult(
            utterances=utterances,
            audio_path=str(audio_file),
            duration=10.0,
            output_path=str(output_file),
            asr_provider="whisper",
            timestamp="2024-01-01"
        )

        # 默认情况下 enhanced_transcript_path 为 None
        assert result.enhanced_transcript_path is None

    def test_transcription_result_to_dict_includes_enhanced(self, tmp_path):
        """测试 to_dict 包含 enhanced_transcript_path（如果存在）"""
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"data")

        output_file = tmp_path / "transcript.json"
        output_file.write_bytes(b'{}')

        utterances = [Utterance(start=0.0, end=2.5, text="test")]

        result = TranscriptionResult(
            utterances=utterances,
            audio_path=str(audio_file),
            duration=10.0,
            output_path=str(output_file),
            asr_provider="whisper",
            timestamp="2024-01-01",
            enhanced_transcript_path="/path/to/enhanced.json"
        )

        data = result.to_dict()
        assert "enhanced_transcript_path" in data
        assert data["enhanced_transcript_path"] == "/path/to/enhanced.json"

    def test_transcription_result_to_dict_excludes_enhanced_when_none(self, tmp_path):
        """测试 enhanced_transcript_path 为 None 时不出现在字典中"""
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"data")

        output_file = tmp_path / "transcript.json"
        output_file.write_bytes(b'{}')

        utterances = [Utterance(start=0.0, end=2.5, text="test")]

        result = TranscriptionResult(
            utterances=utterances,
            audio_path=str(audio_file),
            duration=10.0,
            output_path=str(output_file),
            asr_provider="whisper",
            timestamp="2024-01-01"
        )

        data = result.to_dict()
        assert "enhanced_transcript_path" not in data
