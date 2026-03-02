"""
Tests for Fallback Engine (PR4)
"""

import pytest

from transcript.llm.fallback import (
    FallbackConfig,
    FallbackEngine,
    SentenceCandidate,
    EnhancedSentence,
    apply_fallback,
)
from transcript.llm.types import FallbackLevel, MappingQuality, MappingMethod


class TestFallbackConfig:
    """FallbackConfig 测试"""

    def test_default_config(self):
        """测试默认配置"""
        config = FallbackConfig()

        assert config.enable_per_sentence_fallback is False
        assert config.confidence_threshold == 0.6
        assert config.embedding_similarity_threshold == 0.7
        assert config.min_length_ratio == 0.3
        assert config.max_length_ratio == 3.0

    def test_enable_per_sentence_fallback(self):
        """测试启用单句回退"""
        config = FallbackConfig(enable_per_sentence_fallback=True)
        assert config.enable_per_sentence_fallback is True

    def test_custom_thresholds(self):
        """测试自定义阈值"""
        config = FallbackConfig(
            confidence_threshold=0.7,
            embedding_similarity_threshold=0.8
        )

        assert config.confidence_threshold == 0.7
        assert config.embedding_similarity_threshold == 0.8

    def test_invalid_confidence_threshold(self):
        """测试无效置信度阈值"""
        with pytest.raises(ValueError, match="confidence_threshold 必须在"):
            FallbackConfig(confidence_threshold=1.5)

    def test_invalid_length_ratio_range(self):
        """测试无效长度比率范围"""
        with pytest.raises(ValueError, match="max_length_ratio 必须 > min_length_ratio"):
            FallbackConfig(
                min_length_ratio=3.0,
                max_length_ratio=2.0
            )


class TestSentenceCandidate:
    """SentenceCandidate 测试"""

    def test_create_candidate(self):
        """测试创建候选项"""
        candidate = SentenceCandidate(
            sentence_index=0,
            original_text="测试",
            enhanced_text="测试增强"
        )

        assert candidate.sentence_index == 0
        assert candidate.original_text == "测试"
        assert candidate.enhanced_text == "测试增强"

    def test_empty_original_text_raises(self):
        """测试空原文抛出异常"""
        with pytest.raises(ValueError, match="original_text 不能为空"):
            SentenceCandidate(
                sentence_index=0,
                original_text="",
                enhanced_text="测试"
            )

    def test_none_enhanced_text_raises(self):
        """测试 None 增强文本抛出异常"""
        with pytest.raises(ValueError, match="enhanced_text 不能为 None"):
            SentenceCandidate(
                sentence_index=0,
                original_text="测试",
                enhanced_text=None
            )

    def test_with_metadata(self):
        """测试带元数据"""
        candidate = SentenceCandidate(
            sentence_index=0,
            original_text="测试",
            enhanced_text="测试增强",
            metadata={"start_ms": 1000, "end_ms": 2000}
        )

        assert candidate.metadata["start_ms"] == 1000

    def test_with_mapping_info(self):
        """测试带映射信息"""
        candidate = SentenceCandidate(
            sentence_index=0,
            original_text="测试",
            enhanced_text="测试增强",
            mapping_quality=MappingQuality.HIGH,
            mapping_method=MappingMethod.EXACT,
            embedding_similarity=0.9
        )

        assert candidate.mapping_quality == MappingQuality.HIGH
        assert candidate.embedding_similarity == 0.9


class TestFallbackEngine:
    """FallbackEngine 测试"""

    def setup_method(self):
        self.engine = FallbackEngine()

    def test_process_sentences_no_fallback(self):
        """测试不回退（默认配置）"""
        candidates = [
            SentenceCandidate(
                sentence_index=0,
                original_text="测试",
                enhanced_text="测试增强"
            )
        ]

        results = self.engine.process_sentences(candidates)

        assert len(results) == 1
        assert results[0].enhanced_text == "测试增强"
        assert results[0].confidence > 0
        assert results[0].fallback.level == FallbackLevel.NONE

    def test_low_confidence_triggers_fallback(self):
        """测试低置信度触发回退"""
        config = FallbackConfig(
            enable_per_sentence_fallback=True,
            confidence_threshold=0.9  # 高阈值
        )
        engine = FallbackEngine(config)

        candidates = [
            SentenceCandidate(
                sentence_index=0,
                original_text="测试",
                enhanced_text="测试"
            )
        ]

        results = engine.process_sentences(candidates)

        # confidence 会被计算为 1.0（完全相同），不会触发回退
        # 让我们用低相似度的情况
        candidates = [
            SentenceCandidate(
                sentence_index=0,
                original_text="测试文本很长很长",
                enhanced_text="短"  # 长度比率会很低
            )
        ]

        results = engine.process_sentences(candidates)

        # 应该触发回退
        assert results[0].fallback.level == FallbackLevel.SENTENCE

    def test_excessive_expansion_triggers_fallback(self):
        """测试过度扩展触发回退"""
        candidates = [
            SentenceCandidate(
                sentence_index=0,
                original_text="测试",
                enhanced_text="测试" * 20  # 非常长
            )
        ]

        results = self.engine.process_sentences(candidates)

        assert results[0].fallback.level == FallbackLevel.SENTENCE
        assert "excessive_expansion" in results[0].fallback.reason
        assert results[0].enhanced_text == candidates[0].original_text

    def test_excessive_compression_triggers_fallback(self):
        """测试过度压缩触发回退"""
        candidates = [
            SentenceCandidate(
                sentence_index=0,
                original_text="测试" * 20,
                enhanced_text="测"
            )
        ]

        results = self.engine.process_sentences(candidates)

        assert results[0].fallback.level == FallbackLevel.SENTENCE
        assert "excessive_compression" in results[0].fallback.reason

    def test_embedding_similarity_threshold(self):
        """测试 embedding 相似度阈值"""
        config = FallbackConfig(
            enable_per_sentence_fallback=True,
            embedding_similarity_threshold=0.9  # 高阈值
        )
        engine = FallbackEngine(config)

        candidates = [
            SentenceCandidate(
                sentence_index=0,
                original_text="测试",
                enhanced_text="测试增强",
                embedding_similarity=0.8  # 低于阈值
            )
        ]

        results = engine.process_sentences(candidates)

        # 应该触发回退
        assert results[0].fallback.level == FallbackLevel.SENTENCE
        assert "semantic_drift" in results[0].fallback.reason

    def test_mapping_info_preserved(self):
        """测试映射信息被保留"""
        candidates = [
            SentenceCandidate(
                sentence_index=0,
                original_text="测试",
                enhanced_text="测试增强",
                mapping_quality=MappingQuality.HIGH,
                mapping_method=MappingMethod.EXACT,
                mapping_trace={"method": "exact"}
            )
        ]

        results = self.engine.process_sentences(candidates)

        assert results[0].mapping is not None
        assert results[0].mapping.quality == MappingQuality.HIGH
        assert results[0].mapping.method == MappingMethod.EXACT

    def test_scores_populated(self):
        """测试分数被填充"""
        candidates = [
            SentenceCandidate(
                sentence_index=0,
                original_text="测试",
                enhanced_text="测试增强"
            )
        ]

        results = self.engine.process_sentences(candidates)

        assert results[0].scores is not None
        assert results[0].scores.total > 0

    def test_create_chunk_fallback(self):
        """测试创建整块回退"""
        original_sentences = [
            {"sentence_index": 0, "text": "第一句", "start_ms": 0, "end_ms": 1000},
            {"sentence_index": 1, "text": "第二句", "start_ms": 1000, "end_ms": 2000}
        ]

        results = self.engine.create_chunk_fallback(
            original_sentences,
            reason="llm_call_failed"
        )

        assert len(results) == 2
        assert results[0].enhanced_text == "第一句"  # 使用原文
        assert results[1].enhanced_text == "第二句"
        assert results[0].confidence == 0.0
        assert results[0].fallback.level == FallbackLevel.CHUNK
        assert results[0].fallback.reason == "llm_call_failed"

    def test_to_dict(self):
        """测试序列化"""
        candidates = [
            SentenceCandidate(
                sentence_index=0,
                original_text="测试",
                enhanced_text="测试增强",
                metadata={"start_ms": 0, "end_ms": 1000},
                mapping_quality=MappingQuality.HIGH,
                mapping_method=MappingMethod.EXACT,
                mapping_trace={"method": "exact"}
            )
        ]

        results = self.engine.process_sentences(candidates)

        data = results[0].to_dict()

        assert data["sentence_index"] == 0
        assert data["original_text"] == "测试"
        assert data["enhanced_text"] == "测试增强"
        assert "confidence" in data
        assert "mapping" in data
        assert "fallback" in data
        assert "scores" in data


class TestConvenienceFunction:
    """便捷函数测试"""

    def test_apply_fallback(self):
        """测试便捷函数"""
        candidates = [
            SentenceCandidate(
                sentence_index=0,
                original_text="测试",
                enhanced_text="测试增强"
            )
        ]

        results = apply_fallback(candidates)

        assert len(results) == 1
        assert isinstance(results[0], EnhancedSentence)

    def test_apply_fallback_with_config(self):
        """测试带配置的便捷函数"""
        config = FallbackConfig(
            enable_per_sentence_fallback=True,
            confidence_threshold=0.9
        )

        candidates = [
            SentenceCandidate(
                sentence_index=0,
                original_text="测试",
                enhanced_text="测试"  # confidence 会是 1.0
            )
        ]

        results = apply_fallback(candidates, config)

        # confidence 是 1.0，不小于 0.9，不会回退
        assert results[0].fallback.level == FallbackLevel.NONE


class TestProgressCallback:
    """进度回调测试"""

    def test_progress_callback_called(self):
        """测试进度回调被调用"""
        callback_calls = []

        def callback(stage, progress):
            callback_calls.append((stage, progress))

        candidates = [
            SentenceCandidate(sentence_index=i, original_text="测试", enhanced_text="测试增强")
            for i in range(3)
        ]

        engine = FallbackEngine()
        results = engine.process_sentences(candidates, callback)

        assert len(callback_calls) >= 2  # 至少有开始和结束
        assert callback_calls[-1][0] == "fallback_complete"
