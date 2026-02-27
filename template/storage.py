"""
Template storage.

提供模板的持久化存储功能。
"""

import json
from pathlib import Path
from typing import Union, List, Optional

from template.types import UserTemplate
from template.validation import validate_template


TEMPLATES_DIR = Path(__file__).parent.parent / "data" / "templates"


def _ensure_templates_dir() -> Path:
    """确保模板目录存在"""
    TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
    return TEMPLATES_DIR


def _get_template_path(name: str) -> Path:
    """
    获取模板文件路径

    Args:
        name: 模板名称

    Returns:
        模板文件路径
    """
    return _ensure_templates_dir() / f"{name}.json"


def save_template(template: UserTemplate, overwrite: bool = False) -> str:
    """
    保存模板到磁盘

    Args:
        template: UserTemplate 实例
        overwrite: 是否覆盖已存在的模板

    Returns:
        保存的文件路径

    Raises:
        ValueError: 如果模板已存在且 overwrite=False
        ValueError: 如果模板验证失败
    """
    # 验证模板
    validation = validate_template(template)
    if not validation.is_valid:
        errors = ", ".join([e.message for e in validation.errors])
        raise ValueError(f"模板验证失败: {errors}")

    # 获取文件路径
    output_path = _get_template_path(template.name)

    # 检查文件是否已存在
    if output_path.exists() and not overwrite:
        raise ValueError(
            f"模板已存在: {template.name}. "
            f"使用 overwrite=True 来覆盖。"
        )

    # 保存到文件
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(template.to_dict(), f, ensure_ascii=False, indent=2)

    return str(output_path)


def load_template(name: str) -> UserTemplate:
    """
    从磁盘加载模板

    Args:
        name: 模板名称

    Returns:
        UserTemplate 实例

    Raises:
        FileNotFoundError: 如果模板文件不存在
        ValueError: 如果模板格式无效
    """
    template_path = _get_template_path(name)

    if not template_path.exists():
        raise FileNotFoundError(f"模板不存在: {name}")

    # 读取文件
    try:
        with open(template_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"模板文件 JSON 格式无效: {e}") from e

    # 从字典创建模板
    try:
        template = UserTemplate.from_dict(data)
    except Exception as e:
        raise ValueError(f"无法从数据创建模板: {e}") from e

    return template


def template_exists(name: str) -> bool:
    """
    检查模板是否存在

    Args:
        name: 模板名称

    Returns:
        是否存在
    """
    return _get_template_path(name).exists()


def delete_template(name: str) -> bool:
    """
    删除模板

    Args:
        name: 模板名称

    Returns:
        是否成功删除

    Raises:
        ValueError: 如果是默认模板（不允许删除）
    """
    # 检查是否是默认模板
    from template.defaults import DEFAULT_TEMPLATES
    if name in DEFAULT_TEMPLATES:
        raise ValueError(f"不能删除默认模板: {name}")

    template_path = _get_template_path(name)

    if template_path.exists():
        template_path.unlink()
        return True

    return False


def list_templates() -> List[dict]:
    """
    列出所有可用的模板

    Returns:
        模板元数据列表
    """
    templates = []

    # 获取默认模板
    from template.defaults import get_all_default_templates
    default_templates = get_all_default_templates()

    # 创建默认模板名称集合
    default_names = {t.name for t in default_templates}

    # 添加默认模板
    for template in default_templates:
        templates.append({
            "name": template.name,
            "role": template.role,
            "description": template.description,
            "is_default": True,
            "exists_on_disk": template_exists(template.name)
        })

    # 扫描自定义模板
    for file_path in _ensure_templates_dir().glob("*.json"):
        name = file_path.stem

        # 跳过默认模板
        if name in default_names:
            continue

        try:
            template = load_template(name)
            templates.append({
                "name": template.name,
                "role": template.role,
                "description": template.description,
                "is_default": False,
                "exists_on_disk": True,
                "created_at": template.created_at,
                "updated_at": template.updated_at
            })
        except Exception:
            # 跳过无法加载的模板
            continue

    return templates


def initialize_default_templates() -> None:
    """
    初始化默认模板到磁盘

    如果默认模板不存在，则创建它们。
    不会覆盖已存在的自定义模板。
    """
    from template.defaults import get_all_default_templates

    for template in get_all_default_templates():
        try:
            save_template(template, overwrite=False)
        except ValueError:
            # 模板已存在，跳过
            pass


def get_template_metadata(name: str) -> Optional[dict]:
    """
    获取模板元数据（不加载完整模板）

    Args:
        name: 模板名称

    Returns:
        元数据字典，如果模板不存在则返回 None
    """
    # 检查是否是默认模板
    from template.defaults import DEFAULT_TEMPLATES
    if name in DEFAULT_TEMPLATES:
        template = DEFAULT_TEMPLATES[name]()
        return {
            "name": template.name,
            "role": template.role,
            "description": template.description,
            "is_default": True
        }

    # 检查自定义模板
    template_path = _get_template_path(name)
    if not template_path.exists():
        return None

    try:
        with open(template_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        return {
            "name": data.get("name"),
            "role": data.get("role"),
            "description": data.get("description"),
            "is_default": False,
            "created_at": data.get("created_at"),
            "updated_at": data.get("updated_at")
        }
    except Exception:
        return None
