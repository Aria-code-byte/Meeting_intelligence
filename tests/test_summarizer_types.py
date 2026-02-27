"""
Tests for summarizer module types.
"""

import pytest
from pathlib import Path
from datetime import datetime

from summarizer.types import SummaryResult, SummarySection, SectionFormat


class TestSectionFormat:
    """SectionFormat 枚举测试"""

    def test_format_values(self):
        """测试格式枚举值"""
        assert SectionFormat.BULLET_POINTS.value == "bullet-points"
        assert SectionFormat.PARAGRAPH.value == "paragraph"
        assert SectionFormat.TABLE.value == "table"
        assert SectionFormat.MIXED.value == "mixed"


class TestSummarySection:
    """SummarySection 类测试"""

    def test_section_creation(self):
        """测试部分创建"""
        section = SummarySection(
            id="summary",
            title="会议总结",
            content="这是总结内容"
        )

        assert section.id == "summary"
        assert section.title == "会议总结"
        assert section.content == "这是总结内容"
        assert section.format == SectionFormat.BULLET_POINTS
        assert section.order == 0

    def test_section_is_empty(self):
        """测试空内容检测"""
        section = SummarySection("id", "Title", "")
        assert section.is_empty() is True

        section = SummarySection("id", "Title", "内容")
        assert section.is_empty() is False

    def test_section_to_dict(self):
        """测试转换为字典"""
        section = SummarySection(
            id="test",
            title="Test",
            content="Test content"
        )

        result = section.to_dict()

        assert result["id"] == "test"
        assert result["title"] == "Test"
        assert result["content"] == "Test content"
        assert result["format"] == "bullet-points"

    def test_section_from_dict(self):
        """测试从字典创建"""
        data = {
            "id": "test",
            "title": "Test",
            "content": "Content",
            "format": "paragraph",
            "order": 5
        }

        section = SummarySection.from_dict(data)

        assert section.id == "test"
        assert section.title == "Test"
        assert section.content == "Content"
        assert section.format == SectionFormat.PARAGRAPH
        assert section.order == 5


class TestSummaryResult:
    """SummaryResult 类测试"""

    def test_summary_creation_minimal(self, tmp_path):
        """测试最小总结创建"""
        # 创建测试转录文档
        transcript_file = tmp_path / "transcript.json"
        transcript_file.write_bytes(b"{}")

        sections = [
            SummarySection(id="s1", title="Section 1", content="Content 1", order=1)
        ]

        summary = SummaryResult(
            sections=sections,
            transcript_path=str(transcript_file),
            template_name="test",
            template_role="Test Role",
            llm_provider="mock",
            llm_model="mock-model"
        )

        assert len(summary.sections) == 1
        assert summary.template_name == "test"
        assert summary.llm_provider == "mock"

    def test_summary_nonexistent_transcript(self):
        """测试转录文档不存在"""
        sections = [SummarySection(id="s1", title="S1", content="C1", order=1)]

        with pytest.raises(FileNotFoundError):
            SummaryResult(
                sections=sections,
                transcript_path="/nonexistent/transcript.json",
                template_name="test",
                template_role="Test",
                llm_provider="mock",
                llm_model="mock"
            )

    def test_get_section(self, tmp_path):
        """测试获取部分"""
        transcript_file = tmp_path / "transcript.json"
        transcript_file.write_bytes(b"{}")

        sections = [
            SummarySection(id="s1", title="S1", content="C1", order=1),
            SummarySection(id="s2", title="S2", content="C2", order=2)
        ]

        summary = SummaryResult(
            sections=sections,
            transcript_path=str(transcript_file),
            template_name="test",
            template_role="Test",
            llm_provider="mock",
            llm_model="mock"
        )

        section = summary.get_section("s2")
        assert section is not None
        assert section.title == "S2"

        section = summary.get_section("nonexistent")
        assert section is None

    def test_get_full_text(self, tmp_path):
        """测试获取完整文本"""
        transcript_file = tmp_path / "transcript.json"
        transcript_file.write_bytes(b"{}")

        sections = [
            SummarySection(id="s1", title="S1", content="Content 1", order=1),
            SummarySection(id="s2", title="S2", content="Content 2", order=2)
        ]

        summary = SummaryResult(
            sections=sections,
            transcript_path=str(transcript_file),
            template_name="test",
            template_role="Test",
            llm_provider="mock",
            llm_model="mock"
        )

        full_text = summary.get_full_text()

        assert "# S1" in full_text
        assert "Content 1" in full_text
        assert "# S2" in full_text
        assert "Content 2" in full_text

    def test_save_and_load(self, tmp_path):
        """测试保存和加载"""
        transcript_file = tmp_path / "transcript.json"
        transcript_file.write_bytes(b"{}")

        sections = [SummarySection(id="s1", title="S1", content="Content", order=1)]

        summary = SummaryResult(
            sections=sections,
            transcript_path=str(transcript_file),
            template_name="test",
            template_role="Test",
            llm_provider="mock",
            llm_model="mock"
        )

        # 保存
        output_path = tmp_path / "summary.json"
        saved_path = summary.save(str(output_path))

        assert Path(saved_path).exists()

        # 加载
        from summarizer.export import load_summary
        loaded = load_summary(saved_path)

        assert len(loaded.sections) == 1
        assert loaded.sections[0].title == "S1"

    def test_to_dict(self, tmp_path):
        """测试转换为字典"""
        transcript_file = tmp_path / "transcript.json"
        transcript_file.write_bytes(b"{}")

        summary = SummaryResult(
            sections=[SummarySection(id="s1", title="S1", content="C1", order=1)],
            transcript_path=str(transcript_file),
            template_name="test",
            template_role="Test",
            llm_provider="mock",
            llm_model="mock"
        )

        result = summary.to_dict()

        assert "metadata" in result
        assert "sections" in result
        assert "full_text" in result
        assert result["metadata"]["template_name"] == "test"

    def test_to_markdown(self, tmp_path):
        """测试转换为 Markdown"""
        transcript_file = tmp_path / "transcript.json"
        transcript_file.write_bytes(b"{}")

        summary = SummaryResult(
            sections=[
                SummarySection(id="s1", title="Section 1", content="Content", order=1)
            ],
            transcript_path=str(transcript_file),
            template_name="test",
            template_role="Test Role",
            llm_provider="mock",
            llm_model="mock"
        )

        md = summary.to_markdown()

        assert "# 会议总结 (Test Role)" in md
        assert "## Section 1" in md
        assert "Content" in md
