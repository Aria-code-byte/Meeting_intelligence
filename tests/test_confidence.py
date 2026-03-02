"""
Tests for Confidence Calculator (PR4)
"""

import pytest

from transcript.llm.confidence import (
    ConfidenceCalculator,
    ConfidenceCalculatorConfig,
    calculate_confidence,
)
from transcript.llm.types import ConfidenceBreakdown, MappingQuality


class TestConfidenceCalculatorConfig:
    """ConfidenceCalculatorConfig 测试"""

    def test_default_config(self):
        """测试默认配置"""
        config = ConfidenceCalculatorConfig()

        assert config.embedding_similarity_weight == 0.6
        assert config.length_ratio_weight == 0.2
        assert config.llm_metadata_weight == 0.2

    def test_custom_weights(self):
        """测试自定义权重"""
        config = ConfidenceCalculatorConfig(
            embedding_similarity_weight=0.5,
            length_ratio_weight=0.3,
            llm_metadata_weight=0.2
        )

        assert config.embedding_similarity_weight == 0.5
        assert config.length_ratio_weight == 0.3
        assert config.llm_metadata_weight == 0.2

    def test_weights_must_sum_to_one(self):
        """测试权重总和必须为 1"""
        with pytest.raises(ValueError, match="权重总和应为 1.0"):
            ConfidenceCalculatorConfig(
                embedding_similarity_weight=0.5,
                length_ratio_weight=0.3,
                llm_metadata_weight=0.3  # 总和 1.1
            )

    def test_to_dict(self):
        """测试配置序列化"""
        config = ConfidenceCalculatorConfig()
        weights = config.to_dict()

        assert weights["embedding_similarity"] == 0.6
        assert weights["length_ratio"] == 0.2
        assert weights["llm_metadata"] == 0.2


class TestLengthRatioScore:
    """长度比率得分测试"""

    def setup_method(self):
        self.calculator = ConfidenceCalculator()

    def test_ideal_range_high_score(self):
        """测试理想范围（0.8-1.5）得高分"""
        # 1.0 倍
        score = self.calculator._calculate_length_ratio_score(
            "hello world",
            "hello world"
        )
        assert score == 1.0

        # 1.2 倍
        score = self.calculator._calculate_length_ratio_score(
            "hello",
            "hello!!"  # 5 vs 7 = 1.4 倍
        )
        assert score == 1.0

        # 0.9 倍
        score = self.calculator._calculate_length_ratio_score(
            "hello world!",
            "hello world"
        )
        assert score == 1.0

    def test_excessive_expansion_low_score(self):
        """测试过度扩展得低分"""
        score = self.calculator._calculate_length_ratio_score(
            "hi",
            "hi " * 10  # 20 倍
        )
        assert score == 0.2

    def test_excessive_compression_low_score(self):
        """测试过度压缩得低分"""
        score = self.calculator._calculate_length_ratio_score(
            "hello world this is a long text",
            "hi"
        )
        assert score < 0.5

    def test_empty_original(self):
        """测试空原文"""
        # 两个都空
        score = self.calculator._calculate_length_ratio_score("", "")
        assert score == 0.0

        # 原文空，增强非空
        score = self.calculator._calculate_length_ratio_score("", "hello")
        assert score == 0.3

    def test_interpolate_values(self):
        """测试插值计算"""
        # 0.65 倍（0.5 和 0.8 之间）
        score = self.calculator._calculate_length_ratio_score(
            "hello world!",
            "hello"
        )
        # 长度 12 vs 5 = 0.417 倍，在 0.3-0.5 之间
        assert 0.3 <= score <= 0.5

        # 在 0.5-0.8 之间插值
        score = self.calculator._calculate_length_ratio_score(
            "hello world test!",
            "hello world!"
        )
        # 长度 19 vs 12 = 0.63 倍
        assert 0.6 <= score <= 1.0


class TestLLMMetadataParsing:
    """LLM 元数据解析测试"""

    def setup_method(self):
        self.calculator = ConfidenceCalculator()

    def test_finish_reason_stop(self):
        """测试 stop 原因得高分"""
        score = self.calculator._parse_llm_metadata({"finish_reason": "stop"})
        assert score == 1.0

    def test_finish_reason_length(self):
        """测试 length 原因得中分"""
        score = self.calculator._parse_llm_metadata({"finish_reason": "length"})
        assert score == 0.7

    def test_no_metadata(self):
        """测试无元数据返回 None"""
        score = self.calculator._parse_llm_metadata(None)
        assert score is None

    def test_empty_metadata(self):
        """测试空元数据"""
        score = self.calculator._parse_llm_metadata({})
        assert score == 0.5

    def test_unknown_finish_reason(self):
        """测试未知原因得中分"""
        score = self.calculator._parse_llm_metadata({"finish_reason": "unknown"})
        assert score == 0.5


class TestConfidenceCalculation:
    """置信度计算测试"""

    def setup_method(self):
        self.calculator = ConfidenceCalculator()

    def test_all_features_present(self):
        """测试所有特征都存在"""
        breakdown = self.calculator.calculate(
            original="hello world",
            enhanced="hello world!",
            embedding_similarity=0.9,
            llm_metadata={"finish_reason": "stop"}
        )

        assert breakdown.total > 0.8  # 高置信度
        assert breakdown.embedding_similarity == 0.9
        assert breakdown.length_ratio == 1.0
        assert breakdown.llm_metadata == 1.0

    def test_only_length_ratio(self):
        """测试只有长度比率"""
        breakdown = self.calculator.calculate(
            original="hello world",
            enhanced="hello world!",
            embedding_similarity=None,
            llm_metadata=None
        )

        # 只有 length_ratio，权重应重分配
        assert breakdown.total == breakdown.length_ratio
        assert breakdown.embedding_similarity is None
        assert breakdown.llm_metadata is None

    def test_embedding_and_length(self):
        """测试 embedding + length_ratio"""
        breakdown = self.calculator.calculate(
            original="hello",
            enhanced="hello!",
            embedding_similarity=0.8,
            llm_metadata=None
        )

        assert breakdown.embedding_similarity == 0.8
        assert breakdown.llm_metadata is None
        # 权重重分配: 0.6/(0.6+0.2)=0.75, 0.2/(0.6+0.2)=0.25
        expected = 0.8 * 0.75 + 1.0 * 0.25
        assert abs(breakdown.total - expected) < 0.01

    def test_low_embedding_similarity(self):
        """测试低 embedding 相似度"""
        breakdown = self.calculator.calculate(
            original="hello world",
            enhanced="completely different text",
            embedding_similarity=0.3,
            llm_metadata={"finish_reason": "stop"}
        )

        assert breakdown.total < 0.5  # 低置信度

    def test_excessive_length_change(self):
        """测试过度长度变化"""
        breakdown = self.calculator.calculate(
            original="hi",
            enhanced="hi " * 20,  # 很长的扩展
            embedding_similarity=None,
            llm_metadata=None
        )

        assert breakdown.total < 0.3  # 低置信度

    def test_to_dict(self):
        """测试序列化"""
        breakdown = self.calculator.calculate(
            original="hello",
            enhanced="hello!",
            embedding_similarity=0.9,
            llm_metadata={"finish_reason": "stop"}
        )

        data = breakdown.to_dict()

        assert data["total"] > 0
        assert data["embedding_similarity"] == 0.9
        assert data["length_ratio"] == 1.0
        assert data["llm_metadata"] == 1.0

    def test_to_dict_with_none_values(self):
        """测试含 None 值的序列化"""
        breakdown = self.calculator.calculate(
            original="hello",
            enhanced="hello!",
            embedding_similarity=None,
            llm_metadata=None
        )

        data = breakdown.to_dict()

        assert "total" in data
        assert "length_ratio" in data
        assert "embedding_similarity" not in data  # None 不输出
        assert "llm_metadata" not in data  # None 不输出


class TestConvenienceFunction:
    """便捷函数测试"""

    def test_calculate_confidence(self):
        """测试便捷函数"""
        breakdown = calculate_confidence(
            original="hello",
            enhanced="hello!",
            embedding_similarity=0.85
        )

        assert isinstance(breakdown, ConfidenceBreakdown)
        assert breakdown.total > 0

    def test_calculate_confidence_with_custom_config(self):
        """测试自定义配置"""
        config = ConfidenceCalculatorConfig(
            embedding_similarity_weight=0.7,
            length_ratio_weight=0.3,
            llm_metadata_weight=0.0
        )

        breakdown = calculate_confidence(
            original="hello",
            enhanced="hello!",
            embedding_similarity=0.8,
            config=config
        )

        # 0.7/(0.7+0.3) * 0.8 + 0.3/(0.7+0.3) * 1.0 = 0.7*0.8 + 0.3*1.0 = 0.86
        assert abs(breakdown.total - 0.86) < 0.01
