"""
Summary generation.

整合转录文档和用户模板，生成结构化总结。
"""

import time
from typing import Optional, Union
from pathlib import Path

from transcript.types import TranscriptDocument
from template.types import UserTemplate
from template.render import create_system_prompt, create_user_prompt
from summarizer.types import SummaryResult, SummarySection, SectionFormat
from summarizer.llm import BaseLLMProvider, MockLLMProvider, OpenAIProvider


def generate_summary(
    transcript: Union[TranscriptDocument, str],
    template: Union[UserTemplate, str],
    llm_provider: Optional[BaseLLMProvider] = None,
    save: bool = True,
    output_path: Optional[str] = None
) -> SummaryResult:
    """
    生成结构化总结

    Args:
        transcript: 转录文档对象或文件路径
        template: 用户模板对象或模板名称
        llm_provider: LLM 提供商（可选，默认使用 Mock）
        save: 是否保存到磁盘
        output_path: 输出文件路径（可选）

    Returns:
        SummaryResult 实例

    Raises:
        FileNotFoundError: 如果转录文档不存在
        ValueError: 如果模板无效
        RuntimeError: 如果 LLM 生成失败
    """
    start_time = time.time()

    # 加载转录文档
    if isinstance(transcript, str):
        from transcript.load import load_transcript
        transcript_doc = load_transcript(transcript)
    else:
        transcript_doc = transcript

    # 加载模板
    if isinstance(template, str):
        from template.manager import get_template_manager
        manager = get_template_manager()
        template_obj = manager.get_template(template)
    else:
        template_obj = template

    # 使用 Mock provider 作为默认
    if llm_provider is None:
        llm_provider = MockLLMProvider()

    # 获取转录文本
    transcript_text = transcript_doc.get_full_text()

    # 构建渲染上下文
    from template.render import build_render_context
    context = build_render_context(transcript_doc)

    # 生成系统提示词和用户提示词
    system_prompt = create_system_prompt(template_obj)
    user_prompt = create_user_prompt(template_obj, transcript_text, context)

    # 调用 LLM 生成总结
    response = llm_provider.chat(
        system_prompt=system_prompt,
        user_prompt=user_prompt
    )

    # 解析响应为 sections
    sections = _parse_summary_response(response.content, template_obj)

    # 创建总结结果
    processing_time = time.time() - start_time

    summary = SummaryResult(
        sections=sections,
        transcript_path=transcript_doc.document_path or str(transcript),
        template_name=template_obj.name,
        template_role=template_obj.role,
        llm_provider=llm_provider.name,
        llm_model=llm_provider.model,
        processing_time=processing_time
    )

    # 保存到磁盘
    if save:
        summary.save(output_path)

    return summary


def _parse_summary_response(
    response: str,
    template: UserTemplate
) -> list:
    """
    解析 LLM 响应为 sections（增强版）

    支持多种标题格式：
    - ## 标题
    - ### 标题
    - **标题**
    - 1. 标题
    - 标题:

    Args:
        response: LLM 返回的文本
        template: 用户模板

    Returns:
        SummarySection 列表
    """
    import re

    # 首先尝试多种分割模式
    sections = _try_parse_with_patterns(response)

    if sections:
        # 尝试匹配模板中的 section
        sections = _match_sections_to_template(sections, template)
        return sections

    # 兜底策略1：使用模板结构
    if template.sections:
        return _fallback_use_template(response, template)

    # 兜底策略2：创建默认 section
    return [_create_default_section(response)]


def _try_parse_with_patterns(response: str) -> list:
    """
    尝试使用多种模式解析响应

    Returns:
        解析出的 sections 列表，失败返回空列表
    """
    patterns = [
        (r'\n##\s+', '##'),
        (r'\n###\s+', '###'),
        (r'\n\*\*([^*]+)\*\*\s*\n', '**bold**'),
        (r'\n(\d+)\.\s+\*\*([^*]+)\*\*', 'numbered-bold'),
        (r'\n(\d+)\.\s+', 'numbered'),
        (r'\n([一二三四五六七八九十]+)[、.]\s*', 'chinese-numbered'),
    ]

    for pattern, pattern_name in patterns:
        sections = _parse_with_pattern(response, pattern)
        if sections and len(sections) > 1:
            return sections

    return []


def _parse_with_pattern(response: str, pattern: str) -> list:
    """
    使用特定正则模式解析响应

    Returns:
        解析出的 sections 列表
    """
    import re

    # 分割响应（使用捕获组保留分隔符）
    # 将 (\n##\s+) 改为捕获组，这样分隔符也会保留在结果中
    parts = re.split(pattern, response, flags=re.MULTILINE)

    if len(parts) < 3:
        return []

    sections = []

    # 分割后的结构：
    # parts[0] = 开头的内容（可能为空）
    # parts[1] = 标题 + 内容（第一个 ## 后的内容）
    # parts[2] = 标题 + 内容（第二个 ## 后的内容）
    # ...
    # 每个 part 的格式是 "标题\n内容..."

    for part in parts:
        part = part.strip()
        if not part:
            continue

        # 分离标题和内容
        lines = part.split('\n', 1)
        title = lines[0].strip()

        # 如果没有内容行，跳过
        if len(lines) < 2:
            continue

        content = lines[1].strip() if len(lines) > 1 else ""

        # 过滤掉看起来不像标题的内容
        if not title or len(title) > 100:
            # 可能是内容，跳过
            continue

        sections.append({
            'title': title,
            'content': content
        })

    return sections


def _match_sections_to_template(sections: list, template: UserTemplate) -> list:
    """
    将解析出的 sections 匹配到模板定义

    Args:
        sections: 解析出的 section 字典列表
        template: 用户模板

    Returns:
        SummarySection 对象列表
    """
    result = []
    template_sections_by_id = {s.id: s for s in template.sections}
    template_sections_by_title = {s.title: s for s in template.sections}

    for order, section in enumerate(sections):
        title = section['title']
        content = section['content']

        if not content:
            continue

        # 尝试匹配模板中的 section
        matched_template = None

        # 1. 按 title 精确匹配
        if title in template_sections_by_title:
            matched_template = template_sections_by_title[title]
        else:
            # 2. 模糊匹配
            for template_title, template_section in template_sections_by_title.items():
                if template_title in title or title in template_title:
                    matched_template = template_section
                    break

        if matched_template:
            result.append(SummarySection(
                id=matched_template.id,
                title=matched_template.title,
                content=content,
                format=SectionFormat.BULLET_POINTS,
                order=matched_template.order
            ))
        else:
            # 未匹配到，创建新 section
            result.append(SummarySection(
                id=_title_to_id(title),
                title=title,
                content=content,
                format=SectionFormat.BULLET_POINTS,
                order=len(result)
            ))

    return result


def _fallback_use_template(response: str, template: UserTemplate) -> list:
    """
    兜底策略：使用模板结构分配响应

    将整个响应分配给第一个必需的 section
    """
    # 找第一个必需的 section
    for template_section in sorted(template.sections, key=lambda s: s.order):
        if template_section.required:
            return [
                SummarySection(
                    id=template_section.id,
                    title=template_section.title,
                    content=response.strip(),
                    format=SectionFormat.PARAGRAPH,
                    order=template_section.order
                )
            ]

    # 如果没有必需的，使用第一个
    if template.sections:
        first = sorted(template.sections, key=lambda s: s.order)[0]
        return [
            SummarySection(
                id=first.id,
                title=first.title,
                content=response.strip(),
                format=SectionFormat.PARAGRAPH,
                order=first.order
            )
        ]

    return [_create_default_section(response)]


def _create_default_section(response: str) -> SummarySection:
    """创建默认 section"""
    return SummarySection(
        id="summary",
        title="会议总结",
        content=response.strip(),
        format=SectionFormat.PARAGRAPH,
        order=0
    )


def _title_to_id(title: str) -> str:
    """
    将标题转换为 ID

    Args:
        title: 标题字符串

    Returns:
        ID 字符串
    """
    import re
    # 移除特殊字符，转换为小写，用连字符连接
    id = re.sub(r'[^\w\u4e00-\u9fff]+', '-', title.lower())
    return id.strip('-')
