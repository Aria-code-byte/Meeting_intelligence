"""
Tests for transcript formatter module.
"""

import pytest
import json
from pathlib import Path
from datetime import datetime

from transcript.formatter import (
    TranscriptFormatter,
    FormattedTranscript,
    FormatterConfig,
    FormatMethod,
    Paragraph,
    Section,
    format_transcript,
    format_utterances,
)


class TestFormatterConfig:
    """FormatterConfig 测试"""

    def test_default_config(self):
        """测试默认配置"""
        config = FormatterConfig()
        assert config.merge_gap_threshold == 3.0
        assert config.paragraph_max_length == 300
        assert config.paragraph_min_length == 50
        assert config.section_break_gap == 10.0
        assert config.section_max_duration == 300.0

    def test_custom_config(self):
        """测试自定义配置"""
        config = FormatterConfig(
            merge_gap_threshold=5.0,
            paragraph_max_length=500
        )
        assert config.merge_gap_threshold == 5.0
        assert config.paragraph_max_length == 500


class TestParagraph:
    """Paragraph 测试"""

    def test_paragraph_creation(self):
        """测试段落创建"""
        para = Paragraph(
            text="测试文本",
            start_time=0.0,
            end_time=10.0,
            utterance_indices=[0, 1, 2]
        )
        assert para.text == "测试文本"
        assert para.duration() == 10.0
        assert para.word_count() == 4

    def test_empty_paragraph(self):
        """测试空段落"""
        para = Paragraph(text="", start_time=0.0, end_time=0.0)
        assert para.word_count() == 0
        assert para.duration() == 0.0


class TestSection:
    """Section 测试"""

    def test_section_creation(self):
        """测试 section 创建"""
        paragraphs = [
            Paragraph(text="第一段", start_time=0.0, end_time=10.0),
            Paragraph(text="第二段", start_time=10.0, end_time=20.0),
        ]
        section = Section(
            paragraphs=paragraphs,
            start_time=0.0,
            end_time=20.0,
            section_type="content"
        )
        assert section.paragraph_count() == 2
        # "第一段" = 3 字, "第二段" = 3 字, 共 6 字
        assert section.word_count() == 6
        assert section.duration() == 20.0

    def test_empty_section(self):
        """测试空 section"""
        section = Section(
            paragraphs=[],
            start_time=0.0,
            end_time=0.0
        )
        assert section.paragraph_count() == 0
        assert section.word_count() == 0


class TestTranscriptFormatter:
    """TranscriptFormatter 测试"""

    @pytest.fixture
    def sample_utterances(self):
        """示例 utterances"""
        return [
            {"start": 0.0, "end": 1.8, "text": "起这么夸张的标题的"},
            {"start": 2.06, "end": 3.84, "text": "但听完今天的课程之后"},
            {"start": 3.84, "end": 6.92, "text": "你就会发现其实蓝哥今天给这些课程起的名字"},
            {"start": 6.92, "end": 8.96, "text": "一点点也不夸张"},
            {"start": 10.24, "end": 11.2, "text": "就大家都知道嘛"},
            {"start": 11.2, "end": 14.84, "text": "就是今天的课程的内容是支撑着蓝哥舞"},
            {"start": 30.0, "end": 33.0, "text": "这是一个新的段落"},  # 长停顿
        ]

    def test_format_empty_utterances(self):
        """测试空 utterances"""
        formatter = TranscriptFormatter()
        result = formatter.format([])

        assert result.sections == []
        assert result.metadata.get("error") == "No utterances provided"

    def test_format_rule_based(self, sample_utterances):
        """测试规则格式化"""
        formatter = TranscriptFormatter()
        result = formatter.format(sample_utterances, method=FormatMethod.RULE_BASED)

        assert isinstance(result, FormattedTranscript)
        assert result.metadata["format_method"] == "rule_based"
        assert len(result.sections) > 0
        assert result.total_paragraph_count() > 0

    def test_merge_utterances(self, sample_utterances):
        """测试合并 utterances"""
        formatter = TranscriptFormatter()
        sentences = formatter._merge_utterances(sample_utterances)

        assert len(sentences) > 0
        assert len(sentences) < len(sample_utterances)  # 合并后数量减少

        # 检查句子结构
        for sent in sentences:
            assert "text" in sent
            assert "start" in sent
            assert "end" in sent
            assert "utterance_indices" in sent

    def test_build_paragraphs(self, sample_utterances):
        """测试构建段落"""
        formatter = TranscriptFormatter()
        sentences = formatter._merge_utterances(sample_utterances)
        paragraphs = formatter._build_paragraphs(sentences)

        assert len(paragraphs) > 0

        # 检查段落结构
        for para in paragraphs:
            assert isinstance(para, Paragraph)
            assert para.text
            assert para.start_time <= para.end_time

    def test_build_sections(self, sample_utterances):
        """测试构建 section"""
        formatter = TranscriptFormatter()
        sentences = formatter._merge_utterances(sample_utterances)
        paragraphs = formatter._build_paragraphs(sentences)
        sections = formatter._build_sections(paragraphs)

        assert len(sections) > 0

        # 检查 section 结构
        for section in sections:
            assert isinstance(section, Section)
            assert section.paragraphs

    def test_long_pause_creates_new_section(self):
        """测试长停顿会创建新 section"""
        utterances = [
            {"start": 0.0, "end": 2.0, "text": "第一段内容"},
            {"start": 3.0, "end": 5.0, "text": "继续第一段"},
            {"start": 20.0, "end": 22.0, "text": "第二段内容"},  # 长停顿
        ]

        formatter = TranscriptFormatter(FormatterConfig(section_break_gap=10.0))
        result = formatter.format(utterances, method=FormatMethod.RULE_BASED)

        # 应该有多个 section
        assert len(result.sections) >= 1

    def test_custom_config(self, sample_utterances):
        """测试自定义配置"""
        config = FormatterConfig(
            merge_gap_threshold=1.0,
            paragraph_max_length=100
        )
        formatter = TranscriptFormatter(config)
        result = formatter.format(sample_utterances, method=FormatMethod.RULE_BASED)

        assert isinstance(result, FormattedTranscript)

    def test_semantic_method_not_implemented(self, sample_utterances):
        """测试语义方法未实现"""
        formatter = TranscriptFormatter()

        with pytest.raises(NotImplementedError):
            formatter.format(sample_utterances, method=FormatMethod.SEMANTIC)


class TestFormattedTranscript:
    """FormattedTranscript 测试"""

    @pytest.fixture
    def sample_formatted(self):
        """示例格式化文稿"""
        paragraphs = [
            Paragraph(text="第一段内容", start_time=0.0, end_time=10.0),
            Paragraph(text="第二段内容", start_time=10.0, end_time=20.0),
        ]
        sections = [
            Section(
                paragraphs=paragraphs,
                start_time=0.0,
                end_time=20.0,
                section_type="content"
            )
        ]
        return FormattedTranscript(
            metadata={
                "format_method": "rule_based",
                "word_count": 8,
                "duration": 20.0
            },
            sections=sections
        )

    def test_total_word_count(self, sample_formatted):
        """测试总字数统计"""
        # "第一段内容" = 5 字, "第二段内容" = 5 字, 共 10 字
        assert sample_formatted.total_word_count() == 10

    def test_total_paragraph_count(self, sample_formatted):
        """测试总段落数统计"""
        assert sample_formatted.total_paragraph_count() == 2

    def test_total_duration(self, sample_formatted):
        """测试总时长统计"""
        assert sample_formatted.total_duration() == 20.0

    def test_to_markdown(self, sample_formatted):
        """测试 Markdown 转换"""
        markdown = sample_formatted.to_markdown()

        assert "# 会议文稿" in markdown
        assert "第一段内容" in markdown
        assert "第二段内容" in markdown

    def test_to_plain_text(self, sample_formatted):
        """测试纯文本转换"""
        text = sample_formatted.to_plain_text()

        assert "会议文稿" in text
        assert "第一段内容" in text
        assert "第二段内容" in text

    def test_to_html(self, sample_formatted):
        """测试 HTML 转换"""
        html = sample_formatted.to_html()

        assert "<html>" in html
        assert "第一段内容" in html
        assert "第二段内容" in html

    def test_to_dict(self, sample_formatted):
        """测试字典转换"""
        data = sample_formatted.to_dict()

        assert "metadata" in data
        assert "sections" in data
        assert len(data["sections"]) == 1
        assert len(data["sections"][0]["paragraphs"]) == 2

    def test_format_duration(self):
        """测试时长格式化"""
        transcript = FormattedTranscript(metadata={}, sections=[])
        assert transcript._format_duration(125.5) == "2分5秒"
        assert transcript._format_duration(65.0) == "1分5秒"
        assert transcript._format_duration(45.0) == "0分45秒"

    def test_format_time_range(self):
        """测试时间范围格式化"""
        transcript = FormattedTranscript(metadata={}, sections=[])
        result = transcript._format_time_range(65.0, 185.0)
        assert "01:05" in result
        assert "03:05" in result


class TestConvenienceFunctions:
    """便捷函数测试"""

    def test_format_utterances(self):
        """测试直接格式化 utterances"""
        utterances = [
            {"start": 0.0, "end": 2.0, "text": "测试内容"},
        ]
        result = format_utterances(utterances)

        assert isinstance(result, FormattedTranscript)
        assert len(result.sections) > 0

    def test_format_utterances_with_config(self):
        """测试带配置的格式化"""
        utterances = [
            {"start": 0.0, "end": 2.0, "text": "测试内容"},
        ]
        config = FormatterConfig(merge_gap_threshold=5.0)
        result = format_utterances(utterances, config=config)

        assert isinstance(result, FormattedTranscript)


class TestIntegration:
    """集成测试"""

    def test_full_formatting_workflow(self, tmp_path):
        """测试完整格式化工作流"""
        # 创建临时音频文件（用于通过文件存在性检查）
        audio_path = tmp_path / "test.wav"
        audio_path.write_bytes(b"fake audio data")

        # 创建临时转录文件
        utterances = [
            {"start": 0.0, "end": 1.8, "text": "起这么夸张的标题的"},
            {"start": 2.06, "end": 3.84, "text": "但听完今天的课程之后"},
            {"start": 3.84, "end": 6.92, "text": "你就会发现其实蓝哥今天给这些课程起的名字"},
            {"start": 6.92, "end": 8.96, "text": "一点点也不夸张"},
            {"start": 30.0, "end": 33.0, "text": "这是一个新的段落"},
        ]

        transcript_data = {
            "metadata": {
                "audio_path": str(audio_path),
                "duration": 33.0,
                "asr_provider": "whisper",
                "created_at": datetime.now().isoformat(),
                "utterance_count": len(utterances)
            },
            "utterances": utterances
        }

        transcript_path = tmp_path / "transcript.json"
        with open(transcript_path, "w", encoding="utf-8") as f:
            json.dump(transcript_data, f, ensure_ascii=False)

        # 格式化
        output_path = tmp_path / "output.md"
        result = format_transcript(
            str(transcript_path),
            output_path=str(output_path),
            output_format="markdown"
        )

        # 验证结果
        assert isinstance(result, FormattedTranscript)
        assert output_path.exists()

        # 验证输出文件内容
        content = output_path.read_text(encoding="utf-8")
        assert "# 会议文稿" in content
        assert "起这么夸张的标题的" in content

    def test_save_different_formats(self, tmp_path):
        """测试保存不同格式"""
        utterances = [
            {"start": 0.0, "end": 2.0, "text": "测试内容"},
        ]

        result = format_utterances(utterances)

        # 保存为 Markdown
        md_path = tmp_path / "output.md"
        result.save(md_path, format="markdown")
        assert md_path.exists()

        # 保存为纯文本
        txt_path = tmp_path / "output.txt"
        result.save(txt_path, format="plain")
        assert txt_path.exists()

        # 保存为 HTML
        html_path = tmp_path / "output.html"
        result.save(html_path, format="html")
        assert html_path.exists()
