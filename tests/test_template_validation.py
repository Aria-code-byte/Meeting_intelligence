"""
Tests for template validation module.
"""

import pytest

from template.types import UserTemplate, TemplateSection, SummaryAngle
from template.validation import (
    validate_template,
    validate_template_dict,
    is_template_name_valid,
    normalize_template_name
)


class TestValidateTemplate:
    """validate_template 函数测试"""

    def test_valid_template(self):
        """测试有效模板验证"""
        template = UserTemplate(
            name="test",
            role="Test Role",
            angle=SummaryAngle.BALANCED,
            focus=["test"]
        )

        result = validate_template(template)
        assert result.is_valid is True
        assert len(result.errors) == 0

    # 注意：以下测试改用 validate_template_dict，
    # 因为 UserTemplate.__post_init__ 会提前抛出异常

    def test_warning_for_missing_title(self):
        """测试缺少标题产生警告"""
        template = UserTemplate(
            name="test",
            role="Test",
            angle=SummaryAngle.BALANCED,
            focus=["test"],
            sections=[
                TemplateSection(id="s1", title="", prompt="P1", order=1)
            ]
        )

        result = validate_template(template)
        # 应该有警告但不影响有效性
        assert result.is_valid is True
        assert len(result.warnings) > 0


class TestValidateTemplateDict:
    """validate_template_dict 函数测试"""

    def test_valid_dict(self):
        """测试有效字典"""
        data = {
            "name": "test",
            "role": "Test Role",
            "angle": "balanced",
            "focus": ["test"],
            "sections": []
        }

        result = validate_template_dict(data)
        assert result.is_valid is True

    def test_missing_required_field(self):
        """测试缺少必需字段"""
        data = {
            "name": "test",
            "role": "Test"
            # 缺少 angle 和 focus
        }

        result = validate_template_dict(data)
        assert result.is_valid is False
        assert len(result.errors) >= 2

    def test_missing_name_field(self):
        """测试缺少名称字段"""
        data = {
            "role": "Test",
            "angle": "balanced",
            "focus": ["test"]
        }

        result = validate_template_dict(data)
        assert result.is_valid is False
        assert any("name" in e.field for e in result.errors)

    def test_missing_role_field(self):
        """测试缺少角色字段"""
        data = {
            "name": "test",
            "angle": "balanced",
            "focus": ["test"]
        }

        result = validate_template_dict(data)
        assert result.is_valid is False
        assert any("role" in e.field for e in result.errors)

    def test_invalid_field_type(self):
        """测试无效的字段类型"""
        data = {
            "name": "test",
            "role": "Test",
            "angle": "balanced",
            "focus": "not-a-list"  # 应该是列表
        }

        result = validate_template_dict(data)
        assert result.is_valid is False
        assert any("focus" in e.field for e in result.errors)

    def test_empty_focus_list(self):
        """测试空关注点列表"""
        data = {
            "name": "test",
            "role": "Test",
            "angle": "balanced",
            "focus": []
        }

        result = validate_template_dict(data)
        # 空列表在 dict 验证中不报错（因为 list 是有效类型）
        # 但在实际创建 UserTemplate 时会报错
        assert result.is_valid is True

    def test_duplicate_section_ids_in_dict(self):
        """测试字典中重复的 section ID"""
        data = {
            "name": "test",
            "role": "Test",
            "angle": "balanced",
            "focus": ["test"],
            "sections": [
                {"id": "dup", "title": "First", "prompt": "P1", "order": 1},
                {"id": "dup", "title": "Second", "prompt": "P2", "order": 2}
            ]
        }

        result = validate_template_dict(data)
        assert result.is_valid is False
        assert any("dup" in e.message for e in result.errors)


class TestTemplateNameValidation:
    """模板名称验证测试"""

    def test_valid_names(self):
        """测试有效名称"""
        assert is_template_name_valid("test") is True
        assert is_template_name_valid("my-template") is True
        assert is_template_name_valid("my_template") is True
        assert is_template_name_valid("MyTemplate123") is True

    def test_invalid_names(self):
        """测试无效名称"""
        assert is_template_name_valid("") is False
        assert is_template_name_valid("with space") is False
        assert is_template_name_valid("with.dot") is False
        assert is_template_name_valid("with@symbol") is False

    def test_normalize_name(self):
        """测试名称标准化"""
        assert normalize_template_name("My Template") == "my-template"
        assert normalize_template_name("My_Template") == "my_template"
        assert normalize_template_name("My@Template#Name") == "mytemplatename"
        assert normalize_template_name("UPPERCASE") == "uppercase"
