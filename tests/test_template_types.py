"""
Tests for template module types.
"""

import pytest

from template.types import UserTemplate, TemplateSection, SummaryAngle, OutputFormat


class TestSummaryAngle:
    """SummaryAngle 枚举测试"""

    def test_angle_values(self):
        """测试角度枚举值"""
        assert SummaryAngle.TOWARDS_CONCLUSIONS.value == "towards-conclusions"
        assert SummaryAngle.TOWARDS_PROCESS.value == "towards-process"
        assert SummaryAngle.TOWARDS_DECISIONS.value == "towards-decisions"
        assert SummaryAngle.TOWARDS_USER_IMPACT.value == "towards-user-impact"
        assert SummaryAngle.BALANCED.value == "balanced"


class TestOutputFormat:
    """OutputFormat 枚举测试"""

    def test_format_values(self):
        """测试格式枚举值"""
        assert OutputFormat.BULLET_POINTS.value == "bullet-points"
        assert OutputFormat.PARAGRAPH.value == "paragraph"
        assert OutputFormat.TABLE.value == "table"
        assert OutputFormat.MIXED.value == "mixed"


class TestTemplateSection:
    """TemplateSection 类测试"""

    def test_section_creation(self):
        """测试部分创建"""
        section = TemplateSection(
            id="summary",
            title="会议总结",
            prompt="请总结会议内容"
        )

        assert section.id == "summary"
        assert section.title == "会议总结"
        assert section.prompt == "请总结会议内容"
        assert section.required is True
        assert section.max_length is None
        assert section.format == OutputFormat.BULLET_POINTS
        assert section.order == 0

    def test_section_with_options(self):
        """测试带选项的部分创建"""
        section = TemplateSection(
            id="decisions",
            title="决策",
            prompt="列出决策",
            required=False,
            max_length=500,
            format=OutputFormat.TABLE,
            order=2
        )

        assert section.required is False
        assert section.max_length == 500
        assert section.format == OutputFormat.TABLE
        assert section.order == 2

    def test_section_to_dict(self):
        """测试部分转换为字典"""
        section = TemplateSection(
            id="test",
            title="Test",
            prompt="Test prompt"
        )

        result = section.to_dict()

        assert result["id"] == "test"
        assert result["title"] == "Test"
        assert result["prompt"] == "Test prompt"
        assert result["required"] is True
        assert result["format"] == "bullet-points"

    def test_section_from_dict(self):
        """测试从字典创建部分"""
        data = {
            "id": "test",
            "title": "Test",
            "prompt": "Test prompt",
            "required": False,
            "max_length": 200,
            "format": "paragraph",
            "order": 5
        }

        section = TemplateSection.from_dict(data)

        assert section.id == "test"
        assert section.title == "Test"
        assert section.prompt == "Test prompt"
        assert section.required is False
        assert section.max_length == 200
        assert section.format == OutputFormat.PARAGRAPH
        assert section.order == 5


class TestUserTemplate:
    """UserTemplate 类测试"""

    def test_template_creation_minimal(self):
        """测试最小模板创建"""
        template = UserTemplate(
            name="test",
            role="Test Role",
            angle=SummaryAngle.BALANCED,
            focus=["summary"]
        )

        assert template.name == "test"
        assert template.role == "Test Role"
        assert template.angle == SummaryAngle.BALANCED
        assert template.focus == ["summary"]
        assert template.sections == []
        assert template.is_default is False
        assert template.created_at is not None
        assert template.updated_at is not None

    def test_template_with_sections(self):
        """测试带部分的模板创建"""
        sections = [
            TemplateSection(id="s1", title="Section 1", prompt="Prompt 1", order=1),
            TemplateSection(id="s2", title="Section 2", prompt="Prompt 2", order=2)
        ]

        template = UserTemplate(
            name="test",
            role="Test",
            angle=SummaryAngle.BALANCED,
            focus=["test"],
            sections=sections
        )

        assert len(template.sections) == 2

    def test_template_validation_empty_name(self):
        """测试空名称验证"""
        with pytest.raises(ValueError, match="模板名称不能为空"):
            UserTemplate(
                name="",
                role="Test",
                angle=SummaryAngle.BALANCED,
                focus=["test"]
            )

    def test_template_validation_empty_role(self):
        """测试空角色验证"""
        with pytest.raises(ValueError, match="角色定义不能为空"):
            UserTemplate(
                name="test",
                role="",
                angle=SummaryAngle.BALANCED,
                focus=["test"]
            )

    def test_template_validation_empty_focus(self):
        """测试空关注点验证"""
        with pytest.raises(ValueError, match="关注重点不能为空"):
            UserTemplate(
                name="test",
                role="Test",
                angle=SummaryAngle.BALANCED,
                focus=[]
            )

    def test_template_validation_duplicate_section_ids(self):
        """测试重复 section ID 验证"""
        sections = [
            TemplateSection(id="dup", title="First", prompt="P1", order=1),
            TemplateSection(id="dup", title="Second", prompt="P2", order=2)
        ]

        with pytest.raises(ValueError, match="Section ID 必须唯一"):
            UserTemplate(
                name="test",
                role="Test",
                angle=SummaryAngle.BALANCED,
                focus=["test"],
                sections=sections
            )

    def test_template_to_dict(self):
        """测试模板转换为字典"""
        template = UserTemplate(
            name="test",
            role="Test Role",
            angle=SummaryAngle.TOWARDS_CONCLUSIONS,
            focus=["decision", "action"]
        )

        result = template.to_dict()

        assert result["name"] == "test"
        assert result["role"] == "Test Role"
        assert result["angle"] == "towards-conclusions"
        assert result["focus"] == ["decision", "action"]
        assert "sections" in result
        assert "metadata" in result

    def test_template_from_dict(self):
        """测试从字典创建模板"""
        data = {
            "name": "test",
            "role": "Test Role",
            "angle": "towards-process",
            "focus": ["tech", "implementation"],
            "sections": [],
            "description": "Test template",
            "version": "2.0"
        }

        template = UserTemplate.from_dict(data)

        assert template.name == "test"
        assert template.role == "Test Role"
        assert template.angle == SummaryAngle.TOWARDS_PROCESS
        assert template.focus == ["tech", "implementation"]
        assert template.description == "Test template"
        assert template.version == "2.0"

    def test_get_section(self):
        """测试获取部分"""
        sections = [
            TemplateSection(id="s1", title="S1", prompt="P1", order=1),
            TemplateSection(id="s2", title="S2", prompt="P2", order=2)
        ]

        template = UserTemplate(
            name="test",
            role="Test",
            angle=SummaryAngle.BALANCED,
            focus=["test"],
            sections=sections
        )

        section = template.get_section("s2")
        assert section is not None
        assert section.title == "S2"

        section = template.get_section("nonexistent")
        assert section is None

    def test_add_section(self):
        """测试添加部分"""
        template = UserTemplate(
            name="test",
            role="Test",
            angle=SummaryAngle.BALANCED,
            focus=["test"]
        )

        section = TemplateSection(id="new", title="New", prompt="Prompt", order=1)
        template.add_section(section)

        assert len(template.sections) == 1
        assert template.sections[0].id == "new"

    def test_add_duplicate_section_id(self):
        """测试添加重复 ID"""
        template = UserTemplate(
            name="test",
            role="Test",
            angle=SummaryAngle.BALANCED,
            focus=["test"],
            sections=[TemplateSection(id="dup", title="Dup", prompt="P", order=1)]
        )

        new_section = TemplateSection(id="dup", title="Another", prompt="P2", order=2)

        with pytest.raises(ValueError, match="Section ID 已存在"):
            template.add_section(new_section)

    def test_remove_section(self):
        """测试移除部分"""
        sections = [
            TemplateSection(id="s1", title="S1", prompt="P1", order=1),
            TemplateSection(id="s2", title="S2", prompt="P2", order=2)
        ]

        template = UserTemplate(
            name="test",
            role="Test",
            angle=SummaryAngle.BALANCED,
            focus=["test"],
            sections=sections
        )

        result = template.remove_section("s1")
        assert result is True
        assert len(template.sections) == 1
        assert template.sections[0].id == "s2"

        result = template.remove_section("nonexistent")
        assert result is False

    def test_update_section(self):
        """测试更新部分"""
        section = TemplateSection(id="s1", title="Old", prompt="Old prompt", order=1)
        template = UserTemplate(
            name="test",
            role="Test",
            angle=SummaryAngle.BALANCED,
            focus=["test"],
            sections=[section]
        )

        result = template.update_section("s1", title="New Title")
        assert result is True
        assert template.sections[0].title == "New Title"

        result = template.update_section("nonexistent", title="No effect")
        assert result is False

    def test_clone(self):
        """测试克隆模板"""
        original = UserTemplate(
            name="original",
            role="Original Role",
            angle=SummaryAngle.BALANCED,
            focus=["test"],
            is_default=True
        )

        cloned = original.clone("cloned")

        assert cloned.name == "cloned"
        assert cloned.role == "Original Role"
        assert cloned.is_default is False
        assert cloned.created_at != original.created_at

    def test_section_ordering(self):
        """测试部分排序"""
        # 使用不同的 ID 避免验证失败
        sections = [
            TemplateSection(id="section3", title="S3", prompt="P3", order=3),
            TemplateSection(id="section1", title="S1", prompt="P1", order=1),
            TemplateSection(id="section2", title="S2", prompt="P2", order=2)
        ]

        template = UserTemplate(
            name="test",
            role="Test",
            angle=SummaryAngle.BALANCED,
            focus=["test"],
            sections=sections
        )

        assert template.sections[0].id == "section1"
        assert template.sections[1].id == "section2"
        assert template.sections[2].id == "section3"
