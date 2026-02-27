"""
Summarizer module types.

定义总结结果的数据结构。
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum


class SectionFormat(Enum):
    """部分格式枚举"""
    BULLET_POINTS = "bullet-points"
    PARAGRAPH = "paragraph"
    TABLE = "table"
    MIXED = "mixed"


@dataclass
class SummarySection:
    """
    总结部分

    包含总结中的一个部分的内容。
    """
    id: str
    title: str
    content: str
    format: SectionFormat = SectionFormat.BULLET_POINTS
    order: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "format": self.format.value,
            "order": self.order
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SummarySection":
        """从字典创建"""
        return cls(
            id=data["id"],
            title=data["title"],
            content=data["content"],
            format=SectionFormat(data.get("format", "bullet-points")),
            order=data.get("order", 0)
        )

    def is_empty(self) -> bool:
        """检查内容是否为空"""
        return not self.content or self.content.strip() == ""


@dataclass
class SummaryResult:
    """
    总结结果

    包含完整的结构化总结，按用户模板定义生成。
    """
    sections: List[SummarySection]
    transcript_path: str
    template_name: str
    template_role: str
    llm_provider: str
    llm_model: str
    created_at: Optional[str] = None
    processing_time: Optional[float] = None
    output_path: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """验证总结结果"""
        from pathlib import Path

        # 验证转录文档存在
        if not Path(self.transcript_path).exists():
            raise FileNotFoundError(f"转录文档不存在: {self.transcript_path}")

        # 设置默认时间戳
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()

        # 按 order 排序 sections
        self.sections.sort(key=lambda s: s.order)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "metadata": {
                "transcript_path": self.transcript_path,
                "template_name": self.template_name,
                "template_role": self.template_role,
                "llm_provider": self.llm_provider,
                "llm_model": self.llm_model,
                "created_at": self.created_at,
                "processing_time": self.processing_time
            },
            "sections": [s.to_dict() for s in self.sections],
            "full_text": self.get_full_text()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SummaryResult":
        """从字典创建"""
        metadata = data.get("metadata", {})

        sections = [
            SummarySection.from_dict(s) if isinstance(s, dict) else s
            for s in data.get("sections", [])
        ]

        return cls(
            sections=sections,
            transcript_path=metadata.get("transcript_path"),
            template_name=metadata.get("template_name"),
            template_role=metadata.get("template_role"),
            llm_provider=metadata.get("llm_provider"),
            llm_model=metadata.get("llm_model"),
            created_at=metadata.get("created_at"),
            processing_time=metadata.get("processing_time"),
            metadata=data.get("metadata", {})
        )

    def get_section(self, section_id: str) -> Optional[SummarySection]:
        """获取指定部分"""
        for section in self.sections:
            if section.id == section_id:
                return section
        return None

    def get_full_text(self) -> str:
        """获取完整文字内容"""
        lines = []
        for section in self.sections:
            lines.append(f"# {section.title}")
            lines.append(section.content)
            lines.append("")
        return "\n".join(lines)

    def save(self, path: Optional[str] = None) -> str:
        """
        保存总结到磁盘

        Args:
            path: 保存路径（可选，默认使用 data/summaries/）

        Returns:
            保存的文件路径
        """
        import json
        from pathlib import Path

        if path is None:
            # 生成默认文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_template = self.template_name.replace("-", "_")
            path = f"data/summaries/summary_{safe_template}_{timestamp}.json"

        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)

        self.output_path = str(output_path)
        return str(output_path)

    def to_markdown(self) -> str:
        """
        转换为 Markdown 格式

        Returns:
            Markdown 格式的字符串
        """
        lines = []

        # 标题
        lines.append(f"# 会议总结 ({self.template_role})")
        lines.append("")

        # 元数据
        lines.append("## 元数据")
        lines.append(f"- **模板**: {self.template_name}")
        lines.append(f"- **生成时间**: {self.created_at}")
        if self.processing_time:
            lines.append(f"- **处理时间**: {self.processing_time:.1f}秒")
        lines.append("")

        # 内容
        for section in self.sections:
            lines.append(f"## {section.title}")
            lines.append("")
            lines.append(section.content)
            lines.append("")

        return "\n".join(lines)

    def __repr__(self) -> str:
        return (
            f"SummaryResult("
            f"sections={len(self.sections)}, "
            f"template={self.template_name}, "
            f"provider={self.llm_provider})"
        )
