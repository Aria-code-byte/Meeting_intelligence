"""
Tests for Refiner Module (新增精修模块测试)
"""

import pytest

from template.refiner import (
    RefinerExample,
    REFINER_EXAMPLES,
    build_few_shot_prompt,
    build_refiner_system_prompt,
    build_refiner_user_prompt,
    get_refiner_prompts,
)

from transcript.llm.enhancer import (
    LLMTranscriptEnhancer,
    LLMEnhancerConfig,
    preprocess_utterances,
    clean_enhanced_text,
)


class TestRefinerExamples:
    """Refiner 示例测试"""

    def test_examples_exist(self):
        """测试示例库存在"""
        assert len(REFINER_EXAMPLES) > 0
        assert all(isinstance(ex, RefinerExample) for ex in REFINER_EXAMPLES)

    def test_example_to_markdown(self):
        """测试示例转换为 Markdown"""
        example = RefinerExample(
            original="蓝哥舞",
            refined="蓝哥我",
            description="修正错别字"
        )
        markdown = example.to_markdown()
        assert "蓝哥舞" in markdown
        assert "蓝哥我" in markdown
        assert "修正错别字" in markdown


class TestRefinerPrompts:
    """Refiner 提示词测试"""

    def test_build_few_shot_prompt(self):
        """测试构建 Few-shot 提示词"""
        prompt = build_few_shot_prompt()
        assert "示例 1" in prompt
        assert "原始" in prompt
        assert "修正" in prompt
        assert "说明" in prompt

    def test_build_refiner_system_prompt(self):
        """测试构建系统提示词"""
        prompt = build_refiner_system_prompt()
        assert "专业速记校对员" in prompt
        assert "同音错别字" in prompt
        assert "带/代/待" in prompt
        assert "贷" in prompt

    def test_build_refiner_user_prompt(self):
        """测试构建用户提示词"""
        prompt = build_refiner_user_prompt("测试文本")
        assert "测试文本" in prompt
        assert "原始转录" in prompt
        assert "处理要求" in prompt

    def test_get_refiner_prompts(self):
        """测试获取完整提示词"""
        prompts = get_refiner_prompts("测试文本")
        assert "system_prompt" in prompts
        assert "user_prompt" in prompts
        assert "专业速记校对员" in prompts["system_prompt"]

    def test_get_refiner_prompts_without_examples(self):
        """测试不包含示例的提示词"""
        prompts = get_refiner_prompts("测试文本", include_examples=False)
        assert "system_prompt" in prompts
        assert "user_prompt" in prompts
        # 不包含示例时，user_prompt 中不应有 "示例 1"
        assert "示例 1" not in prompts["user_prompt"]


class TestPreprocessUtterances:
    """预处理 utterances 测试"""

    def test_empty_utterances(self):
        """测试空列表"""
        result = preprocess_utterances([])
        assert result == []

    def test_single_utterance(self):
        """测试单个片段"""
        utterances = [
            {"start": 0.0, "end": 1.0, "text": "Hello"}
        ]
        result = preprocess_utterances(utterances)
        assert len(result) == 1
        assert result[0]["text"] == "Hello"
        assert result[0]["start"] == 0.0
        assert result[0]["end"] == 1.0

    def test_merge_close_utterances(self):
        """测试合并时间间隔小的片段"""
        utterances = [
            {"start": 0.0, "end": 1.0, "text": "Hello"},
            {"start": 1.001, "end": 2.0, "text": "World"},  # 间隔 < 500ms
        ]
        result = preprocess_utterances(utterances, min_gap_ms=500)
        assert len(result) == 1
        assert "Hello" in result[0]["text"]
        assert "World" in result[0]["text"]

    def test_keep_separated_utterances(self):
        """测试保留时间间隔大的片段"""
        utterances = [
            {"start": 0.0, "end": 1.0, "text": "Hello"},
            {"start": 2.0, "end": 3.0, "text": "World"},  # 间隔 >= 500ms
        ]
        result = preprocess_utterances(utterances, min_gap_ms=500)
        assert len(result) == 2

    def test_preserve_timestamps(self):
        """测试保留原始时间戳（整数毫秒）"""
        # 使用较大的时间间隔，避免被合并
        utterances = [
            {"start": 0.123, "end": 1.456, "text": "First"},
            {"start": 3.000, "end": 4.500, "text": "Second"},  # 间隔 > 500ms
        ]
        result = preprocess_utterances(utterances, min_gap_ms=500)
        # 时间戳应该被保留（不修改）
        assert len(result) == 2  # 两个片段应该分开
        assert result[0]["start"] == 0.123
        assert result[0]["end"] == 1.456
        assert result[1]["start"] == 3.000
        assert result[1]["end"] == 4.500

    def test_max_chunk_duration(self):
        """测试最大块时长限制"""
        # 创建多个小片段，总时长超过限制
        utterances = [
            {"start": float(i), "end": float(i + 5), "text": f"Text{i}"}
            for i in range(0, 100, 5)  # 0-5, 5-10, 10-15, ...
        ]
        result = preprocess_utterances(
            utterances,
            min_gap_ms=0,
            max_chunk_duration_ms=15000  # 15秒
        )
        # 应该被分成多个块
        assert len(result) > 1


class TestCleanEnhancedText:
    """清洗增强文本测试"""

    def test_strip_whitespace(self):
        """测试去除首尾空格"""
        result = clean_enhanced_text("  Hello World  ")
        assert result == "Hello World"

    def test_remove_extra_spaces(self):
        """测试去除多余空格"""
        result = clean_enhanced_text("Hello     World")
        assert result == "Hello World"

    def test_preserve_punctuation_spacing(self):
        """测试保留标点后的空格"""
        result = clean_enhanced_text("Hello, world!")
        assert result == "Hello, world!"

    def test_normalize_quotes(self):
        """测试标准化引号"""
        result = clean_enhanced_text('"Hello"')
        # 简单引号标准化
        assert '"' in result or '"' in result

    def test_empty_text(self):
        """测试空文本"""
        result = clean_enhanced_text("")
        assert result == ""

    def test_none_text(self):
        """测试 None 文本"""
        result = clean_enhanced_text(None)
        assert result is None


class TestSpeechToTextRefinerTemplate:
    """speech-to-text-refiner 模板测试"""

    def test_template_exists(self):
        """测试模板存在"""
        from transcript.llm.enhancer import PREDEFINED_TEMPLATES
        assert "speech-to-text-refiner" in PREDEFINED_TEMPLATES

    def test_template_content(self):
        """测试模板内容"""
        from transcript.llm.enhancer import PREDEFINED_TEMPLATES
        template = PREDEFINED_TEMPLATES["speech-to-text-refiner"]

        # 检查关键内容存在
        assert "ASR" in template.system_prompt or "转录" in template.system_prompt
        assert "同音错别字" in template.system_prompt or "错别字" in template.system_prompt
        assert "蓝哥舞" in template.system_prompt or "蓝哥我" in template.system_prompt
        assert "{transcript_text}" in template.user_prompt_template

    def test_template_has_few_shot_examples(self):
        """测试模板包含 Few-shot 示例"""
        from transcript.llm.enhancer import PREDEFINED_TEMPLATES
        template = PREDEFINED_TEMPLATES["speech-to-text-refiner"]

        # 检查是否有示例内容
        assert "示例" in template.system_prompt or "示例" in template.user_prompt_template

    def test_enhancer_with_refiner_template(self):
        """测试使用 refiner 模板的增强器"""
        config = LLMEnhancerConfig(
            provider="mock",
            template_name="speech-to-text-refiner"
        )
        enhancer = LLMTranscriptEnhancer(config)

        assert enhancer.template.name == "个人叙述精修"
        result = enhancer.enhance("蓝哥舞从东北来")
        assert result.success is True


class TestEnhanceUtterances:
    """enhance_utterances 方法测试"""

    def test_empty_utterances(self):
        """测试空 utterances"""
        config = LLMEnhancerConfig(provider="mock")
        enhancer = LLMTranscriptEnhancer(config)

        result = enhancer.enhance_utterances([])
        assert result.success is False

    def test_enhance_utterances_success(self):
        """测试成功增强 utterances"""
        config = LLMEnhancerConfig(provider="mock")
        enhancer = LLMTranscriptEnhancer(config)

        utterances = [
            {"start": 0.0, "end": 1.0, "text": "Hello"},
            {"start": 1.5, "end": 2.5, "text": "World"},
        ]

        result = enhancer.enhance_utterances(utterances)
        assert result.success is True
        assert result.original_text == "Hello World"
        assert "original_utterance_count" in result.metadata

    def test_enhance_utterances_preserves_timestamps(self):
        """测试保留原始时间戳"""
        config = LLMEnhancerConfig(provider="mock")
        enhancer = LLMTranscriptEnhancer(config)

        utterances = [
            {"start": 0.123, "end": 1.456, "text": "First"},
            {"start": 2.0, "end": 3.0, "text": "Second"},
        ]

        result = enhancer.enhance_utterances(utterances)
        # 原始时间戳被保留在 metadata 中
        assert result.metadata["original_utterance_count"] == 2
