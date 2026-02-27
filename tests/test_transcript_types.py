"""
Tests for transcript module types.
"""

import pytest
from pathlib import Path
from datetime import datetime

from transcript.types import TranscriptDocument


class TestTranscriptDocument:
    """TranscriptDocument 类型测试"""

    def test_document_creation(self, tmp_path):
        """测试文档创建"""
        # 创建测试音频文件
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"RIFF" + b"\x00" * 1000)

        utterances = [
            {"start": 0.0, "end": 2.5, "text": "大家好"},
            {"start": 2.6, "end": 5.0, "text": "今天讨论项目"}
        ]

        document = TranscriptDocument(
            utterances=utterances,
            audio_path=str(audio_file),
            duration=10.0,
            asr_provider="whisper-local-base"
        )

        assert document.utterance_count == 2
        assert document.duration == 10.0
        assert document.asr_provider == "whisper-local-base"
        assert document.audio_path == str(audio_file)

    def test_document_nonexistent_audio(self, tmp_path):
        """测试音频文件不存在时抛出错误"""
        with pytest.raises(FileNotFoundError):
            TranscriptDocument(
                utterances=[],
                audio_path="/nonexistent/audio.wav",
                duration=10.0,
                asr_provider="whisper"
            )

    def test_document_invalid_duration(self, tmp_path):
        """测试无效时长时抛出错误"""
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"data")

        with pytest.raises(ValueError, match="时长必须大于 0"):
            TranscriptDocument(
                utterances=[],
                audio_path=str(audio_file),
                duration=0,
                asr_provider="whisper"
            )

    def test_utterance_validation_missing_field(self, tmp_path):
        """测试 utterance 缺少必需字段"""
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"data")

        utterances = [
            {"start": 0.0, "text": "缺少 end 字段"}
        ]

        with pytest.raises(ValueError, match="缺少字段"):
            TranscriptDocument(
                utterances=utterances,
                audio_path=str(audio_file),
                duration=10.0,
                asr_provider="whisper"
            )

    def test_utterance_negative_start(self, tmp_path):
        """测试负数开始时间"""
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"data")

        utterances = [
            {"start": -1.0, "end": 2.5, "text": "test"}
        ]

        with pytest.raises(ValueError, match="start 时间不能为负数"):
            TranscriptDocument(
                utterances=utterances,
                audio_path=str(audio_file),
                duration=10.0,
                asr_provider="whisper"
            )

    def test_utterance_end_before_start(self, tmp_path):
        """测试结束时间小于开始时间"""
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"data")

        utterances = [
            {"start": 5.0, "end": 2.5, "text": "test"}
        ]

        with pytest.raises(ValueError, match="end 时间必须大于 start 时间"):
            TranscriptDocument(
                utterances=utterances,
                audio_path=str(audio_file),
                duration=10.0,
                asr_provider="whisper"
            )

    def test_utterance_non_monotonic(self, tmp_path):
        """测试时间戳不单调"""
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"data")

        utterances = [
            {"start": 0.0, "end": 2.5, "text": "first"},
            {"start": 5.0, "end": 7.0, "text": "third"},
            {"start": 3.0, "end": 4.5, "text": "second"}
        ]

        with pytest.raises(ValueError, match="时间戳不单调"):
            TranscriptDocument(
                utterances=utterances,
                audio_path=str(audio_file),
                duration=10.0,
                asr_provider="whisper"
            )

    def test_to_dict(self, tmp_path):
        """测试转换为字典"""
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"data")

        utterances = [
            {"start": 0.0, "end": 2.5, "text": "test"}
        ]

        document = TranscriptDocument(
            utterances=utterances,
            audio_path=str(audio_file),
            duration=10.0,
            asr_provider="whisper-local-base",
            created_at="2024-01-01T00:00:00"
        )

        result = document.to_dict()

        assert "metadata" in result
        assert "utterances" in result
        assert result["metadata"]["audio_path"] == str(audio_file)
        assert result["metadata"]["duration"] == 10.0
        assert result["metadata"]["utterance_count"] == 1
        assert len(result["utterances"]) == 1

    def test_from_dict(self, tmp_path):
        """测试从字典创建"""
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"data")

        data = {
            "metadata": {
                "audio_path": str(audio_file),
                "duration": 10.0,
                "asr_provider": "whisper-local-base",
                "created_at": "2024-01-01T00:00:00"
            },
            "utterances": [
                {"start": 0.0, "end": 2.5, "text": "test"}
            ]
        }

        document = TranscriptDocument.from_dict(data)

        assert document.utterance_count == 1
        assert document.duration == 10.0
        assert document.asr_provider == "whisper-local-base"

    def test_from_dict_missing_metadata(self):
        """测试从字典创建时缺少 metadata"""
        data = {
            "utterances": []
        }

        with pytest.raises(ValueError, match="缺少 metadata"):
            TranscriptDocument.from_dict(data)

    def test_from_dict_missing_utterances(self):
        """测试从字典创建时缺少 utterances"""
        data = {
            "metadata": {"audio_path": "test.wav", "duration": 10.0, "asr_provider": "whisper"}
        }

        with pytest.raises(ValueError, match="缺少 utterances"):
            TranscriptDocument.from_dict(data)

    def test_save_and_load(self, tmp_path):
        """测试保存和加载"""
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"data")

        utterances = [
            {"start": 0.0, "end": 2.5, "text": "大家好"}
        ]

        document = TranscriptDocument(
            utterances=utterances,
            audio_path=str(audio_file),
            duration=10.0,
            asr_provider="whisper"
        )

        # 保存
        output_path = tmp_path / "transcript_test.json"
        saved_path = document.save(str(output_path))
        assert Path(saved_path).exists()

        # 验证文件内容
        import json
        with open(saved_path, "r", encoding="utf-8") as f:
            saved_data = json.load(f)

        assert saved_data["metadata"]["utterance_count"] == 1
        assert len(saved_data["utterances"]) == 1

    def test_get_full_text(self, tmp_path):
        """测试获取完整文字"""
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"data")

        utterances = [
            {"start": 0.0, "end": 2.5, "text": "大家好"},
            {"start": 2.6, "end": 5.0, "text": "今天讨论项目"}
        ]

        document = TranscriptDocument(
            utterances=utterances,
            audio_path=str(audio_file),
            duration=10.0,
            asr_provider="whisper"
        )

        full_text = document.get_full_text()
        assert full_text == "大家好 今天讨论项目"

    def test_get_utterances_after(self, tmp_path):
        """测试获取指定时间之后的片段"""
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"data")

        utterances = [
            {"start": 0.0, "end": 2.0, "text": "first"},
            {"start": 3.0, "end": 5.0, "text": "second"},
            {"start": 6.0, "end": 8.0, "text": "third"}
        ]

        document = TranscriptDocument(
            utterances=utterances,
            audio_path=str(audio_file),
            duration=10.0,
            asr_provider="whisper"
        )

        result = document.get_utterances_after(4.0)
        assert len(result) == 1
        assert result[0]["text"] == "third"

    def test_get_utterances_before(self, tmp_path):
        """测试获取指定时间之前的片段"""
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"data")

        utterances = [
            {"start": 0.0, "end": 2.0, "text": "first"},
            {"start": 3.0, "end": 5.0, "text": "second"},
            {"start": 6.0, "end": 8.0, "text": "third"}
        ]

        document = TranscriptDocument(
            utterances=utterances,
            audio_path=str(audio_file),
            duration=10.0,
            asr_provider="whisper"
        )

        result = document.get_utterances_before(4.0)
        assert len(result) == 1
        assert result[0]["text"] == "first"

    def test_get_utterances_between(self, tmp_path):
        """测试获取时间范围内的片段"""
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"data")

        utterances = [
            {"start": 0.0, "end": 2.0, "text": "first"},
            {"start": 3.0, "end": 5.0, "text": "second"},
            {"start": 6.0, "end": 8.0, "text": "third"}
        ]

        document = TranscriptDocument(
            utterances=utterances,
            audio_path=str(audio_file),
            duration=10.0,
            asr_provider="whisper"
        )

        result = document.get_utterances_between(2.5, 5.5)
        assert len(result) == 1
        assert result[0]["text"] == "second"

    def test_empty_utterances(self, tmp_path):
        """测试空的 utterances 列表"""
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"data")

        document = TranscriptDocument(
            utterances=[],
            audio_path=str(audio_file),
            duration=10.0,
            asr_provider="whisper"
        )

        assert document.utterance_count == 0
        assert document.get_full_text() == ""

    def test_transcript_document_with_source_path(self, tmp_path):
        """测试 TranscriptDocument 保存 source_transcript_path"""
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"data")

        utterances = [
            {"start": 0.0, "end": 2.5, "text": "test"}
        ]

        document = TranscriptDocument(
            utterances=utterances,
            audio_path=str(audio_file),
            duration=10.0,
            asr_provider="whisper",
            source_transcript_path="/path/to/raw/asr.json"
        )

        assert document.source_transcript_path == "/path/to/raw/asr.json"

    def test_transcript_document_source_path_optional(self, tmp_path):
        """测试 source_transcript_path 是可选的"""
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"data")

        utterances = [
            {"start": 0.0, "end": 2.5, "text": "test"}
        ]

        document = TranscriptDocument(
            utterances=utterances,
            audio_path=str(audio_file),
            duration=10.0,
            asr_provider="whisper"
        )

        assert document.source_transcript_path is None

    def test_to_dict_includes_source_path(self, tmp_path):
        """测试 to_dict 包含 source_transcript_path（如果存在）"""
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"data")

        utterances = [
            {"start": 0.0, "end": 2.5, "text": "test"}
        ]

        document = TranscriptDocument(
            utterances=utterances,
            audio_path=str(audio_file),
            duration=10.0,
            asr_provider="whisper",
            source_transcript_path="/path/to/raw.json"
        )

        result = document.to_dict()
        assert "source_transcript_path" in result["metadata"]
        assert result["metadata"]["source_transcript_path"] == "/path/to/raw.json"

    def test_from_dict_restores_source_path(self, tmp_path):
        """测试 from_dict 恢复 source_transcript_path"""
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"data")

        data = {
            "metadata": {
                "audio_path": str(audio_file),
                "duration": 10.0,
                "asr_provider": "whisper",
                "created_at": "2024-01-01T00:00:00",
                "source_transcript_path": "/path/to/raw.json"
            },
            "utterances": [
                {"start": 0.0, "end": 2.5, "text": "test"}
            ]
        }

        document = TranscriptDocument.from_dict(data)
        assert document.source_transcript_path == "/path/to/raw.json"
