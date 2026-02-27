"""
Tests for transcript load module.
"""

import pytest
import json
from pathlib import Path

from transcript.load import load_transcript, list_transcripts, get_latest_transcript, validate_transcript_file
from transcript.types import TranscriptDocument


class TestLoadTranscript:
    """load_transcript 函数测试"""

    def test_load_valid_document(self, tmp_path):
        """测试加载有效文档"""
        # 创建测试音频文件
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"data")

        # 创建测试文档
        doc_data = {
            "metadata": {
                "audio_path": str(audio_file),
                "duration": 10.0,
                "asr_provider": "whisper-local-base",
                "created_at": "2024-01-01T00:00:00",
                "utterance_count": 1
            },
            "utterances": [
                {"start": 0.0, "end": 2.5, "text": "大家好"}
            ]
        }

        doc_file = tmp_path / "transcript.json"
        with open(doc_file, "w", encoding="utf-8") as f:
            json.dump(doc_data, f)

        # 加载文档
        document = load_transcript(doc_file)

        assert document.utterance_count == 1
        assert document.duration == 10.0
        assert document.asr_provider == "whisper-local-base"
        assert document.document_path == str(doc_file)

    def test_load_nonexistent_file(self):
        """测试加载不存在的文件"""
        with pytest.raises(FileNotFoundError, match="文档文件不存在"):
            load_transcript("/nonexistent/transcript.json")

    def test_load_invalid_extension(self, tmp_path):
        """测试加载非 JSON 文件"""
        txt_file = tmp_path / "transcript.txt"
        txt_file.write_text("not json")

        with pytest.raises(ValueError, match="必须是 JSON 格式"):
            load_transcript(txt_file)

    def test_load_invalid_json(self, tmp_path):
        """测试加载损坏的 JSON"""
        json_file = tmp_path / "transcript.json"
        json_file.write_text("{ invalid json }")

        with pytest.raises(ValueError, match="JSON 格式无效"):
            load_transcript(json_file)

    def test_load_missing_metadata(self, tmp_path):
        """测试加载缺少 metadata 的文档"""
        doc_data = {
            "utterances": []
        }

        doc_file = tmp_path / "transcript.json"
        with open(doc_file, "w", encoding="utf-8") as f:
            json.dump(doc_data, f)

        with pytest.raises(ValueError, match="缺少 metadata"):
            load_transcript(doc_file)

    def test_load_missing_utterances(self, tmp_path):
        """测试加载缺少 utterances 的文档"""
        doc_data = {
            "metadata": {
                "audio_path": "test.wav",
                "duration": 10.0,
                "asr_provider": "whisper"
            }
        }

        doc_file = tmp_path / "transcript.json"
        with open(doc_file, "w", encoding="utf-8") as f:
            json.dump(doc_data, f)

        with pytest.raises(ValueError, match="缺少 utterances"):
            load_transcript(doc_file)


class TestListTranscripts:
    """list_transcripts 函数测试"""

    def test_list_empty_directory(self, tmp_path):
        """测试列出空目录"""
        result = list_transcripts(tmp_path)
        assert result == []

    def test_list_transcripts(self, tmp_path):
        """测试列出 transcript 文件"""
        # 创建测试文件
        (tmp_path / "transcript_20240101_120000.json").write_text("{}")
        (tmp_path / "transcript_20240101_130000.json").write_text("{}")
        (tmp_path / "other_file.txt").write_text("test")

        result = list_transcripts(tmp_path)

        assert len(result) == 2
        assert all("transcript_" in p for p in result)

    def test_list_nonexistent_directory(self):
        """测试列出不存在的目录"""
        result = list_transcripts("/nonexistent/path")
        assert result == []


class TestGetLatestTranscript:
    """get_latest_transcript 函数测试"""

    def test_get_latest_empty(self, tmp_path):
        """测试从空目录获取最新文档"""
        result = get_latest_transcript(tmp_path)
        assert result is None

    def test_get_latest(self, tmp_path):
        """测试获取最新文档"""
        # 创建测试音频文件
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"data")

        # 创建文档数据
        doc_data = {
            "metadata": {
                "audio_path": str(audio_file),
                "duration": 10.0,
                "asr_provider": "whisper",
                "created_at": "2024-01-01T00:00:00",
                "utterance_count": 0
            },
            "utterances": []
        }

        # 创建多个文档
        doc1 = tmp_path / "transcript_20240101_120000.json"
        doc2 = tmp_path / "transcript_20240101_130000.json"

        with open(doc1, "w") as f:
            json.dump(doc_data, f)
        with open(doc2, "w") as f:
            json.dump(doc_data, f)

        result = get_latest_transcript(tmp_path)

        assert result is not None
        assert result.utterance_count == 0


class TestValidateTranscriptFile:
    """validate_transcript_file 函数测试"""

    def test_validate_valid_file(self, tmp_path):
        """测试验证有效文件"""
        # 创建测试音频文件
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"data")

        doc_data = {
            "metadata": {
                "audio_path": str(audio_file),
                "duration": 10.0,
                "asr_provider": "whisper",
                "created_at": "2024-01-01T00:00:00",
                "utterance_count": 1
            },
            "utterances": [
                {"start": 0.0, "end": 2.5, "text": "test"}
            ]
        }

        doc_file = tmp_path / "transcript.json"
        with open(doc_file, "w", encoding="utf-8") as f:
            json.dump(doc_data, f)

        result = validate_transcript_file(doc_file)

        assert result["valid"] is True
        assert len(result["errors"]) == 0

    def test_validate_nonexistent_file(self):
        """测试验证不存在的文件"""
        result = validate_transcript_file("/nonexistent/file.json")

        assert result["valid"] is False
        assert "文件不存在" in result["errors"]

    def test_validate_missing_metadata(self, tmp_path):
        """测试验证缺少 metadata 的文件"""
        doc_data = {"utterances": []}

        doc_file = tmp_path / "transcript.json"
        with open(doc_file, "w", encoding="utf-8") as f:
            json.dump(doc_data, f)

        result = validate_transcript_file(doc_file)

        assert result["valid"] is False
        assert any("缺少 metadata" in e for e in result["errors"])

    def test_validate_missing_utterances(self, tmp_path):
        """测试验证缺少 utterances 的文件"""
        doc_data = {
            "metadata": {
                "audio_path": "test.wav",
                "duration": 10.0,
                "asr_provider": "whisper"
            }
        }

        doc_file = tmp_path / "transcript.json"
        with open(doc_file, "w", encoding="utf-8") as f:
            json.dump(doc_data, f)

        result = validate_transcript_file(doc_file)

        assert result["valid"] is False
        assert any("缺少 utterances" in e for e in result["errors"])

    def test_validate_invalid_json(self, tmp_path):
        """测试验证无效的 JSON"""
        doc_file = tmp_path / "transcript.json"
        doc_file.write_text("{ invalid }")

        result = validate_transcript_file(doc_file)

        assert result["valid"] is False
        assert any("JSON" in e for e in result["errors"])

    def test_validate_missing_utterance_field(self, tmp_path):
        """测试验证 utterance 缺少字段"""
        doc_data = {
            "metadata": {
                "audio_path": "test.wav",
                "duration": 10.0,
                "asr_provider": "whisper"
            },
            "utterances": [
                {"start": 0.0, "text": "missing end"}
            ]
        }

        doc_file = tmp_path / "transcript.json"
        with open(doc_file, "w", encoding="utf-8") as f:
            json.dump(doc_data, f)

        result = validate_transcript_file(doc_file)

        assert result["valid"] is False
        assert any("缺少字段" in e for e in result["errors"])
