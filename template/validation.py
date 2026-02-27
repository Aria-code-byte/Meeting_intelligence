"""
Template validation.

提供模板验证功能，确保模板结构正确且可用。
"""

from typing import Dict, List, Any
from template.types import UserTemplate, TemplateSection, SummaryAngle


class ValidationError:
    """验证错误"""
    def __init__(self, field: str, message: str, is_warning: bool = False):
        self.field = field
        self.message = message
        self.is_warning = is_warning

    def to_dict(self) -> Dict[str, Any]:
        return {
            "field": self.field,
            "message": self.message,
            "is_warning": self.is_warning
        }


class ValidationResult:
    """验证结果"""
    def __init__(self):
        self.errors: List[ValidationError] = []
        self.warnings: List[ValidationError] = []

    def add_error(self, field: str, message: str) -> None:
        """添加错误"""
        self.errors.append(ValidationError(field, message, False))

    def add_warning(self, field: str, message: str) -> None:
        """添加警告"""
        self.warnings.append(ValidationError(field, message, True))

    @property
    def is_valid(self) -> bool:
        """是否有效（无错误）"""
        return len(self.errors) == 0

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "valid": self.is_valid,
            "errors": [e.to_dict() for e in self.errors],
            "warnings": [e.to_dict() for e in self.warnings]
        }


def validate_template(template: UserTemplate) -> ValidationResult:
    """
    验证用户模板

    Args:
        template: UserTemplate 实例

    Returns:
        ValidationResult 实例
    """
    result = ValidationResult()

    # 验证必需字段
    if not template.name:
        result.add_error("name", "模板名称不能为空")

    if not template.role:
        result.add_error("role", "角色定义不能为空")

    # 验证 angle
    if not isinstance(template.angle, SummaryAngle):
        try:
            # 尝试从字符串创建
            if isinstance(template.angle, str):
                SummaryAngle(template.angle)
            else:
                result.add_error("angle", f"无效的总结角度类型: {type(template.angle)}")
        except ValueError:
            result.add_error("angle", f"无效的总结角度: {template.angle}")

    # 验证 focus
    if not template.focus:
        result.add_error("focus", "关注重点不能为空")
    elif not isinstance(template.focus, list):
        result.add_error("focus", "focus 必须是列表")
    elif not all(isinstance(f, str) for f in template.focus):
        result.add_error("focus", "focus 中的每个元素必须是字符串")

    # 验证 sections
    section_ids = []
    for i, section in enumerate(template.sections):
        section_index = f"sections[{i}]"

        if not isinstance(section, TemplateSection):
            result.add_error(section_index, f"无效的 section 类型: {type(section)}")
            continue

        # 验证 section 字段
        if not section.id:
            result.add_error(f"{section_index}.id", "Section ID 不能为空")

        if not section.title:
            result.add_warning(f"{section_index}.title", "Section 建议有标题")

        if not section.prompt:
            result.add_warning(f"{section_index}.prompt", "Section 建议有提示模板")

        # 检查 ID 唯一性
        if section.id in section_ids:
            result.add_error(f"{section_index}.id", f"重复的 Section ID: {section.id}")
        else:
            section_ids.append(section.id)

        # 检查 order
        if section.order < 0:
            result.add_error(f"{section_index}.order", "Section order 不能为负数")

    # 验证 metadata
    if template.metadata and not isinstance(template.metadata, dict):
        result.add_error("metadata", "metadata 必须是字典")

    return result


def validate_template_dict(data: Dict[str, Any]) -> ValidationResult:
    """
    验证模板字典数据

    Args:
        data: 模板字典

    Returns:
        ValidationResult 实例
    """
    result = ValidationResult()

    # 验证必需字段存在
    required_fields = ["name", "role", "angle", "focus"]
    for field in required_fields:
        if field not in data:
            result.add_error(field, f"缺少必需字段: {field}")

    # 验证字段类型
    if "name" in data and not isinstance(data["name"], str):
        result.add_error("name", "name 必须是字符串")

    if "role" in data and not isinstance(data["role"], str):
        result.add_error("role", "role 必须是字符串")

    if "focus" in data and not isinstance(data["focus"], list):
        result.add_error("focus", "focus 必须是列表")

    if "sections" in data and not isinstance(data["sections"], list):
        result.add_error("sections", "sections 必须是列表")

    # 验证 sections 结构
    if "sections" in data and isinstance(data["sections"], list):
        section_ids = []
        for i, section in enumerate(data["sections"]):
            if not isinstance(section, dict):
                result.add_error(f"sections[{i}]", "section 必须是字典")
                continue

            section_index = f"sections[{i}]"

            if "id" not in section:
                result.add_error(f"{section_index}.id", "section 缺少 id 字段")

            if "id" in section:
                if section["id"] in section_ids:
                    result.add_error(f"{section_index}.id", f"重复的 Section ID: {section['id']}")
                else:
                    section_ids.append(section["id"])

    return result


def is_template_name_valid(name: str) -> bool:
    """
    检查模板名称是否有效

    Args:
        name: 模板名称

    Returns:
        是否有效
    """
    if not name:
        return False

    # 只允许字母、数字、连字符和下划线
    import re
    pattern = r'^[a-zA-Z0-9\-_]+$'
    return bool(re.match(pattern, name))


def normalize_template_name(name: str) -> str:
    """
    标准化模板名称（转换为小写并替换空格）

    Args:
        name: 原始名称

    Returns:
        标准化后的名称
    """
    # 转换为小写
    name = name.lower()
    # 替换空格为连字符
    name = name.replace(" ", "-")
    # 移除特殊字符
    import re
    name = re.sub(r'[^a-zA-Z0-9\-_]', '', name)
    return name
