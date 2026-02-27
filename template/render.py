"""
Template rendering.

将模板转换为 LLM 可用的提示词。
"""

from typing import Dict, Any, Optional, List
from datetime import timedelta

from template.types import UserTemplate, TemplateSection, OutputFormat


def render_template_to_prompt(
    template: UserTemplate,
    transcript_context: Optional[Dict[str, Any]] = None
) -> str:
    """
    将模板渲染为 LLM 提示词

    Args:
        template: UserTemplate 实例
        transcript_context: 转录文档上下文（可选）

    Returns:
        渲染后的提示词字符串
    """
    lines = []

    # 系统角色定义
    lines.append("# 角色定义")
    lines.append(f"你是一位{template.role}。")
    lines.append("")

    # 总结角度说明
    lines.append("# 总结角度")
    angle_descriptions = {
        "towards-conclusions": "偏向结论型总结，重点提炼会议的核心结论和决策",
        "towards-process": "偏向过程型总结，详细记录讨论的过程和思路",
        "towards-decisions": "偏向决策型总结，突出会议中做出的各项决策",
        "towards-user-impact": "偏向用户体验型总结，关注对用户的影响",
        "balanced": "平衡型总结，兼顾过程和结论"
    }
    angle_desc = angle_descriptions.get(
        template.angle.value,
        "自定义总结角度"
    )
    lines.append(f"本次总结采用「{angle_desc}」的角度。")
    lines.append("")

    # 关注重点
    lines.append("# 关注重点")
    focus_list = "、".join(template.focus)
    lines.append(f"请重点关注：{focus_list}")
    lines.append("")

    # 转录上下文
    if transcript_context:
        lines.append("# 会议信息")
        if "duration" in transcript_context:
            duration = transcript_context["duration"]
            if isinstance(duration, (int, float)):
                duration_str = format_duration(duration)
                lines.append(f"- 会议时长：{duration_str}")
        if "participant_count" in transcript_context:
            lines.append(f"- 参与人数：{transcript_context['participant_count']}人")
        lines.append("")

    # 输出结构
    if template.sections:
        lines.append("# 输出结构")
        lines.append("请按以下结构输出总结：")
        lines.append("")

        for section in sorted(template.sections, key=lambda s: s.order):
            lines.append(f"## {section.order}. {section.title}")
            lines.append(f"{section.prompt}")

            # 添加格式说明
            format_hints = {
                OutputFormat.BULLET_POINTS: "（使用项目符号列表）",
                OutputFormat.PARAGRAPH: "（使用段落形式）",
                OutputFormat.TABLE: "（使用表格形式）",
                OutputFormat.MIXED: "（使用混合形式）"
            }
            format_hint = format_hints.get(section.format, "")
            if format_hint:
                lines.append(format_hint)

            if section.max_length:
                lines.append(f"（最多{section.max_length}字）")

            lines.append("")

    # 组装提示词
    prompt = "\n".join(lines)

    return prompt


def render_section_prompt(
    section: TemplateSection,
    context: Optional[Dict[str, Any]] = None
) -> str:
    """
    渲染单个部分的提示词

    Args:
        section: TemplateSection 实例
        context: 上下文变量（可选）

    Returns:
        渲染后的提示词
    """
    prompt = section.prompt

    # 替换占位符
    if context:
        for key, value in context.items():
            placeholder = "{" + key + "}"
            if placeholder in prompt:
                prompt = prompt.replace(placeholder, str(value))

    return prompt


def render_all_sections(
    template: UserTemplate,
    context: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    渲染所有部分的提示词

    Args:
        template: UserTemplate 实例
        context: 上下文变量（可选）

    Returns:
        渲染后的部分列表，每个包含 id, title, prompt, format 等信息
    """
    sections = []

    for section in sorted(template.sections, key=lambda s: s.order):
        sections.append({
            "id": section.id,
            "title": section.title,
            "prompt": render_section_prompt(section, context),
            "required": section.required,
            "max_length": section.max_length,
            "format": section.format.value,
            "order": section.order
        })

    return sections


def format_duration(seconds: float) -> str:
    """
    格式化时长为人类可读格式

    Args:
        seconds: 时长（秒）

    Returns:
        格式化的时长字符串
    """
    duration = timedelta(seconds=int(seconds))
    hours, remainder = divmod(duration.seconds, 3600)
    minutes, _ = divmod(remainder, 60)

    if duration.days > 0:
        return f"{duration.days}天{hours}小时{minutes}分钟"
    elif hours > 0:
        return f"{hours}小时{minutes}分钟"
    else:
        return f"{minutes}分钟"


def build_render_context(
    transcript_doc=None,
    additional_info: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    构建渲染上下文

    Args:
        transcript_doc: 转录文档实例（可选）
        additional_info: 额外信息（可选）

    Returns:
        渲染上下文字典
    """
    context = {}

    if transcript_doc:
        context["duration"] = transcript_doc.duration
        context["utterance_count"] = transcript_doc.utterance_count

        # 获取统计信息
        from transcript.build import get_transcript_stats
        stats = get_transcript_stats(transcript_doc)
        context["total_words"] = stats["total_words"]
        context["speaking_time"] = stats["speaking_time_formatted"]

    if additional_info:
        context.update(additional_info)

    return context


def create_system_prompt(template: UserTemplate) -> str:
    """
    创建系统提示词（不包含具体的转录内容）

    Args:
        template: UserTemplate 实例

    Returns:
        系统提示词字符串
    """
    lines = []

    lines.append(f"你是{template.role}。")
    lines.append("")

    angle_instructions = {
        "towards-conclusions": "重点提炼会议的核心结论和决策，简明扼要。",
        "towards-process": "详细记录讨论的过程、思路和关键对话。",
        "towards-decisions": "突出会议中做出的各项决策及其背景。",
        "towards-user-impact": "关注讨论内容对用户体验的影响。",
        "balanced": "平衡记录过程和结论，兼顾细节和要点。"
    }

    lines.append(angle_instructions.get(
        template.angle.value,
        "根据用户模板生成总结。"
    ))
    lines.append("")

    focus_str = "、".join(template.focus)
    lines.append(f"重点关注：{focus_str}")
    lines.append("")

    return "\n".join(lines)


def create_user_prompt(
    template: UserTemplate,
    transcript_text: str,
    context: Optional[Dict[str, Any]] = None
) -> str:
    """
    创建用户提示词（包含具体的转录内容）

    Args:
        template: UserTemplate 实例
        transcript_text: 转录文本
        context: 额外上下文（可选）

    Returns:
        用户提示词字符串
    """
    lines = []

    lines.append("# 会议转录内容")
    lines.append(transcript_text)
    lines.append("")

    lines.append("# 请根据上述转录内容生成总结")
    lines.append("")

    if template.sections:
        lines.append("请按以下结构组织总结：")
        lines.append("")
        for section in sorted(template.sections, key=lambda s: s.order):
            req_marker = "（必需）" if section.required else "（可选）"
            lines.append(f"{section.order}. **{section.title}** {req_marker}")
            lines.append(f"   {section.prompt}")
            lines.append("")

    # 添加上下文信息
    if context:
        lines.append("# 补充信息")
        for key, value in context.items():
            lines.append(f"- {key}: {value}")
        lines.append("")

    return "\n".join(lines)
