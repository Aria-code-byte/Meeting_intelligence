"""
Tests for transcript build module.
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from transcript.build import build_transcript, format_timestamp, group_utterances_into_paragraphs, get_transcript_stats
from asr.types import TranscriptionResult, Utterance


class TestBuildTranscript:
    """build_transcript 函数测试"""

    def test_build_transcript_success(self, tmp_path):
        """测试成功构建 transcript"""
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
                Utterance(start=2.6, end=5.0, text="今天讨论项目")
            ],
            audio_path=str(audio_file),
            duration=10.0,
            output_path=str(asr_file),
            asr_provider="whisper-local-base",
            timestamp="2024-01-01T00:00:00"
        )

        # 构建 transcript（不保存）
        document = build_transcript(asr_result, save=False)

        assert document.utterance_count == 2
        assert document.duration == 10.0
        assert document.asr_provider == "whisper-local-base"
        assert len(document.utterances) == 2
        assert document.utterances[0]["text"] == "大家好"
        assert document.utterances[1]["text"] == "今天讨论项目"

    def test_build_transcript_save(self, tmp_path):
        """测试构建并保存 transcript"""
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"data")

        # 创建 ASR 结果文件
        asr_file = tmp_path / "asr_result.json"
        asr_file.write_bytes(b"{}")

        asr_result = TranscriptionResult(
            utterances=[
                Utterance(start=0.0, end=2.5, text="大家好")
            ],
            audio_path=str(audio_file),
            duration=10.0,
            output_path=str(asr_file),
            asr_provider="whisper",
            timestamp="2024-01-01T00:00:00"
        )

        # 指定输出路径
        output_path = tmp_path / "transcript_output.json"
        document = build_transcript(asr_result, save=True, output_path=str(output_path))

        assert Path(output_path).exists()
        assert document.document_path == str(output_path)

    def test_build_transcript_invalid_result_type(self):
        """测试无效的 ASR 结果类型"""
        with pytest.raises(ValueError, match="asr_result 必须是 TranscriptionResult 类型"):
            build_transcript("not a result", save=False)

    def test_build_transcript_preserves_raw_source(self, tmp_path):
        """测试构建 transcript 时追溯原始 ASR 路径"""
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"data")

        asr_file = tmp_path / "asr_result.json"
        asr_file.write_bytes(b"{}")

        # 创建原始 transcript 文件
        raw_transcript_file = tmp_path / "raw_transcript.json"
        raw_transcript_file.write_bytes(b'{"utterances": [], "audio_path": "test.wav"}')

        asr_result = TranscriptionResult(
            utterances=[
                Utterance(start=0.0, end=2.5, text="大家好")
            ],
            audio_path=str(audio_file),
            duration=10.0,
            output_path=str(asr_file),
            asr_provider="whisper",
            timestamp="2024-01-01T00:00:00",
            transcript_path=str(raw_transcript_file)
        )

        document = build_transcript(asr_result, save=False)

        # 验证 source_transcript_path 正确记录
        assert document.source_transcript_path == str(raw_transcript_file)

    def test_build_transcript_disabled_enhanced_by_default(self, tmp_path):
        """测试 enhanced 默认不启用"""
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"data")

        asr_file = tmp_path / "asr_result.json"
        asr_file.write_bytes(b"{}")

        asr_result = TranscriptionResult(
            utterances=[Utterance(start=0.0, end=2.5, text="test")],
            audio_path=str(audio_file),
            duration=10.0,
            output_path=str(asr_file),
            asr_provider="whisper",
            timestamp="2024-01-01T00:00:00"
        )

        document = build_transcript(asr_result, save=False)

        # PR1: enhanced 不应自动生成
        assert asr_result.enhanced_transcript_path is None
        # 默认行为应与原版一致
        assert document.utterance_count == 1
        assert document.utterances[0]["text"] == "test"

    def test_build_transcript_with_enhanced_flag_true(self, tmp_path):
        """测试 enable_enhanced=True 时行为（PR1 仅预留接口）"""
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"data")

        asr_file = tmp_path / "asr_result.json"
        asr_file.write_bytes(b"{}")

        asr_result = TranscriptionResult(
            utterances=[Utterance(start=0.0, end=2.5, text="test")],
            audio_path=str(audio_file),
            duration=10.0,
            output_path=str(asr_file),
            asr_provider="whisper",
            timestamp="2024-01-01T00:00:00"
        )

        # PR1: enable_enhanced=True 暂不改变行为
        document = build_transcript(asr_result, save=False, enable_enhanced=True)

        # 验证原内容未被修改
        assert document.utterance_count == 1
        assert document.utterances[0]["text"] == "test"
        # Future PRs 将在此添加 enhanced 处理逻辑


class TestFormatTimestamp:
    """format_timestamp 函数测试"""

    def test_format_timestamp_seconds(self):
        """测试格式化秒数"""
        assert format_timestamp(0) == "[00:00]"
        assert format_timestamp(30) == "[00:30]"
        assert format_timestamp(59) == "[00:59]"

    def test_format_timestamp_minutes(self):
        """测试格式化分钟"""
        assert format_timestamp(60) == "[01:00]"
        assert format_timestamp(90) == "[01:30]"
        assert format_timestamp(3661) == "[61:01]"


class TestGroupUtterancesIntoParagraphs:
    """group_utterances_into_paragraphs 函数测试"""

    def test_empty_utterances(self):
        """测试空的 utterances 列表"""
        result = group_utterances_into_paragraphs([])
        assert result == []

    def test_single_utterance(self):
        """测试单个 utterance"""
        utterances = [
            {"start": 0.0, "end": 2.5, "text": "hello"}
        ]
        result = group_utterances_into_paragraphs(utterances)
        assert len(result) == 1
        assert len(result[0]) == 1

    def test_continuous_speech(self):
        """测试连续语音（间隔小）"""
        utterances = [
            {"start": 0.0, "end": 2.0, "text": "first"},
            {"start": 2.5, "end": 4.0, "text": "second"},
            {"start": 4.5, "end": 6.0, "text": "third"}
        ]
        result = group_utterances_into_paragraphs(utterances, max_gap=3.0)
        assert len(result) == 1
        assert len(result[0]) == 3

    def test_speech_with_pause(self):
        """测试有停顿的语音（间隔大）"""
        utterances = [
            {"start": 0.0, "end": 2.0, "text": "first"},
            {"start": 10.0, "end": 12.0, "text": "second"}
        ]
        result = group_utterances_into_paragraphs(utterances, max_gap=3.0)
        assert len(result) == 2
        assert len(result[0]) == 1
        assert len(result[1]) == 1

    def test_multiple_paragraphs(self):
        """测试多个段落"""
        utterances = [
            {"start": 0.0, "end": 2.0, "text": "p1-1"},
            {"start": 2.5, "end": 4.0, "text": "p1-2"},
            {"start": 15.0, "end": 17.0, "text": "p2-1"},
            {"start": 17.5, "end": 19.0, "text": "p2-2"},
            {"start": 30.0, "end": 32.0, "text": "p3-1"}
        ]
        result = group_utterances_into_paragraphs(utterances, max_gap=3.0)
        assert len(result) == 3
        assert len(result[0]) == 2
        assert len(result[1]) == 2
        assert len(result[2]) == 1


class TestGetTranscriptStats:
    """get_transcript_stats 函数测试"""

    def test_get_stats(self, tmp_path):
        """测试获取统计信息"""
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"data")

        from transcript.types import TranscriptDocument

        document = TranscriptDocument(
            utterances=[
                {"start": 0.0, "end": 3.0, "text": "hello world"},
                {"start": 5.0, "end": 8.0, "text": "this is a test"}
            ],
            audio_path=str(audio_file),
            duration=20.0,
            asr_provider="whisper"
        )

        stats = get_transcript_stats(document)

        assert stats["total_utterances"] == 2
        assert stats["total_words"] == 6
        assert stats["duration_seconds"] == 20.0
        assert stats["speaking_time_seconds"] == 6.0
        assert "words_per_minute" in stats
        assert "speaking_ratio" in stats

    def test_get_stats_empty(self, tmp_path):
        """测试空文档的统计信息"""
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"data")

        from transcript.types import TranscriptDocument

        document = TranscriptDocument(
            utterances=[],
            audio_path=str(audio_file),
            duration=10.0,
            asr_provider="whisper"
        )

        stats = get_transcript_stats(document)

        assert stats["total_utterances"] == 0
        assert stats["total_words"] == 0
        assert stats["speaking_time_seconds"] == 0
        assert stats["words_per_minute"] == 0
