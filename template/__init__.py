"""
Template module - 用户模板系统

定义用户如何体验会议：角色定位、总结角度、关注重点。
这是产品的"灵魂模块"。
"""

from template.types import UserTemplate, TemplateSection, SummaryAngle, OutputFormat
from template.defaults import (
    get_default_template,
    list_default_templates,
    get_all_default_templates
)
from template.storage import (
    save_template,
    load_template,
    delete_template,
    list_templates,
    template_exists,
    initialize_default_templates
)
from template.manager import TemplateManager, get_template_manager
from template.render import (
    render_template_to_prompt,
    render_section_prompt,
    render_all_sections,
    create_system_prompt,
    create_user_prompt
)

__all__ = [
    # Types
    "UserTemplate",
    "TemplateSection",
    "SummaryAngle",
    "OutputFormat",
    # Defaults
    "get_default_template",
    "list_default_templates",
    "get_all_default_templates",
    # Storage
    "save_template",
    "load_template",
    "delete_template",
    "list_templates",
    "template_exists",
    "initialize_default_templates",
    # Manager
    "TemplateManager",
    "get_template_manager",
    # Render
    "render_template_to_prompt",
    "render_section_prompt",
    "render_all_sections",
    "create_system_prompt",
    "create_user_prompt",
]
