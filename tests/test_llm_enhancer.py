"""
Tests for LLM Enhancement Module (PR3)
"""

import pytest
from pathlib import Path

from transcript.llm.enhancer import (
    LLMTranscriptEnhancer,
    LLMEnhancerConfig,
    EnhancedTranscriptResult,
    PromptTemplate,
    PREDEFINED_TEMPLATES,
    EnhancementError,
    LLMProviderError,
    ParseError,
    map_enhanced_text_to_sentences,
    _split_into_sentences,
)


class TestPromptTemplate:
    """PromptTemplate 测试"""

    def test_predefined_templates_exist(self):
        """测试预定义模板存在"""
        assert "general" in PREDEFINED_TEMPLATES
        assert "technical" in PREDEFINED_TEMPLATES
        assert "executive" in PREDEFINED_TEMPLATES
        assert "minimal" in PREDEFINED_TEMPLATES

    def test_template_format_user_prompt(self):
        """测试格式化用户提示词"""
        template = PromptTemplate(
            name="test",
            system_prompt="Test system",
            user_prompt_template="Text: {transcript_text}"
        )

        result = template.format_user_prompt("Hello world")
        assert result == "Text: Hello world"


class TestLLMEnhancerConfig:
    """LLMEnhancerConfig 测试"""

    def test_default_config(self):
        """测试默认配置"""
        config = LLMEnhancerConfig()

        assert config.enabled is False
        assert config.provider == "openai"
        assert config.model == "gpt-4o-mini"
        assert config.max_tokens == 8000
        assert config.temperature == 0.3
        assert config.fallback_on_error is True
        assert config.template_name == "general"

    def test_custom_config(self):
        """测试自定义配置"""
        config = LLMEnhancerConfig(
            provider="anthropic",
            model="claude-3-5-sonnet",
            temperature=0.5,
            template_name="technical"
        )

        assert config.provider == "anthropic"
        assert config.model == "claude-3-5-sonnet"
        assert config.temperature == 0.5
        assert config.template_name == "technical"

    def test_get_template_predefined(self):
        """测试获取预定义模板"""
        config = LLMEnhancerConfig(template_name="technical")
        template = config.get_template()

        assert template.name == "技术会议"  # 模板的 name 是中文名称
        assert "技术" in template.system_prompt or "技术" in template.description

    def test_get_template_custom(self):
        """测试获取自定义模板"""
        config = LLMEnhancerConfig(
            template_name="custom",
            system_prompt="Custom system",
            user_prompt_template="Custom: {transcript_text}"
        )
        template = config.get_template()

        assert template.name == "custom"
        assert template.system_prompt == "Custom system"

    def test_validation_max_tokens_positive(self):
        """测试 max_tokens 必须 > 0"""
        with pytest.raises(ValueError, match="max_tokens 必须 > 0"):
            LLMEnhancerConfig(max_tokens=0)

    def test_validation_temperature_range(self):
        """测试 temperature 范围"""
        with pytest.raises(ValueError, match="temperature 必须在"):
            LLMEnhancerConfig(temperature=3.0)

        with pytest.raises(ValueError, match="temperature 必须在"):
            LLMEnhancerConfig(temperature=-0.5)

    def test_validation_unknown_template_without_custom(self):
        """测试未知模板且无自定义提示词"""
        with pytest.raises(ValueError, match="未知模板名称"):
            LLMEnhancerConfig(template_name="unknown")


class TestLLMTranscriptEnhancer:
    """LLMTranscriptEnhancer 测试"""

    def test_init_with_config(self):
        """测试初始化"""
        config = LLMEnhancerConfig(
            provider="mock",
            model="test-model"
        )

        enhancer = LLMTranscriptEnhancer(config)

        assert enhancer.config == config
        assert enhancer.provider is not None
        assert enhancer.template is not None

    def test_init_with_mock_provider(self):
        """测试使用 Mock Provider"""
        config = LLMEnhancerConfig(provider="mock")
        enhancer = LLMTranscriptEnhancer(config)

        # Mock provider 应该被创建
        assert enhancer.provider is not None

    def test_enhance_success_with_mock(self):
        """测试使用 Mock 增强成功"""
        config = LLMEnhancerConfig(provider="mock")
        enhancer = LLMTranscriptEnhancer(config)

        # Mock provider 应该返回预设的响应
        result = enhancer.enhance("大家 好")

        assert result.success is True
        assert result.original_text == "大家 好"
        assert result.fallback_used is False

    def test_enhance_with_fallback(self):
        """测试回退模式"""
        config = LLMEnhancerConfig(
            provider="mock",
            fallback_on_error=True
        )
        enhancer = LLMTranscriptEnhancer(config)

        # 即使 mock 失败，也应该回退到原文
        result = enhancer.enhance("test text")

        assert result.success is True


class TestEnhancedTranscriptResult:
    """EnhancedTranscriptResult 测试"""

    def test_result_creation(self):
        """测试创建结果"""
        result = EnhancedTranscriptResult(
            original_text="Original",
            enhanced_text="Enhanced"
        )

        assert result.original_text == "Original"
        assert result.enhanced_text == "Enhanced"
        assert result.success is True
        assert result.fallback_used is False

    def test_result_with_error(self):
        """测试带错误的结果"""
        result = EnhancedTranscriptResult(
            original_text="Original",
            enhanced_text="Enhanced",
            success=False,
            error_message="API error"
        )

        assert result.success is False
        assert result.error_message == "API error"

    def test_result_fallback_used(self):
        """测试回退结果"""
        result = EnhancedTranscriptResult(
            original_text="Original",
            enhanced_text="Original",  # 回退使用原文
            fallback_used=True
        )

        assert result.fallback_used is True

    def test_to_dict(self):
        """测试序列化"""
        result = EnhancedTranscriptResult(
            original_text="Original",
            enhanced_text="Enhanced",
            metadata={"model": "gpt-4"}
        )

        data = result.to_dict()

        assert data["original_text"] == "Original"
        assert data["enhanced_text"] == "Enhanced"
        assert data["success"] is True
        assert data["metadata"]["model"] == "gpt-4"


class TestSplitIntoSentences:
    """_split_into_sentences 测试"""

    def test_split_simple_text(self):
        """测试分割简单文本"""
        text = "Hello world. How are you?"
        sentences = _split_into_sentences(text)

        assert len(sentences) >= 2
        assert "Hello world" in sentences[0] or "Hello" in sentences[0]

    def test_split_chinese_punctuation(self):
        """测试中文标点分割"""
        text = "大家好。今天我们讨论项目。"
        sentences = _split_into_sentences(text)

        assert len(sentences) >= 1
        assert any("大家好" in s for s in sentences)

    def test_split_mixed_punctuation(self):
        """测试混合标点"""
        text = "你好！Hello world. 今天不错。"
        sentences = _split_into_sentences(text)

        assert len(sentences) >= 2

    def test_split_no_punctuation(self):
        """测试无标点文本"""
        text = "Hello world how are you"
        sentences = _split_into_sentences(text)

        # 无标点时应返回原文
        assert len(sentences) == 1
        assert sentences[0] == text


class TestMapEnhancedTextToSentences:
    """map_enhanced_text_to_sentences 测试"""

    def test_empty_original_sentences(self):
        """测试空原始 sentences"""
        result = map_enhanced_text_to_sentences("Enhanced text", [])
        assert result == []

    def test_same_count_mapping(self):
        """测试相同数量映射"""
        original = [
            {"sentence_index": 0, "start_ms": 0, "end_ms": 1000, "text": "First"},
            {"sentence_index": 1, "start_ms": 1000, "end_ms": 2000, "text": "Second"},
        ]

        # 增强文本恰好也是两句话
        enhanced = "First enhanced. Second enhanced."
        result = map_enhanced_text_to_sentences(enhanced, original)

        assert len(result) == 2
        assert result[0]["sentence_index"] == 0
        assert result[1]["sentence_index"] == 1
        assert "enhanced_text" in result[0]
        assert "enhanced_text" in result[1]

    def test_preserves_original_fields(self):
        """测试保留原始字段"""
        original = [
            {"sentence_index": 0, "start_ms": 1000, "end_ms": 2500, "text": "Original text"},
        ]

        enhanced = "Enhanced version."
        result = map_enhanced_text_to_sentences(enhanced, original)

        assert result[0]["sentence_index"] == 0
        assert result[0]["start_ms"] == 1000
        assert result[0]["end_ms"] == 2500
        assert result[0]["text"] == "Original text"
        assert result[0]["enhanced_text"] == "Enhanced version."


class TestErrorClasses:
    """错误类测试"""

    def test_enhancement_error(self):
        """测试基础错误类"""
        error = EnhancementError("Test error")
        assert str(error) == "Test error"

    def test_llm_provider_error(self):
        """测试 LLM 提供商错误"""
        error = LLMProviderError("API failed")
        assert isinstance(error, EnhancementError)
        assert "API failed" in str(error)

    def test_parse_error(self):
        """测试解析错误"""
        error = ParseError("Invalid format")
        assert isinstance(error, EnhancementError)
        assert "Invalid format" in str(error)


class TestPredefinedTemplatesContent:
    """预定义模板内容测试"""

    def test_general_template_content(self):
        """测试通用模板内容"""
        template = PREDEFINED_TEMPLATES["general"]

        assert "标点" in template.system_prompt
        assert "语法" in template.system_prompt
        assert "{transcript_text}" in template.user_prompt_template

    def test_technical_template_content(self):
        """测试技术会议模板内容"""
        template = PREDEFINED_TEMPLATES["technical"]

        assert "技术" in template.system_prompt or "技术" in template.description

    def test_executive_template_content(self):
        """测试高管汇报模板内容"""
        template = PREDEFINED_TEMPLATES["executive"]

        assert "高管" in template.system_prompt or "高管" in template.description

    def test_minimal_template_content(self):
        """测试最小改动模板内容"""
        template = PREDEFINED_TEMPLATES["minimal"]

        assert "最小" in template.system_prompt or "最小" in template.description
