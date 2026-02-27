"""
Integration tests for transcript module.
"""

import pytest
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

from transcript.build import build_transcript
from transcript.load import load_transcript, get_latest_transcript
from transcript.export import export_json, export_text, export_markdown
from transcript.types import TranscriptDocument
from asr.types import TranscriptionResult, Utterance


class TestASRToTranscriptIntegration:
    """ASR 到 Transcript 的集成测试"""

    def test_full_asr_to_transcript_flow(self, tmp_path):
        """测试完整的 ASR → Transcript 流程"""
        # 创建测试音频文件
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"RIFF" + b"\x00" * 1000)

        # 创建 ASR 结果文件
        asr_file = tmp_path / "asr_result.json"
        asr_file.write_bytes(b"{}")

        # 创建 ASR 结果
        asr_result = TranscriptionResult(
            utterances=[
                Utterance(start=0.0, end=2.5, text="大家好"),
                Utterance(start=2.6, end=5.0, text="今天讨论项目进展"),
                Utterance(start=5.5, end=8.0, text="下周一完成")
            ],
            audio_path=str(audio_file),
            duration=10.0,
            output_path=str(asr_file),
            asr_provider="whisper-local-base",
            timestamp="2024-01-01T00:00:00"
        )

        # 构建 transcript
        transcript_path = tmp_path / "transcript.json"
        document = build_transcript(asr_result, save=True, output_path=str(transcript_path))

        # 验证文档已创建
        assert Path(transcript_path).exists()

        # 验证文档内容
        loaded_doc = load_transcript(transcript_path)
        assert loaded_doc.utterance_count == 3
        assert loaded_doc.duration == 10.0
        assert loaded_doc.asr_provider == "whisper-local-base"

    def test_build_then_export(self, tmp_path):
        """测试构建后导出多种格式"""
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"data")

        # 创建 ASR 结果文件
        asr_file = tmp_path / "asr.json"
        asr_file.write_bytes(b"{}")

        asr_result = TranscriptionResult(
            utterances=[
                Utterance(start=0.0, end=2.5, text="测试内容")
            ],
            audio_path=str(audio_file),
            duration=10.0,
            output_path=str(asr_file),
            asr_provider="whisper",
            timestamp="2024-01-01T00:00:00"
        )

        # 构建（不保存）
        document = build_transcript(asr_result, save=False)

        # 导出各种格式
        json_path = export_json(document, tmp_path / "output.json")
        txt_path = export_text(document, tmp_path / "output.txt")
        md_path = export_markdown(document, tmp_path / "output.md")

        assert Path(json_path).exists()
        assert Path(txt_path).exists()
        assert Path(md_path).exists()

        # 验证内容
        json_content = json.loads(Path(json_path).read_text())
        assert json_content["metadata"]["utterance_count"] == 1

        txt_content = Path(txt_path).read_text()
        assert "测试内容" in txt_content

        md_content = Path(md_path).read_text()
        assert "测试内容" in md_content


class TestTranscriptPersistence:
    """Transcript 持久化测试"""

    def test_save_and_roundtrip(self, tmp_path):
        """测试保存和往返转换"""
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"data")

        # 创建原始文档
        original = TranscriptDocument(
            utterances=[
                {"start": 0.0, "end": 2.5, "text": "大家好"},
                {"start": 3.0, "end": 5.5, "text": "今天讨论项目"}
            ],
            audio_path=str(audio_file),
            duration=10.0,
            asr_provider="whisper-local-base"
        )

        # 保存
        saved_path = original.save(str(tmp_path / "transcript.json"))

        # 加载
        loaded = load_transcript(saved_path)

        # 验证数据一致
        assert loaded.utterance_count == original.utterance_count
        assert loaded.duration == original.duration
        assert loaded.asr_provider == original.asr_provider
        assert len(loaded.utterances) == len(original.utterances)
        assert loaded.utterances[0]["text"] == original.utterances[0]["text"]


class TestTranscriptWithASRIntegration:
    """Transcript 与 ASR 模块集成测试"""

    @patch('asr.transcribe.WhisperProvider')
    def test_transcribe_with_auto_build(self, mock_whisper_class, tmp_path):
        """测试 ASR 转写时自动构建 transcript"""
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"RIFF" + b"\x00" * 1000)

        # Mock Whisper provider
        mock_provider = MagicMock()
        mock_provider.name = "whisper-local-base"
        mock_provider.transcribe.return_value = [
            Utterance(start=0.0, end=2.5, text="大家好"),
            Utterance(start=2.6, end=5.0, text="测试")
        ]
        mock_whisper_class.return_value = mock_provider

        # Mock _get_audio_duration
        with patch('audio.extract_audio._get_audio_duration', return_value=10.0):
            from asr.transcribe import transcribe

            # 转写时自动构建 transcript
            result = transcribe(str(audio_file), auto_build_transcript=True)

            # 验证结果包含 transcript_path
            assert result.transcript_path is not None
            assert Path(result.transcript_path).exists()

            # 验证可以加载 transcript
            from transcript.load import load_transcript
            doc = load_transcript(result.transcript_path)
            assert doc.utterance_count == 2

    @patch('asr.transcribe.WhisperProvider')
    def test_transcribe_without_auto_build(self, mock_whisper_class, tmp_path):
        """测试 ASR 转写时不自动构建 transcript"""
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"RIFF" + b"\x00" * 1000)

        # Mock Whisper provider
        mock_provider = MagicMock()
        mock_provider.name = "whisper-local-base"
        mock_provider.transcribe.return_value = [
            Utterance(start=0.0, end=2.5, text="大家好")
        ]
        mock_whisper_class.return_value = mock_provider

        # Mock _get_audio_duration
        with patch('audio.extract_audio._get_audio_duration', return_value=10.0):
            from asr.transcribe import transcribe

            # 转写时不自动构建
            result = transcribe(str(audio_file), auto_build_transcript=False)

            # 验证结果不包含 transcript_path
            assert result.transcript_path is None


class TestTranscriptQueries:
    """Transcript 查询功能测试"""

    def test_time_based_queries(self, tmp_path):
        """测试基于时间的查询"""
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"data")

        document = TranscriptDocument(
            utterances=[
                {"start": 0.0, "end": 2.0, "text": "first"},
                {"start": 3.0, "end": 5.0, "text": "second"},
                {"start": 6.0, "end": 8.0, "text": "third"},
                {"start": 9.0, "end": 11.0, "text": "fourth"}
            ],
            audio_path=str(audio_file),
            duration=15.0,
            asr_provider="whisper"
        )

        # 查询时间之后的
        after = document.get_utterances_after(5.0)
        assert len(after) == 2
        assert after[0]["text"] == "third"

        # 查询时间之前的
        before = document.get_utterances_before(5.0)
        assert len(before) == 2
        assert before[0]["text"] == "first"
        assert before[1]["text"] == "second"

        # 查询时间范围内的
        between = document.get_utterances_between(2.5, 8.5)
        assert len(between) == 2
        assert between[0]["text"] == "second"
        assert between[1]["text"] == "third"


class TestTranscriptWithEmptyASR:
    """空 ASR 结果的处理测试"""

    def test_empty_asr_result(self, tmp_path):
        """测试处理空的 ASR 结果"""
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"data")

        # 创建 ASR 结果文件
        asr_file = tmp_path / "asr.json"
        asr_file.write_bytes(b"{}")

        asr_result = TranscriptionResult(
            utterances=[],  # 空
            audio_path=str(audio_file),
            duration=10.0,
            output_path=str(asr_file),
            asr_provider="whisper",
            timestamp="2024-01-01T00:00:00"
        )

        # 构建 transcript
        document = build_transcript(asr_result, save=False)

        # 验证空文档正确创建
        assert document.utterance_count == 0
        assert document.get_full_text() == ""
        assert len(document.utterances) == 0
