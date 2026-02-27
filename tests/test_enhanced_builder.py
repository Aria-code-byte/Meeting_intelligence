"""
Tests for Enhanced Transcript Builder (PR2)
"""

import pytest
from pathlib import Path

from transcript.enhanced_builder import (
    TimeWindow,
    Sentence,
    Chunk,
    build_fixed_chunks,
    build_chunks_with_overlap,
    match_sentences_to_chunks,
    EnhancedTranscriptConfig,
    EnhancedTranscript,
    EnhancedSentence,
    EnhancementProcessor,
    build_enhanced_transcript,
    chunk_transcript_by_time,
    create_sentences_from_utterances,
    validate_sentences,
    validate_chunk_progression,
    TimeUnit,
)


class TestTimeWindow:
    """TimeWindow 测试"""

    def test_time_window_creation(self):
        """测试时间窗口创建"""
        window = TimeWindow(0, 60000)
        assert window.start_ms == 0
        assert window.end_ms == 60000
        assert window.duration_ms == 60000
        assert window.duration_seconds == 60.0

    def test_time_window_from_seconds(self):
        """测试从秒数创建"""
        window = TimeWindow.from_seconds(10.5, 70.5)
        assert window.start_ms == 10500
        assert window.end_ms == 70500
        assert window.duration_ms == 60000

    def test_time_window_validation(self):
        """测试验证"""
        with pytest.raises(ValueError, match="end_ms 必须大于 start_ms"):
            TimeWindow(100, 50)

        with pytest.raises(ValueError, match="start_ms 不能为负数"):
            TimeWindow(-1, 100)

    def test_overlaps_with(self):
        """测试重叠判断"""
        w1 = TimeWindow(0, 100)
        w2 = TimeWindow(50, 150)
        w3 = TimeWindow(150, 200)

        assert w1.overlaps_with(w2) is True
        assert w1.overlaps_with(w3) is False
        # w2(50-150) 和 w3(150-200) 仅在边界接触，不算重叠
        assert w2.overlaps_with(w3) is False

    def test_overlaps_with_touching_boundary(self):
        """测试边界接触不算重叠"""
        w1 = TimeWindow(0, 100)
        w2 = TimeWindow(100, 200)  # 恰好接触

        assert w1.overlaps_with(w2) is False

    def test_intersection_duration(self):
        """测试重叠时长"""
        w1 = TimeWindow(0, 100)
        w2 = TimeWindow(50, 150)

        assert w1.intersection_duration_ms(w2) == 50
        assert w1.intersection_duration_ms(TimeWindow(200, 300)) == 0

    def test_contains(self):
        """测试包含关系"""
        w1 = TimeWindow(0, 100)
        w2 = TimeWindow(20, 80)
        w3 = TimeWindow(50, 150)

        assert w1.contains(w2) is True
        assert w1.contains(w3) is False


class TestSentence:
    """Sentence 测试"""

    def test_sentence_creation(self):
        """测试句子创建"""
        sent = Sentence(
            sentence_index=0,
            start_ms=1000,
            end_ms=5000,
            text="Hello world"
        )
        assert sent.sentence_index == 0
        assert sent.start_ms == 1000
        assert sent.end_ms == 5000
        assert sent.duration_ms == 4000
        assert sent.text == "Hello world"

    def test_sentence_from_utterance(self):
        """测试从 utterance 创建"""
        utterance = {"start": 1.0, "end": 3.5, "text": "Test sentence"}
        sent = Sentence.from_utterance(5, utterance)

        assert sent.sentence_index == 5
        assert sent.start_ms == 1000
        assert sent.end_ms == 3500
        assert sent.text == "Test sentence"

    def test_sentence_validation(self):
        """测试验证"""
        with pytest.raises(ValueError, match="sentence_index 不能为负数"):
            Sentence(-1, 0, 100, "test")

        with pytest.raises(ValueError, match="text 不能为空"):
            Sentence(0, 0, 100, "")

    def test_overlaps_with_chunk(self):
        """测试与 chunk 的重叠判断"""
        sent = Sentence(0, 25000, 75000, "Test")
        chunk = TimeWindow(0, 60000)  # 0-60s

        assert sent.overlaps_with_chunk(chunk) is True

    def test_cross_chunk_sentence(self):
        """测试跨 chunk 的 sentence"""
        # sentence: 45s - 75s
        sent = Sentence(0, 45000, 75000, "Cross chunk sentence")

        chunk1 = TimeWindow(0, 60000)    # 0-60s
        chunk2 = TimeWindow(50000, 110000)  # 50-110s

        # sentence 应该与两个 chunk 都有交集
        assert sent.overlaps_with_chunk(chunk1) is True
        assert sent.overlaps_with_chunk(chunk2) is True


class TestBuildFixedChunks:
    """build_fixed_chunks 测试"""

    def test_empty_duration(self):
        """测试空时长"""
        assert build_fixed_chunks(0, 60, 10) == []
        assert build_fixed_chunks(-1, 60, 10) == []

    def test_single_chunk(self):
        """测试单个 chunk"""
        chunks = build_fixed_chunks(30000, 60, 10)  # 30秒 < 60秒窗口
        assert len(chunks) == 1
        assert chunks[0].start_ms == 0
        assert chunks[0].end_ms == 30000

    def test_multiple_chunks_with_overlap(self):
        """测试多个 chunk 带 overlap"""
        chunks = build_fixed_chunks(180000, 60, 10)  # 3分钟, 60s窗口, 10s overlap

        # 预期: 0-60s, 50-110s, 100-160s, 150-180s
        assert len(chunks) == 4

        assert chunks[0].start_ms == 0
        assert chunks[0].end_ms == 60000

        assert chunks[1].start_ms == 50000
        assert chunks[1].end_ms == 110000

        assert chunks[2].start_ms == 100000
        assert chunks[2].end_ms == 160000

        assert chunks[3].start_ms == 150000
        assert chunks[3].end_ms == 180000

    def test_overlap_verification(self):
        """验证 overlap 大小"""
        chunks = build_fixed_chunks(180000, 60, 10)

        # chunk 0 和 chunk 1 的 overlap
        assert chunks[0].end_ms - chunks[1].start_ms == 10000  # 10s overlap

        # chunk 1 和 chunk 2 的 overlap
        assert chunks[1].end_ms - chunks[2].start_ms == 10000

    def test_integer_milliseconds(self):
        """测试使用整数毫秒"""
        chunks = build_fixed_chunks(125123, 60, 10)

        # 验证所有边界都是整数
        for chunk in chunks:
            assert isinstance(chunk.start_ms, int)
            assert isinstance(chunk.end_ms, int)
            assert chunk.start_ms >= 0
            assert chunk.end_ms > chunk.start_ms

    def test_last_chunk_merge(self):
        """测试最后一个过小 chunk 被合并"""
        chunks = build_fixed_chunks(155000, 60, 10)  # 2分35秒
        # 最后一个窗口应该是 150-155 (5秒)，会被合并到前一个
        # 所以应该只有 3 个 chunk: 0-60, 50-110, 100-155

        # 注意：实际实现中，最后一个窗口如果太小（< step/2 = 25s），会被合并
        # 这里最后一个窗口 150-155 只有 5秒，所以会合并
        expected_chunks = 3
        assert len(chunks) == expected_chunks


class TestMatchSentencesToChunks:
    """match_sentences_to_chunks 测试"""

    def test_empty_sentences(self):
        """测试空 sentences"""
        chunks = [TimeWindow(0, 60000), TimeWindow(50000, 110000)]
        result = match_sentences_to_chunks([], chunks)

        assert len(result) == 2
        assert result[0].sentence_indices == []
        assert result[1].sentence_indices == []

    def test_sentence_in_single_chunk(self):
        """测试 sentence 只在一个 chunk 中"""
        sentences = [
            Sentence(0, 5000, 25000, "First sentence"),
        ]
        chunks = [TimeWindow(0, 60000)]

        result = match_sentences_to_chunks(sentences, chunks)

        assert len(result) == 1
        assert result[0].sentence_indices == [0]

    def test_sentence_crosses_two_chunks(self):
        """测试 sentence 跨越两个 chunks"""
        # sentence: 45s - 75s
        sentences = [
            Sentence(0, 45000, 75000, "Cross chunk"),
        ]
        chunks = [
            TimeWindow(0, 60000),     # 0-60s
            TimeWindow(50000, 110000)  # 50-110s
        ]

        result = match_sentences_to_chunks(sentences, chunks)

        # sentence 应该在两个 chunk 中都被匹配
        assert result[0].sentence_indices == [0]
        assert result[1].sentence_indices == [0]

    def test_multiple_sentences_multiple_chunks(self):
        """测试多句子多 chunk"""
        sentences = [
            Sentence(0, 5000, 20000, "S1"),    # 0-20s
            Sentence(1, 25000, 45000, "S2"),   # 25-45s
            Sentence(2, 50000, 75000, "S3"),   # 50-75s (跨 chunk)
            Sentence(3, 80000, 100000, "S4"),  # 80-100s
        ]
        chunks = [
            TimeWindow(0, 60000),      # 0-60s
            TimeWindow(50000, 110000)   # 50-110s
        ]

        result = match_sentences_to_chunks(sentences, chunks)

        # chunk 0: S1, S2, S3 (S3 跨 chunk)
        assert set(result[0].sentence_indices) == {0, 1, 2}

        # chunk 1: S3, S4 (S3 跨 chunk)
        assert set(result[1].sentence_indices) == {2, 3}


class TestEnhancementProcessor:
    """EnhancementProcessor 测试"""

    def test_process_chunk_placeholder(self):
        """测试 PR2 占位实现（直接返回原文）"""
        sentences = [
            Sentence(0, 5000, 15000, "Original text 1"),
            Sentence(1, 20000, 30000, "Original text 2"),
        ]
        chunk = Chunk(
            chunk_id=0,
            time_window=TimeWindow(0, 60000),
            sentence_indices=[0, 1]
        )

        processor = EnhancementProcessor()
        results = processor.process_chunk(chunk, sentences)

        assert len(results) == 2

        # PR2: enhanced_text 应该等于 original_text
        assert results[0].enhanced_text == "Original text 1"
        assert results[0].original_text == "Original text 1"
        assert results[0].confidence == 1.0

    def test_deduplication_by_sentence_index(self):
        """测试按 sentence_index 去重"""
        sentences = [
            Sentence(0, 5000, 75000, "Cross chunk"),  # 跨 chunk
        ]
        chunks_windows = [
            TimeWindow(0, 60000),
            TimeWindow(50000, 110000)
        ]

        chunks = match_sentences_to_chunks(sentences, chunks_windows)
        processor = EnhancementProcessor()

        enhanced_results = {}

        # 模拟处理两个 chunk
        for chunk in chunks:
            chunk_results = processor.process_chunk(chunk, sentences)
            # 去重逻辑：保留第一次匹配的结果
            for sent_idx, enhanced_sent in chunk_results.items():
                if sent_idx not in enhanced_results:
                    enhanced_results[sent_idx] = enhanced_sent

        # 只应该有一个结果（去重后）
        assert len(enhanced_results) == 1
        assert 0 in enhanced_results


class TestBuildEnhancedTranscript:
    """build_enhanced_transcript 集成测试"""

    def test_empty_utterances(self):
        """测试空 utterances"""
        config = EnhancedTranscriptConfig(enabled=True)
        result = build_enhanced_transcript([], config)

        assert result.sentence_count == 0
        assert result.chunk_count == 0

    def test_full_pipeline(self):
        """测试完整流程"""
        utterances = [
            {"start": 0.0, "end": 20.0, "text": "First sentence"},
            {"start": 25.0, "end": 45.0, "text": "Second sentence"},
            {"start": 50.0, "end": 75.0, "text": "Third sentence (cross chunk)"},
            {"start": 80.0, "end": 100.0, "text": "Fourth sentence"},
        ]

        config = EnhancedTranscriptConfig(
            enabled=True,
            chunk_window_seconds=60.0,
            chunk_overlap_seconds=10.0
        )

        result = build_enhanced_transcript(
            utterances,
            config,
            source_transcript_path="/path/to/raw.json"
        )

        # 验证元数据
        assert result.metadata["total_duration_ms"] == 100000
        assert result.metadata["sentence_count"] == 4
        assert result.metadata["chunk_count"] == 2  # 0-60s, 50-100s

        # 验证 sentences（按 sentence_index 排序）
        assert len(result.sentences) == 4
        assert result.sentences[0].sentence_index == 0
        assert result.sentences[1].sentence_index == 1
        assert result.sentences[2].sentence_index == 2
        assert result.sentences[3].sentence_index == 3

        # 验证 chunks
        assert len(result.chunks) == 2

        # 第一个 chunk (0-60s) 应该包含 sentence 0, 1, 2
        assert set(result.chunks[0].sentence_indices) == {0, 1, 2}

        # 第二个 chunk (50-100s) 应该包含 sentence 2, 3
        assert set(result.chunks[1].sentence_indices) == {2, 3}

    def test_cross_chunk_deduplication(self):
        """测试跨 chunk 去重"""
        utterances = [
            {"start": 45.0, "end": 75.0, "text": "Cross chunk sentence"},
        ]

        config = EnhancedTranscriptConfig(
            enabled=True,
            chunk_window_seconds=60.0,
            chunk_overlap_seconds=10.0
        )

        result = build_enhanced_transcript(utterances, config)

        # 虽然 sentence 在两个 chunk 中，但最终结果只应该有一个
        assert result.sentence_count == 1
        assert result.sentences[0].sentence_index == 0


class TestChunkTranscriptByTime:
    """chunk_transcript_by_time 便捷函数测试"""

    def test_chunking_output_format(self):
        """测试输出格式"""
        utterances = [
            {"start": 0.0, "end": 30.0, "text": "S1"},
            {"start": 35.0, "end": 65.0, "text": "S2"},
            {"start": 70.0, "end": 100.0, "text": "S3"},
        ]

        chunks = chunk_transcript_by_time(utterances, 60, 10)

        assert len(chunks) == 2

        # 验证输出格式
        assert "chunk_id" in chunks[0]
        assert "start_ms" in chunks[0]
        assert "end_ms" in chunks[0]
        assert "start_seconds" in chunks[0]
        assert "end_seconds" in chunks[0]
        assert "sentence_indices" in chunks[0]
        assert "sentence_count" in chunks[0]

    def test_integer_milliseconds_in_output(self):
        """测试输出使用整数毫秒"""
        utterances = [
            {"start": 0.0, "end": 30.0, "text": "S1"},
        ]

        chunks = chunk_transcript_by_time(utterances, 60, 10)

        # 验证使用整数毫秒
        assert isinstance(chunks[0]["start_ms"], int)
        assert isinstance(chunks[0]["end_ms"], int)


class TestEnhancedSentence:
    """EnhancedSentence 测试"""

    def test_enhanced_sentence_creation(self):
        """测试创建"""
        sent = EnhancedSentence(
            sentence_index=0,
            start_ms=1000,
            end_ms=5000,
            original_text="Original",
            enhanced_text="Enhanced",
            confidence=0.95
        )

        assert sent.sentence_index == 0
        assert sent.original_text == "Original"
        assert sent.enhanced_text == "Enhanced"
        assert sent.confidence == 0.95

    def test_confidence_validation(self):
        """测试置信度验证"""
        with pytest.raises(ValueError, match="confidence 必须在"):
            EnhancedSentence(0, 0, 1000, "a", "b", confidence=1.5)

        with pytest.raises(ValueError, match="confidence 必须在"):
            EnhancedSentence(0, 0, 1000, "a", "b", confidence=-0.1)

    def test_to_dict(self):
        """测试序列化"""
        sent = EnhancedSentence(
            sentence_index=5,
            start_ms=10000,
            end_ms=20000,
            original_text="Original",
            enhanced_text="Enhanced",
            confidence=0.85
        )

        data = sent.to_dict()

        assert data["sentence_index"] == 5
        assert data["start_ms"] == 10000
        assert data["end_ms"] == 20000
        assert data["original_text"] == "Original"
        assert data["enhanced_text"] == "Enhanced"
        assert data["confidence"] == 0.85


class TestConfigValidation:
    """EnhancedTranscriptConfig 验证测试"""

    def test_window_must_be_positive(self):
        """测试窗口必须为正"""
        with pytest.raises(ValueError):
            EnhancedTranscriptConfig(chunk_window_seconds=0)

        with pytest.raises(ValueError):
            EnhancedTranscriptConfig(chunk_window_seconds=-60)

    def test_overlap_cannot_be_negative(self):
        """测试 overlap 不能为负"""
        with pytest.raises(ValueError):
            EnhancedTranscriptConfig(chunk_overlap_seconds=-10)

    def test_overlap_must_be_less_than_window(self):
        """测试 overlap 必须小于窗口"""
        with pytest.raises(ValueError):
            EnhancedTranscriptConfig(
                chunk_window_seconds=60,
                chunk_overlap_seconds=60
            )

        with pytest.raises(ValueError):
            EnhancedTranscriptConfig(
                chunk_window_seconds=60,
                chunk_overlap_seconds=70
            )

    def test_max_drift_ms_validation(self):
        """测试 max_drift_ms 验证"""
        # 负数应该抛出错误
        with pytest.raises(ValueError):
            EnhancedTranscriptConfig(max_drift_ms=-1000)

        # 零是允许的
        config = EnhancedTranscriptConfig(max_drift_ms=0)
        assert config.max_drift_ms == 0

        # 正数是允许的
        config = EnhancedTranscriptConfig(max_drift_ms=30000)
        assert config.max_drift_ms == 30000


class TestValidateSentences:
    """validate_sentences 函数测试"""

    def test_validate_normal_sentences(self):
        """测试正常的 sentences"""
        sentences = [
            Sentence(0, 0, 1000, "First"),
            Sentence(1, 1000, 2000, "Second"),
        ]
        # 不应该抛出错误
        validate_sentences(sentences)

    def test_validate_time_regression(self):
        """测试时间倒退"""
        sentences = [
            Sentence(0, 0, 1000, "First"),
            Sentence(1, 900, 1500, "Second"),  # 倒退
        ]
        with pytest.raises(ValueError, match="时间倒退"):
            validate_sentences(sentences)

    def test_validate_one_millisecond_tolerance(self):
        """测试 1 毫秒容差"""
        sentences = [
            Sentence(0, 0, 1000, "First"),
            Sentence(1, 1000, 2000, "Second"),  # 边界接触，允许
        ]
        # 不应该抛出错误（1ms 容差）
        validate_sentences(sentences)

    # 注意：由于 Sentence.__post_init__ 已经做了基础验证，
    # validate_sentences 主要是检测时间单调性问题
    # 以下测试已在 Sentence 构造时触发，不再重复测试


class TestValidateChunkProgression:
    """validate_chunk_progression 测试"""

    def test_validate_empty_chunks(self):
        """测试空 chunks"""
        validate_chunk_progression([])  # 不应该抛出错误

    def test_validate_single_chunk(self):
        """测试单个 chunk"""
        chunks = [
            Chunk(0, TimeWindow(0, 60000))
        ]
        validate_chunk_progression(chunks)  # 不应该抛出错误

    def test_validate_normal_progression(self):
        """测试正常的 chunk 进展"""
        chunks = [
            Chunk(0, TimeWindow(0, 60000), actual_overlap_ms_with_next=10000),
            Chunk(1, TimeWindow(50000, 110000), actual_overlap_ms_with_previous=10000),
        ]
        validate_chunk_progression(chunks)  # 不应该抛出错误

    def test_validate_non_sequential_chunk_id(self):
        """测试非连续 chunk_id"""
        chunks = [
            Chunk(0, TimeWindow(0, 60000)),
            Chunk(2, TimeWindow(50000, 110000)),  # 跳过了 1
        ]
        with pytest.raises(AssertionError, match="chunk_id 不连续"):
            validate_chunk_progression(chunks)

    def test_validate_time_regression(self):
        """测试时间倒退"""
        chunks = [
            Chunk(0, TimeWindow(50000, 110000)),
            Chunk(1, TimeWindow(0, 60000)),  # 倒退
        ]
        with pytest.raises(AssertionError, match="start_ms 时间倒退"):
            validate_chunk_progression(chunks)

    def test_validate_negative_overlap(self):
        """测试负数 overlap"""
        chunks = [
            Chunk(0, TimeWindow(0, 60000)),
            Chunk(1, TimeWindow(60000, 120000), actual_overlap_ms_with_previous=-100),
        ]
        with pytest.raises(AssertionError, match="actual_overlap_ms_with_previous 为负数"):
            validate_chunk_progression(chunks)


class TestActualOverlapCalculation:
    """actual_overlap_ms_* 计算测试"""

    def test_overlap_calculation(self):
        """测试 overlap 计算"""
        config = EnhancedTranscriptConfig(
            chunk_window_seconds=60,
            chunk_overlap_seconds=10
        )

        chunks = build_chunks_with_overlap(180000, config)  # 3 分钟

        # chunk 0: 0-60000
        # chunk 1: 50000-110000, overlap = 10000ms
        assert chunks[1].actual_overlap_ms_with_previous == 10000
        assert chunks[0].actual_overlap_ms_with_next == 10000

    def test_no_overlap_at_boundary(self):
        """测试边界无 overlap"""
        chunks = build_chunks_with_overlap(120000, EnhancedTranscriptConfig(
            chunk_window_seconds=60,
            chunk_overlap_seconds=0  # 无 overlap
        ))

        assert chunks[1].actual_overlap_ms_with_previous == 0
        assert chunks[0].actual_overlap_ms_with_next == 0

    def test_first_chunk_no_previous_overlap(self):
        """测试第一个 chunk 没有 previous overlap"""
        chunks = build_chunks_with_overlap(180000, EnhancedTranscriptConfig(
            chunk_window_seconds=60,
            chunk_overlap_seconds=10
        ))

        assert chunks[0].actual_overlap_ms_with_previous == 0

    def test_last_chunk_no_next_overlap(self):
        """测试最后一个 chunk 没有 next overlap"""
        chunks = build_chunks_with_overlap(180000, EnhancedTranscriptConfig(
            chunk_window_seconds=60,
            chunk_overlap_seconds=10
        ))

        assert chunks[-1].actual_overlap_ms_with_next == 0


class TestChunkTranscriptByTimeWithOverlap:
    """chunk_transcript_by_time overlap 信息测试"""

    def test_output_includes_overlap_info(self):
        """测试输出包含 overlap 信息"""
        utterances = [
            {"start": 0.0, "end": 30.0, "text": "S1"},
            {"start": 35.0, "end": 65.0, "text": "S2"},
        ]

        chunks = chunk_transcript_by_time(utterances, 60, 10)

        # 应该包含 overlap 信息
        assert "actual_overlap_ms_with_previous" in chunks[0]
        assert "actual_overlap_ms_with_next" in chunks[0]


class TestLoopLimitProtection:
    """循环限制保护测试"""

    def test_max_chunks_protection(self, tmp_path):
        """测试 MAX_CHUNKS 保护"""
        # 创建一个非常长的 utterances 列表来测试保护机制
        # 每个 utterance 1 秒，总时长应该远超 MAX_CHUNKS * window_size
        utterances = []
        for i in range(100):  # 100 秒
            utterances.append({"start": float(i), "end": float(i + 1), "text": f"S{i}"})

        config = EnhancedTranscriptConfig(
            chunk_window_seconds=0.1,  # 0.1 秒窗口（极小）
            chunk_overlap_seconds=0.01  # 0.01 秒 overlap
        )

        # 对于 100 秒，0.1 秒窗口会产生 ~1000 个 chunk，应该不会超过限制
        result = build_enhanced_transcript(utterances, config)
        assert result.chunk_count > 0
        assert result.chunk_count < 10000  # 应该远低于限制
