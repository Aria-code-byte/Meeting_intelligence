"""
Tests for PositionMapper (PR4)
"""

import pytest

from transcript.llm.mapper import PositionMapper
from transcript.llm.types import MappingQuality, MappingMethod


class TestPositionMapper:
    """PositionMapper 测试"""

    def test_supports_method(self):
        """测试方法类型"""
        mapper = PositionMapper()
        assert mapper.supports_method() == MappingMethod.POSITION

    def test_direct_match_same_count(self):
        """测试句子数量相同时直接映射"""
        mapper = PositionMapper()

        enhanced_text = "大家好。今天我们讨论项目。"
        original_sentences = [
            {"sentence_index": 0, "text": "大家好"},
            {"sentence_index": 1, "text": "今天我们讨论项目"}
        ]

        results = mapper.map(enhanced_text, original_sentences)

        assert len(results) == 2
        # 中文标点会被转换成英文标点
        assert results[0].enhanced_text == "大家好."
        assert results[1].enhanced_text == "今天我们讨论项目."
        assert results[0].mapping_quality == MappingQuality.LOW
        assert results[0].mapping_method == MappingMethod.POSITION

    def test_ratio_mapping_different_count(self):
        """测试句子数量不同时比例映射"""
        mapper = PositionMapper()

        # 增强文本只有一句话（使用英文标点）
        enhanced_text = "大家好,今天我们讨论项目."
        original_sentences = [
            {"sentence_index": 0, "text": "大家好"},
            {"sentence_index": 1, "text": "今天我们讨论项目"}
        ]

        results = mapper.map(enhanced_text, original_sentences)

        assert len(results) == 2
        # 两句都分配到了增强文本的一部分

    def test_split_chinese_punctuation(self):
        """测试中文标点分割"""
        mapper = PositionMapper()

        enhanced_text = "大家好！今天怎么样？还不错。"
        original_sentences = [
            {"sentence_index": 0, "text": "大家好"},
            {"sentence_index": 1, "text": "今天怎么样"},
            {"sentence_index": 2, "text": "还不错"}
        ]

        results = mapper.map(enhanced_text, original_sentences)

        assert len(results) == 3
        assert "大家好" in results[0].enhanced_text
        assert "今天怎么样" in results[1].enhanced_text
        assert "还不错" in results[2].enhanced_text

    def test_split_mixed_punctuation(self):
        """测试混合标点分割"""
        mapper = PositionMapper()

        enhanced_text = "Hello. 测试！What's up?"
        original_sentences = [
            {"sentence_index": 0, "text": "Hello"},
            {"sentence_index": 1, "text": "测试"},
            {"sentence_index": 2, "text": "What's up"}
        ]

        results = mapper.map(enhanced_text, original_sentences)

        assert len(results) == 3

    def test_split_english_punctuation(self):
        """测试英文标点分割"""
        mapper = PositionMapper()

        enhanced_text = "Hello world. How are you? I'm fine."
        original_sentences = [
            {"sentence_index": 0, "text": "Hello world"},
            {"sentence_index": 1, "text": "How are you"},
            {"sentence_index": 2, "text": "I'm fine"}
        ]

        results = mapper.map(enhanced_text, original_sentences)

        assert len(results) == 3
        assert results[0].enhanced_text == "Hello world."
        assert results[1].enhanced_text == "How are you?"
        assert results[2].enhanced_text == "I'm fine."

    def test_no_punctuation_returns_single_sentence(self):
        """测试无标点时返回单句"""
        mapper = PositionMapper()

        enhanced_text = "hello world how are you"
        original_sentences = [
            {"sentence_index": 0, "text": "hello"}
        ]

        results = mapper.map(enhanced_text, original_sentences)

        assert len(results) == 1
        assert results[0].enhanced_text == "hello world how are you"

    def test_empty_sentences(self):
        """测试空句子列表"""
        mapper = PositionMapper()

        enhanced_text = "测试文本"
        original_sentences = []

        results = mapper.map(enhanced_text, original_sentences)

        assert results == []

    def test_empty_enhanced_text(self):
        """测试空增强文本"""
        mapper = PositionMapper()

        enhanced_text = ""
        original_sentences = [
            {"sentence_index": 0, "text": "测试"}
        ]

        results = mapper.map(enhanced_text, original_sentences)

        assert len(results) == 1
        assert results[0].enhanced_text == ""

    def test_mapping_trace_contains_strategy(self):
        """测试映射追踪包含策略信息"""
        mapper = PositionMapper()

        enhanced_text = "测试。文本。"
        original_sentences = [
            {"sentence_index": 0, "text": "测试"},
            {"sentence_index": 1, "text": "文本"}
        ]

        results = mapper.map(enhanced_text, original_sentences)

        trace = results[0].mapping_trace
        assert trace["method"] == "position"
        assert "strategy" in trace

    def test_trailing_text_appended_to_last(self):
        """测试多余文本追加到最后一句"""
        mapper = PositionMapper()

        # 增强文本比原句多
        enhanced_text = "第一句。第二句。第三句。"
        original_sentences = [
            {"sentence_index": 0, "text": "第一句"},
            {"sentence_index": 1, "text": "第二句"}
        ]

        results = mapper.map(enhanced_text, original_sentences)

        assert len(results) == 2
        # 第三句应该被追加到最后
        assert "第三句" in results[-1].enhanced_text

    def test_chinese_english_mixed(self):
        """测试中英混合"""
        mapper = PositionMapper()

        enhanced_text = "Hello大家好。How are you怎么样？"
        original_sentences = [
            {"sentence_index": 0, "text": "Hello大家好"},
            {"sentence_index": 1, "text": "How are you怎么样"}
        ]

        results = mapper.map(enhanced_text, original_sentences)

        assert len(results) == 2


class TestSplitIntoSentences:
    """_split_into_sentences 私有方法测试"""

    def test_split_simple(self):
        """测试简单分割"""
        mapper = PositionMapper()
        sentences = mapper._split_into_sentences("A. B. C.")
        assert len(sentences) >= 3
        assert "A." in sentences[0]
        assert "B." in sentences[1]

    def test_split_chinese(self):
        """测试中文分割"""
        mapper = PositionMapper()
        sentences = mapper._split_into_sentences("你好。世界。")
        assert len(sentences) >= 2
        assert "你好" in sentences[0]
        assert "世界" in sentences[1]

    def test_split_mixed(self):
        """测试混合分割"""
        mapper = PositionMapper()
        sentences = mapper._split_into_sentences("你好！Hello? World。")
        assert len(sentences) >= 3

    def test_split_no_punctuation(self):
        """测试无标点"""
        mapper = PositionMapper()
        sentences = mapper._split_into_sentences("hello world")
        assert len(sentences) == 1
        assert sentences[0] == "hello world"
