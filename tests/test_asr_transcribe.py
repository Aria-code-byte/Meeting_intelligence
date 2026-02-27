"""
Unit tests for ASR transcribe module
"""

import pytest
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

from asr.transcribe import (
    transcribe,
    load_transcript,
    export_text,
    get_provider
)
from asr.types import Utterance, TranscriptionResult


class TestTranscribe:
    """transcribe 函数测试"""

    def test_transcribe_nonexistent_file(self):
        """测试转写不存在的文件"""
        with pytest.raises(FileNotFoundError):
            transcribe("/nonexistent/audio.wav")

    def test_transcribe_invalid_provider(self, tmp_path):
        """测试无效的提供商"""
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"RIFF" + b"\x00" * 1000)

        with pytest.raises(ValueError, match="不支持的 ASR 提供商"):
            transcribe(str(audio_file), provider="invalid_provider")

    @patch('asr.transcribe.WhisperProvider')
    @patch('audio.extract_audio._get_audio_duration', return_value=10.0)
    def test_transcribe_success(self, mock_duration, mock_provider_class, tmp_path):
        """测试成功的转写"""
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"RIFF" + b"\x00" * 1000)

        # Mock provider
        mock_provider = MagicMock()
        mock_provider.name = "whisper-base"
        mock_provider.transcribe.return_value = [
            Utterance(start=0.0, end=2.5, text="大家好"),
            Utterance(start=2.6, end=5.0, text="今天讨论项目")
        ]
        mock_provider_class.return_value = mock_provider

        result = transcribe(str(audio_file))

        assert isinstance(result, TranscriptionResult)
        assert len(result.utterances) == 2
        assert result.asr_provider == "whisper-base"
        assert result.duration == 10.0

        # 验证结果已保存
        assert Path(result.output_path).exists()

    @patch('asr.transcribe.WhisperProvider')
    @patch('audio.extract_audio._get_audio_duration', return_value=10.0)
    def test_transcribe_empty_result(self, mock_duration, mock_provider_class, tmp_path):
        """测试空转写结果（静音音频）"""
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"RIFF" + b"\x00" * 1000)

        mock_provider = MagicMock()
        mock_provider.name = "whisper-base"
        mock_provider.transcribe.return_value = []
        mock_provider_class.return_value = mock_provider

        result = transcribe(str(audio_file))

        assert isinstance(result, TranscriptionResult)
        assert len(result.utterances) == 0


class TestLoadTranscript:
    """load_transcript 函数测试"""

    def test_load_nonexistent_file(self):
        """测试加载不存在的文件"""
        with pytest.raises(FileNotFoundError):
            load_transcript("/nonexistent/transcript.json")

    def test_load_success(self, tmp_path):
        """测试成功加载转录结果"""
        # 创建 JSON 文件
        json_file = tmp_path / "transcript.json"
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"data")

        data = {
            "utterances": [
                {"start": 0.0, "end": 2.5, "text": "大家好"},
                {"start": 2.6, "end": 5.0, "text": "今天讨论项目"}
            ],
            "audio_path": str(audio_file),
            "duration": 10.0,
            "asr_provider": "whisper",
            "timestamp": "2024-01-01T00:00:00"
        }

        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(data, f)

        result = load_transcript(str(json_file))

        assert isinstance(result, TranscriptionResult)
        assert len(result.utterances) == 2
        assert result.duration == 10.0
        assert result.asr_provider == "whisper"


class TestExportText:
    """export_text 函数测试"""

    def test_export_text(self, tmp_path):
        """测试导出为纯文本"""
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"data")

        output_file = tmp_path / "transcript.json"
        output_file.write_bytes(b'{}')

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
            timestamp="2024-01-01"
        )

        text_file = tmp_path / "output.txt"
        export_text(result, str(text_file))

        # 验证文件内容
        content = text_file.read_text(encoding="utf-8")
        assert "[0.0-2.5] 大家好" in content
        assert "[2.6-5.0] 今天讨论项目" in content


class TestGetProvider:
    """get_provider 函数测试"""

    def test_get_whisper_provider(self):
        """测试获取 Whisper 提供商"""
        provider = get_provider("whisper")
        assert provider is not None
        assert hasattr(provider, "transcribe")

    def test_get_invalid_provider(self):
        """测试获取无效提供商"""
        with pytest.raises(ValueError, match="不支持的提供商"):
            get_provider("invalid")
