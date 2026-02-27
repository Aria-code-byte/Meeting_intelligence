"""
Template module types.

定义用户模板系统的类型结构。
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum


class SummaryAngle(Enum):
    """总结角度枚举"""
    TOWARDS_CONCLUSIONS = "towards-conclusions"  # 偏向结论
    TOWARDS_PROCESS = "towards-process"  # 偏向过程
    TOWARDS_DECISIONS = "towards-decisions"  # 偏向决策
    TOWARDS_USER_IMPACT = "towards-user-impact"  # 偏向用户体验
    BALANCED = "balanced"  # 平衡


class OutputFormat(Enum):
    """输出格式枚举"""
    BULLET_POINTS = "bullet-points"
    PARAGRAPH = "paragraph"
    TABLE = "table"
    MIXED = "mixed"


@dataclass
class TemplateSection:
    """
    模板部分定义

    定义总结中的一个部分，包含标题和提示模板。
    """
    id: str
    title: str
    prompt: str
    required: bool = True
    max_length: Optional[int] = None
    format: OutputFormat = OutputFormat.BULLET_POINTS
    order: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "title": self.title,
            "prompt": self.prompt,
            "required": self.required,
            "max_length": self.max_length,
            "format": self.format.value,
            "order": self.order
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TemplateSection":
        """从字典创建"""
        return cls(
            id=data["id"],
            title=data["title"],
            prompt=data["prompt"],
            required=data.get("required", True),
            max_length=data.get("max_length"),
            format=OutputFormat(data.get("format", "bullet-points")),
            order=data.get("order", 0)
        )


@dataclass
class UserTemplate:
    """
    用户模板

    定义用户如何体验会议：角色定位、总结角度、关注重点。
    这是产品的"灵魂模块"。
    """
    name: str
    role: str
    angle: SummaryAngle
    focus: List[str]
    sections: List[TemplateSection] = field(default_factory=list)
    description: Optional[str] = None
    version: str = "1.0"
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    is_default: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """验证模板"""
        if not self.name:
            raise ValueError("模板名称不能为空")

        if not self.role:
            raise ValueError("角色定义不能为空")

        if not isinstance(self.angle, SummaryAngle):
            raise ValueError(f"无效的总结角度: {self.angle}")

        if not self.focus:
            raise ValueError("关注重点不能为空")

        if not isinstance(self.focus, list):
            raise ValueError("focus 必须是列表")

        # 验证 section ID 唯一性
        section_ids = [s.id for s in self.sections]
        if len(section_ids) != len(set(section_ids)):
            raise ValueError("Section ID 必须唯一")

        # 按 order 排序 sections
        self.sections.sort(key=lambda s: s.order)

        # 设置默认时间戳
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
        if self.updated_at is None:
            self.updated_at = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "role": self.role,
            "angle": self.angle.value,
            "focus": self.focus,
            "sections": [s.to_dict() for s in self.sections],
            "description": self.description,
            "version": self.version,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "is_default": self.is_default,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UserTemplate":
        """从字典创建"""
        # 处理 angle 枚举
        angle_value = data.get("angle", "balanced")
        if isinstance(angle_value, str):
            angle = SummaryAngle(angle_value)
        else:
            angle = angle_value

        # 处理 sections
        sections = [
            TemplateSection.from_dict(s) if isinstance(s, dict) else s
            for s in data.get("sections", [])
        ]

        return cls(
            name=data["name"],
            role=data["role"],
            angle=angle,
            focus=data.get("focus", []),
            sections=sections,
            description=data.get("description"),
            version=data.get("version", "1.0"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
            is_default=data.get("is_default", False),
            metadata=data.get("metadata", {})
        )

    def get_section(self, section_id: str) -> Optional[TemplateSection]:
        """获取指定部分"""
        for section in self.sections:
            if section.id == section_id:
                return section
        return None

    def add_section(self, section: TemplateSection) -> None:
        """添加部分"""
        # 检查 ID 是否已存在
        if self.get_section(section.id):
            raise ValueError(f"Section ID 已存在: {section.id}")

        self.sections.append(section)
        # 按顺序排序
        self.sections.sort(key=lambda s: s.order)

    def remove_section(self, section_id: str) -> bool:
        """移除部分"""
        for i, section in enumerate(self.sections):
            if section.id == section_id:
                self.sections.pop(i)
                return True
        return False

    def update_section(self, section_id: str, **kwargs) -> bool:
        """更新部分"""
        section = self.get_section(section_id)
        if section is None:
            return False

        for key, value in kwargs.items():
            if hasattr(section, key):
                setattr(section, key, value)
        return True

    def clone(self, new_name: str) -> "UserTemplate":
        """克隆模板"""
        import copy
        cloned = copy.deepcopy(self)
        cloned.name = new_name
        cloned.is_default = False
        cloned.created_at = datetime.now().isoformat()
        cloned.updated_at = datetime.now().isoformat()
        return cloned

    def __repr__(self) -> str:
        return (
            f"UserTemplate("
            f"name={self.name}, "
            f"role={self.role}, "
            f"angle={self.angle.value}, "
            f"focus={self.focus})"
        )
