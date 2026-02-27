"""
Tests for template defaults module.
"""

import pytest

from template.defaults import (
    get_product_manager_template,
    get_developer_template,
    get_designer_template,
    get_executive_template,
    get_general_template,
    get_default_template,
    list_default_templates,
    get_all_default_templates,
    DEFAULT_TEMPLATES
)
from template.types import SummaryAngle, OutputFormat


class TestDefaultTemplates:
    """默认模板测试"""

    def test_product_manager_template(self):
        """测试产品经理模板"""
        template = get_product_manager_template()

        assert template.name == "product-manager"
        assert template.role == "Product Manager"
        assert template.angle == SummaryAngle.TOWARDS_CONCLUSIONS
        assert "requirements" in template.focus
        assert "decisions" in template.focus
        assert "action-items" in template.focus
        assert template.is_default is True

        # 验证 sections
        section_ids = [s.id for s in template.sections]
        assert "summary" in section_ids
        assert "requirements" in section_ids
        assert "decisions" in section_ids
        assert "action-items" in section_ids

    def test_developer_template(self):
        """测试开发者模板"""
        template = get_developer_template()

        assert template.name == "developer"
        assert template.role == "Developer"
        assert template.angle == SummaryAngle.TOWARDS_PROCESS
        assert "technical-decisions" in template.focus
        assert "implementation" in template.focus
        assert template.is_default is True

    def test_designer_template(self):
        """测试设计师模板"""
        template = get_designer_template()

        assert template.name == "designer"
        assert template.role == "Designer"
        assert template.angle == SummaryAngle.TOWARDS_USER_IMPACT
        assert "ux" in template.focus
        assert "user-feedback" in template.focus
        assert template.is_default is True

    def test_executive_template(self):
        """测试高管模板"""
        template = get_executive_template()

        assert template.name == "executive"
        assert template.role == "Executive"
        assert template.angle == SummaryAngle.TOWARDS_DECISIONS
        assert "strategy" in template.focus
        assert "resources" in template.focus
        assert "timeline" in template.focus
        assert template.is_default is True

    def test_general_template(self):
        """测试通用模板"""
        template = get_general_template()

        assert template.name == "general"
        assert template.role == "General"
        assert template.angle == SummaryAngle.BALANCED
        assert "summary" in template.focus
        assert "key-points" in template.focus
        assert template.is_default is True

        # 通用模板应该有更少的 sections
        assert len(template.sections) == 3

    def test_all_default_templates_valid(self):
        """测试所有默认模板都有效"""
        for template_func in DEFAULT_TEMPLATES.values():
            template = template_func()
            # 验证模板可以正常创建
            assert template.name is not None
            assert template.role is not None
            assert template.angle is not None
            assert len(template.focus) > 0
            assert template.is_default is True


class TestGetDefaultTemplate:
    """get_default_template 函数测试"""

    def test_get_existing_template(self):
        """测试获取存在的模板"""
        template = get_default_template("general")
        assert template.name == "general"

    def test_get_nonexistent_template(self):
        """测试获取不存在的模板"""
        with pytest.raises(ValueError, match="默认模板不存在"):
            get_default_template("nonexistent")

    def test_error_message_shows_available(self):
        """测试错误消息包含可用模板"""
        try:
            get_default_template("wrong")
        except ValueError as e:
            assert "product-manager" in str(e)
            assert "developer" in str(e)
            assert "general" in str(e)


class TestListDefaultTemplates:
    """list_default_templates 函数测试"""

    def test_list_returns_all_names(self):
        """测试列出返回所有模板名称"""
        names = list_default_templates()

        assert len(names) == 5
        assert "product-manager" in names
        assert "developer" in names
        assert "designer" in names
        assert "executive" in names
        assert "general" in names


class TestGetAllDefaultTemplates:
    """get_all_default_templates 函数测试"""

    def test_get_all_returns_templates(self):
        """测试获取所有默认模板"""
        templates = get_all_default_templates()

        assert len(templates) == 5

        names = {t.name for t in templates}
        assert "product-manager" in names
        assert "developer" in names
        assert "designer" in names
        assert "executive" in names
        assert "general" in names

    def test_all_templates_are_valid(self):
        """测试所有返回的模板都有效"""
        templates = get_all_default_templates()

        for template in templates:
            assert isinstance(template.name, str)
            assert isinstance(template.role, str)
            assert isinstance(template.angle, SummaryAngle)
            assert isinstance(template.focus, list)
            assert template.is_default is True
