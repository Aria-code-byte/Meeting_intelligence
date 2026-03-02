"""
Tests for ExactMapper (PR4)
"""

import pytest

from transcript.llm.mapper import ExactMapper
from transcript.llm.types import MappingQuality, MappingMethod
from transcript.llm.enhancer import ParseError


class TestExactMapper:
    """ExactMapper 测试"""

    def test_supports_method(self):
        """测试方法类型"""
        mapper = ExactMapper()
        assert mapper.supports_method() == MappingMethod.EXACT

    def test_parse_valid_json(self):
        """测试解析有效 JSON"""
        mapper = ExactMapper()

        llm_output = '''{
  "sentences": [
    {"sentence_index": 0, "enhanced_text": "大家好！"},
    {"sentence_index": 1, "enhanced_text": "今天我们讨论项目。"}
  ]
}'''

        original_sentences = [
            {"sentence_index": 0, "text": "大家好"},
            {"sentence_index": 1, "text": "今天我们讨论项目"}
        ]

        results = mapper.map(llm_output, original_sentences)

        assert len(results) == 2
        assert results[0].sentence_index == 0
        assert results[0].enhanced_text == "大家好！"
        assert results[0].mapping_quality == MappingQuality.HIGH
        assert results[0].mapping_method == MappingMethod.EXACT

    def test_parse_json_from_markdown(self):
        """测试从 Markdown 代码块解析 JSON"""
        mapper = ExactMapper()

        llm_output = '''```json
{
  "sentences": [
    {"sentence_index": 0, "enhanced_text": "测试文本"}
  ]
}
```'''

        original_sentences = [
            {"sentence_index": 0, "text": "测试文本"}
        ]

        results = mapper.map(llm_output, original_sentences)

        assert len(results) == 1
        assert results[0].enhanced_text == "测试文本"

    def test_parse_invalid_schema_missing_sentences(self):
        """测试缺少 sentences 字段"""
        mapper = ExactMapper()

        llm_output = '{"result": "something"}'
        original_sentences = [{"sentence_index": 0, "text": "测试"}]

        results = mapper.map(llm_output, original_sentences)

        # 非严格模式返回空列表
        assert results == []

    def test_parse_invalid_schema_missing_index(self):
        """测试缺少 sentence_index 字段"""
        mapper = ExactMapper()

        llm_output = '''{
  "sentences": [
    {"enhanced_text": "测试文本"}
  ]
}'''

        original_sentences = [{"sentence_index": 0, "text": "测试"}]

        results = mapper.map(llm_output, original_sentences)

        assert results == []

    def test_strict_mode_raises_on_invalid_json(self):
        """测试严格模式下无效 JSON 抛出异常"""
        mapper = ExactMapper(strict=True)

        llm_output = "not valid json"
        original_sentences = [{"sentence_index": 0, "text": "测试"}]

        with pytest.raises(ParseError):
            mapper.map(llm_output, original_sentences)

    def test_strict_mode_raises_on_invalid_schema(self):
        """测试严格模式下无效 schema 抛出异常"""
        mapper = ExactMapper(strict=True)

        llm_output = '{"result": "something"}'
        original_sentences = [{"sentence_index": 0, "text": "测试"}]

        with pytest.raises(ParseError, match="schema"):
            mapper.map(llm_output, original_sentences)

    def test_partial_match(self):
        """测试部分匹配"""
        mapper = ExactMapper()

        # LLM 只返回部分句子
        llm_output = '''{
  "sentences": [
    {"sentence_index": 0, "enhanced_text": "第一句"}
  ]
}'''

        original_sentences = [
            {"sentence_index": 0, "text": "第一句"},
            {"sentence_index": 1, "text": "第二句"}
        ]

        results = mapper.map(llm_output, original_sentences)

        # 只返回匹配的部分
        assert len(results) == 1
        assert results[0].sentence_index == 0

    def test_mapping_trace(self):
        """测试映射追踪信息"""
        mapper = ExactMapper()

        llm_output = '''{
  "sentences": [
    {"sentence_index": 0, "enhanced_text": "测试"}
  ]
}'''

        original_sentences = [{"sentence_index": 0, "text": "测试"}]

        results = mapper.map(llm_output, original_sentences)

        trace = results[0].mapping_trace
        assert "method" in trace
        assert trace["method"] == "exact"
        assert "input_sentences" in trace
        assert "output_sentences" in trace
        assert "duration_ms" in trace
        assert "timestamp" in trace

    def test_preserves_llm_notes(self):
        """测试保留 LLM notes（如果存在）"""
        mapper = ExactMapper()

        llm_output = '''{
  "sentences": [
    {"sentence_index": 0, "enhanced_text": "测试", "llm_notes": "添加了标点"}
  ]
}'''

        original_sentences = [{"sentence_index": 0, "text": "测试"}]

        results = mapper.map(llm_output, original_sentences)

        # enhanced_text 被正确提取
        assert results[0].enhanced_text == "测试"

    def test_empty_sentences_list(self):
        """测试空句子列表"""
        mapper = ExactMapper()

        llm_output = '{"sentences": []}'
        original_sentences = []

        results = mapper.map(llm_output, original_sentences)

        assert results == []

    def test_empty_llm_output(self):
        """测试空 LLM 输出"""
        mapper = ExactMapper()

        llm_output = ""
        original_sentences = [{"sentence_index": 0, "text": "测试"}]

        results = mapper.map(llm_output, original_sentences)

        assert results == []
