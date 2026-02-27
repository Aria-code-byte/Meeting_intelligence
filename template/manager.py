"""
Template manager.

提供模板的统一管理接口。
"""

from typing import List, Optional, Dict, Any
from pathlib import Path

from template.types import UserTemplate
from template.storage import (
    save_template,
    load_template,
    delete_template,
    list_templates,
    template_exists,
    initialize_default_templates,
    get_template_metadata
)
from template.defaults import get_default_template, get_all_default_templates


class TemplateManager:
    """
    模板管理器

    提供统一的模板管理接口，包括获取、创建、更新、删除模板。
    """

    def __init__(self, auto_init: bool = True):
        """
        初始化模板管理器

        Args:
            auto_init: 是否自动初始化默认模板
        """
        if auto_init:
            self._ensure_defaults_initialized()

    def _ensure_defaults_initialized(self) -> None:
        """确保默认模板已初始化"""
        initialize_default_templates()

    def get_template(self, name: str) -> UserTemplate:
        """
        获取指定名称的模板

        Args:
            name: 模板名称

        Returns:
            UserTemplate 实例

        Raises:
            FileNotFoundError: 如果模板不存在
        """
        # 首先尝试从磁盘加载（包括默认模板和自定义模板）
        try:
            return load_template(name)
        except FileNotFoundError:
            # 如果磁盘上不存在，尝试从默认模板获取
            try:
                return get_default_template(name)
            except ValueError:
                raise FileNotFoundError(f"模板不存在: {name}")

    def get_or_default(self, name: Optional[str] = None) -> UserTemplate:
        """
        获取模板，如果未指定则返回默认模板

        Args:
            name: 模板名称（可选）

        Returns:
            UserTemplate 实例
        """
        if name is None:
            name = "general"

        return self.get_template(name)

    def list_templates(self, include_defaults: bool = True) -> List[Dict[str, Any]]:
        """
        列出所有可用模板

        Args:
            include_defaults: 是否包含默认模板

        Returns:
            模板元数据列表
        """
        all_templates = list_templates()

        if include_defaults:
            return all_templates
        else:
            return [t for t in all_templates if not t.get("is_default", False)]

    def create_template(
        self,
        name: str,
        role: str,
        angle: str,
        focus: List[str],
        description: Optional[str] = None,
        sections: Optional[List] = None
    ) -> UserTemplate:
        """
        创建新的自定义模板

        Args:
            name: 模板名称
            role: 角色定义
            angle: 总结角度
            focus: 关注重点列表
            description: 模板描述
            sections: 自定义部分列表

        Returns:
            创建的 UserTemplate 实例

        Raises:
            ValueError: 如果模板已存在或参数无效
        """
        from template.types import SummaryAngle

        # 检查名称是否已存在
        if template_exists(name):
            raise ValueError(f"模板已存在: {name}")

        # 创建模板
        template = UserTemplate(
            name=name,
            role=role,
            angle=SummaryAngle(angle),
            focus=focus,
            sections=sections or [],
            description=description,
            is_default=False
        )

        # 保存模板
        save_template(template, overwrite=False)

        return template

    def update_template(self, name: str, **kwargs) -> UserTemplate:
        """
        更新现有模板

        Args:
            name: 模板名称
            **kwargs: 要更新的字段

        Returns:
            更新后的 UserTemplate 实例

        Raises:
            FileNotFoundError: 如果模板不存在
            ValueError: 如果是默认模板或更新无效
        """
        from template.defaults import DEFAULT_TEMPLATES

        # 不允许直接修改默认模板
        if name in DEFAULT_TEMPLATES:
            raise ValueError(
                f"不能直接修改默认模板: {name}. "
                f"请克隆模板后进行修改。"
            )

        # 加载现有模板
        template = load_template(name)

        # 更新字段
        for key, value in kwargs.items():
            if key == "angle":
                from template.types import SummaryAngle
                value = SummaryAngle(value)

            if hasattr(template, key):
                setattr(template, key, value)

        # 更新时间戳
        from datetime import datetime
        template.updated_at = datetime.now().isoformat()

        # 保存更新后的模板
        save_template(template, overwrite=True)

        return template

    def delete_template(self, name: str) -> bool:
        """
        删除模板

        Args:
            name: 模板名称

        Returns:
            是否成功删除

        Raises:
            ValueError: 如果是默认模板
        """
        return delete_template(name)

    def clone_template(self, source_name: str, new_name: str) -> UserTemplate:
        """
        克隆模板

        Args:
            source_name: 源模板名称
            new_name: 新模板名称

        Returns:
            克隆的 UserTemplate 实例

        Raises:
            FileNotFoundError: 如果源模板不存在
            ValueError: 如果新名称已存在
        """
        # 加载源模板
        source = self.get_template(source_name)

        # 检查新名称是否已存在
        if template_exists(new_name):
            raise ValueError(f"模板已存在: {new_name}")

        # 克隆模板
        cloned = source.clone(new_name)

        # 保存克隆的模板
        save_template(cloned, overwrite=False)

        return cloned

    def get_default_template_names(self) -> List[str]:
        """
        获取所有默认模板的名称

        Returns:
            模板名称列表
        """
        from template.defaults import list_default_templates
        return list_default_templates()

    def search_templates(
        self,
        keyword: Optional[str] = None,
        role: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        搜索模板

        Args:
            keyword: 关键词（搜索名称、角色、描述）
            role: 角色过滤

        Returns:
            匹配的模板元数据列表
        """
        templates = self.list_templates()

        results = []
        for template in templates:
            # 角色过滤
            if role is not None:
                if template.get("role", "").lower() != role.lower():
                    continue

            # 关键词搜索
            if keyword is not None:
                keyword_lower = keyword.lower()
                searchable_text = (
                    template.get("name", "") + " " +
                    template.get("role", "") + " " +
                    template.get("description", "")
                ).lower()

                if keyword_lower not in searchable_text:
                    continue

            results.append(template)

        return results


# 全局单例
_default_manager: Optional[TemplateManager] = None


def get_template_manager() -> TemplateManager:
    """
    获取全局模板管理器实例

    Returns:
        TemplateManager 实例
    """
    global _default_manager

    if _default_manager is None:
        _default_manager = TemplateManager()

    return _default_manager
