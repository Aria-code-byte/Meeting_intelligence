#!/usr/bin/env python3
"""
AI Meeting Assistant - Minimal CLI (优化版)

改进：
- 添加增强文稿导出 (.txt)
- 优化摘要生成（确保 id 和 title 正确填充）
- 清晰的控制台输出（三步骤）
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

# 加载 .env（可选）
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent / ".env"
    load_dotenv(env_path)
except ImportError:
    pass


# ============================================================
# 输出目录配置
# ============================================================

OUTPUT_DIR = Path(__file__).parent.parent / "data" / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def get_output_timestamp() -> str:
    """获取输出文件时间戳"""
    return datetime.now().strftime("%Y%m%d_%H%M%S")


# ============================================================
# LLM Provider 创建
# ============================================================

def create_llm_provider(provider_name: str, model: str = None):
    """创建 LLM Provider"""
    if provider_name == "mock":
        from summarizer.llm.mock import MockLLMProvider
        return MockLLMProvider()

    elif provider_name == "glm":
        from summarizer.llm.glm import GLMProvider
        api_key = os.environ.get("ZHIPU_API_KEY")
        if not api_key:
            raise RuntimeError(
                "未设置 ZHIPU_API_KEY 环境变量\n"
                "请设置: export ZHIPU_API_KEY=your-key\n"
                "或在 .env 文件中添加: ZHIPU_API_KEY=your-key"
            )
        model = model or os.environ.get("DEFAULT_LLM_MODEL", "glm-4-flash")
        return GLMProvider(api_key=api_key, model=model)

    elif provider_name == "openai":
        from summarizer.llm.openai import OpenAIProvider
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("未设置 OPENAI_API_KEY 环境变量")
        model = model or os.environ.get("DEFAULT_LLM_MODEL", "gpt-4o-mini")
        return OpenAIProvider(api_key=api_key, model=model)

    elif provider_name == "anthropic":
        from summarizer.llm.anthropic import AnthropicProvider
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError("未设置 ANTHROPIC_API_KEY 环境变量")
        model = model or os.environ.get("DEFAULT_LLM_MODEL", "claude-3-5-sonnet-20241022")
        return AnthropicProvider(api_key=api_key, model=model)

    else:
        raise ValueError(f"不支持的 provider: {provider_name}")


# ============================================================
# 增强文稿处理
# ============================================================

def enhance_transcript(
    transcript_doc: dict,
    llm_provider,
    template_name: str = "general"
) -> str:
    """
    增强转录文本（使用 LLMTranscriptEnhancer）

    对于长文本，自动分块处理
    """
    from transcript.llm.enhancer import LLMTranscriptEnhancer, LLMEnhancerConfig
    from summarizer.llm.base import LLMMessage

    # 提取完整文本
    utterances = transcript_doc.get('utterances', [])

    # 判断文本长度，决定是否分块
    total_chars = sum(len(u.get('text', '')) for u in utterances)

    if total_chars < 3000:
        # 短文本，直接处理
        return _enhance_text_direct(utterances, llm_provider, template_name)
    else:
        # 长文本，分块处理
        return _enhance_text_in_blocks(utterances, llm_provider, template_name)


def _enhance_text_direct(utterances: list, llm_provider, template_name: str) -> str:
    """直接增强短文本"""
    from summarizer.llm.base import LLMMessage

    transcript_text = ' '.join([u.get('text', '') for u in utterances])

    # 使用强化版 prompt
    from transcript.llm.enhancer import LLMEnhancerConfig, PREDEFINED_TEMPLATES

    template = PREDEFINED_TEMPLATES.get(
        "speech-to-text-refiner" if template_name == "general" else template_name,
        PREDEFINED_TEMPLATES["general"]
    )

    system_prompt = template.system_prompt
    user_prompt = template.format_user_prompt(transcript_text)

    messages = [
        LLMMessage(role="system", content=system_prompt),
        LLMMessage(role="user", content=user_prompt)
    ]

    response = llm_provider.generate(messages=messages, temperature=0.1, max_tokens=8000)
    enhanced_text = response.content if hasattr(response, 'content') else str(response)

    # 简单清洗
    enhanced_text = enhanced_text.strip()
    enhanced_text = re.sub(r'\n{3,}', '\n\n', enhanced_text)

    return enhanced_text


def _enhance_text_in_blocks(utterances: list, llm_provider, template_name: str) -> str:
    """分块增强长文本"""
    from summarizer.llm.base import LLMMessage
    from transcript.llm.enhancer import PREDEFINED_TEMPLATES

    template = PREDEFINED_TEMPLATES.get(
        "speech-to-text-refiner" if template_name == "general" else template_name,
        PREDEFINED_TEMPLATES["general"]
    )

    system_prompt = template.system_prompt

    # 分块：每 2000 字符一块
    blocks = []
    current_block = []

    current_size = 0
    for u in utterances:
        text = u.get('text', '')
        if current_size + len(text) > 2000 and current_block:
            blocks.append(current_block)
            current_block = []
            current_size = 0
        current_block.append(text)
        current_size += len(text)

    if current_block:
        blocks.append(current_block)

    # 处理每个块
    enhanced_blocks = []
    for i, block in enumerate(blocks):
        transcript_text = ' '.join(block)

        user_prompt = template.format_user_prompt(transcript_text)

        messages = [
            LLMMessage(role="system", content=system_prompt),
            LLMMessage(role="user", content=user_prompt)
        ]

        try:
            response = llm_provider.generate(messages=messages, temperature=0.1, max_tokens=8000)
            enhanced_text = response.content if hasattr(response, 'content') else str(response)
            enhanced_text = enhanced_text.strip()
            enhanced_blocks.append(enhanced_text)
        except Exception as e:
            print(f"      块 {i+1} 增强失败，使用原文: {e}")
            enhanced_blocks.append(transcript_text)

    # 合并所有块
    enhanced_text = ' '.join(enhanced_blocks)
    enhanced_text = re.sub(r'\n{3,}', '\n\n', enhanced_text)

    return enhanced_text


# ============================================================
# 带时间索引的实录生成
# ============================================================

def create_time_blocks(
    utterances: list,
    block_duration_minutes: int = 3
) -> list:
    """
    将 utterances 按时间跨度聚合为时间块

    Args:
        utterances: 原始 utterance 列表
        block_duration_minutes: 每块的时长（分钟）

    Returns:
        时间块列表，每个块包含 start_ms, end_ms, text
    """
    if not utterances:
        return []

    block_duration_ms = block_duration_minutes * 60 * 1000
    blocks = []

    current_block = {
        "start_ms": int(utterances[0]["start"] * 1000),
        "end_ms": int(utterances[0]["end"] * 1000),
        "text": "",
        "utterances": []
    }

    for u in utterances:
        u_start_ms = int(u["start"] * 1000)
        u_end_ms = int(u["end"] * 1000)

        # 检查是否应该开始新块
        if u_start_ms >= current_block["start_ms"] + block_duration_ms and current_block["text"]:
            # 保存当前块
            blocks.append({
                "start_ms": current_block["start_ms"],
                "end_ms": current_block["end_ms"],
                "text": current_block["text"].strip()
            })
            # 开始新块
            current_block = {
                "start_ms": u_start_ms,
                "end_ms": u_end_ms,
                "text": "",
                "utterances": []
            }

        current_block["end_ms"] = max(current_block["end_ms"], u_end_ms)
        current_block["text"] += " " + u["text"]
        current_block["utterances"].append(u)

    # 添加最后一个块
    if current_block["text"].strip():
        blocks.append({
            "start_ms": current_block["start_ms"],
            "end_ms": current_block["end_ms"],
            "text": current_block["text"].strip()
        })

    return blocks


def ms_to_mmss(ms: int) -> str:
    """
    将毫秒转换为 MM:SS 格式

    Args:
        ms: 毫秒数

    Returns:
        格式化后的时间字符串
    """
    seconds = ms // 1000
    mm = seconds // 60
    ss = seconds % 60
    return f"{mm:02d}:{ss:02d}"


def refine_transcript_with_timestamps(
    transcript_doc: dict,
    llm_provider,
    block_duration_minutes: int = 3
) -> str:
    """
    生成带时间索引的纯净实录

    Args:
        transcript_doc: 转录文档
        llm_provider: LLM 提供商
        block_duration_minutes: 每块的时长（分钟）

    Returns:
        带时间戳的实录文本
    """
    from template.recorder import get_recorder_prompts
    from summarizer.llm.base import LLMMessage

    utterances = transcript_doc.get('utterances', [])

    # 创建时间块
    time_blocks = create_time_blocks(utterances, block_duration_minutes)

    print(f"      ✓ 创建了 {len(time_blocks)} 个时间块")

    # 处理每个时间块
    refined_lines = []

    for i, block in enumerate(time_blocks):
        start_time = ms_to_mmss(block["start_ms"])
        end_time = ms_to_mmss(block["end_ms"])

        # 获取提示词
        prompts = get_recorder_prompts(block["text"])

        messages = [
            LLMMessage(role="system", content=prompts["system_prompt"]),
            LLMMessage(role="user", content=prompts["user_prompt"])
        ]

        # 调用 LLM
        try:
            response = llm_provider.generate(
                messages=messages,
                temperature=0.1,
                max_tokens=8000
            )
            refined_text = response.content if hasattr(response, 'content') else str(response)
        except Exception as e:
            print(f"      块 {i+1} 处理失败，使用原文: {e}")
            refined_text = block["text"]

        # 清洗文本
        refined_text = refined_text.strip()
        refined_text = re.sub(r'\n{3,}', '\n\n', refined_text)

        # 添加时间戳
        refined_lines.append(f"[{start_time} - {end_time}] {refined_text}")

    return "\n\n".join(refined_lines)


# ============================================================
# 摘要解析（增强版）
# ============================================================

def parse_summary_sections(content: str) -> list:
    """
    解析摘要内容为 sections（增强版）

    确保每个 section 都有正确的 id 和 title
    """
    sections = []

    # 按 markdown 标题分割
    pattern = r'\n##\s+([^\n]+)'
    parts = re.split(pattern, content)

    for i, title in enumerate(re.findall(pattern, content)):
        title = title.strip()
        # 获取对应的内容
        if i + 1 < len(parts):
            section_content = parts[i + 1].strip()
        else:
            section_content = ""

        # 推断 id
        section_id = _infer_section_id(title)

        sections.append({
            'id': section_id,
            'title': title,
            'content': section_content
        })

    return sections


def _infer_section_id(title: str) -> str:
    """
    从标题推断 section id

    Args:
        title: 标题字符串

    Returns:
        section id
    """
    title_lower = title.lower()

    # 关键词映射
    keywords_map = {
        'summary': 'summary',
        '总结': 'summary',
        'key': 'key-points',
        '关键': 'key-points',
        '要点': 'key-points',
        'action': 'action-items',
        '行动': 'action-items',
        'actionitem': 'action-items',
        'decision': 'decisions',
        '决策': 'decisions',
        'requirement': 'requirements',
        '需求': 'requirements',
        'risk': 'risks',
        '风险': 'risks',
    }

    for keyword, section_id in keywords_map.items():
        if keyword in title_lower:
            return section_id

    # 默认：转换标题为 id
    return re.sub(r'[^\w\u4e00-\u9fff]+', '-', title_lower).strip('-')


# ============================================================
# 主程序
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        prog="meeting-intelligence",
        description="AI Meeting Assistant - 智能会议总结工具",
        epilog="""
示例:
  python -m meeting_intelligence meeting.mp4
  python -m meeting_intelligence meeting.mp3 --provider glm
  python -m meeting_intelligence meeting.mp4 --provider glm --template product-manager
        """
    )
    parser.add_argument('input', help='输入文件路径')
    parser.add_argument('--template', '-t', default='general', help='模板名称（默认: general）')
    parser.add_argument('--provider', '-p', default='mock',
                       choices=['mock', 'glm', 'openai', 'anthropic'],
                       help='LLM 提供商（默认: mock）')
    parser.add_argument('--model', '-m', help='LLM 模型名称')
    parser.add_argument('--no-save', action='store_true', help='不保存结果到文件')

    args = parser.parse_args()
    input_path = Path(args.input)

    # 验证文件
    if not input_path.exists():
        print(f"错误: 文件不存在: {args.input}")
        return 1

    video_extensions = ['.mp4', '.mkv', '.mov']
    audio_extensions = ['.mp3', '.wav', '.m4a']
    ext = input_path.suffix.lower()

    if ext not in video_extensions + audio_extensions:
        print(f"错误: 不支持的文件格式: {ext}")
        return 1

    try:
        # 打印标题
        print("=" * 50)
        print("  AI Meeting Assistant")
        print("=" * 50)
        print(f"输入文件: {input_path}")
        print(f"文件类型: {'视频' if ext in video_extensions else '音频'}")
        print(f"模板: {args.template}")
        print(f"Provider: {args.provider}")
        if args.model:
            print(f"Model: {args.model}")
        print()

        timestamp = get_output_timestamp()
        base_name = input_path.stem

        # ============================================================
        # 步骤 1: ASR 转写
        # ============================================================
        print("[1/3] 原始转录中...")
        from asr.transcribe import transcribe
        asr_result = transcribe(str(input_path))

        # 读取 ASR 结果
        with open(asr_result.output_path, 'r', encoding='utf-8') as f:
            transcript_data = json.load(f)

        transcript_doc = {
            'utterances': transcript_data['utterances'],
            'audio_path': transcript_data['audio_path'],
            'duration': transcript_data['duration'],
            'asr_provider': transcript_data['asr_provider'],
            'timestamp': transcript_data.get('timestamp'),
            'document_path': asr_result.output_path
        }

        print(f"      ✓ 识别了 {len(transcript_data['utterances'])} 个片段")
        print()
        print("[1/3] 原始转录已保存")
        print(f"      文件: {Path(asr_result.output_path).name}")
        print()

        # ============================================================
        # 步骤 2: 增强文稿（书面化）
        # ============================================================
        print("[2/3] 增强文稿（书面化）中...")

        # 创建 LLM Provider
        llm = create_llm_provider(args.provider, args.model)

        # 增强转录
        enhanced_text = enhance_transcript(transcript_doc, llm, args.template)

        print(f"      ✓ 增强完成")

        # 保存增强文稿
        if not args.no_save:
            enhanced_path = OUTPUT_DIR / f"{base_name}_enhanced_{timestamp}.txt"
            with open(enhanced_path, 'w', encoding='utf-8') as f:
                f.write(enhanced_text)
        else:
            enhanced_path = None

        print()
        print("[2/3] 增强文稿（书面化）已保存")
        if enhanced_path:
            print(f"      文件: {enhanced_path.name}")
        print()

        # ============================================================
        # 步骤 3: 带时间索引的纯净实录
        # ============================================================
        print("[3/3] 带时间索引的纯净实录生成中...")

        # 生成带时间戳的实录
        import time
        start_time = time.time()

        refined_text = refine_transcript_with_timestamps(
            transcript_doc,
            llm,
            block_duration_minutes=3
        )

        processing_time = time.time() - start_time

        # 保存实录文件
        if not args.no_save:
            refined_path = OUTPUT_DIR / f"{base_name}_refined_{timestamp}.txt"
            with open(refined_path, 'w', encoding='utf-8') as f:
                f.write(refined_text)
        else:
            refined_path = None

        print(f"      ✓ 处理时间: {processing_time:.2f} 秒")
        print()
        print("[3/3] 带时间索引的纯净实录已生成")
        if refined_path:
            print(f"      文件: {refined_path.name}")
        print()

        # 显示预览
        print("=" * 50)
        print("实录预览:")
        print("=" * 50)
        preview_lines = refined_text.split('\n')
        for line in preview_lines[:6]:  # 显示前 6 行
            print(line)
        if len(preview_lines) > 6:
            print("...")
        print()

        # 输出文件列表
        if not args.no_save:
            print("输出文件:")
            if Path(asr_result.output_path).exists():
                print(f"  - {asr_result.output_path}")
            if 'enhanced_path' in locals() and enhanced_path and Path(enhanced_path).exists():
                print(f"  - {enhanced_path}")
            if 'refined_path' in locals() and refined_path and Path(refined_path).exists():
                print(f"  - {refined_path}")

        return 0

    except RuntimeError as e:
        print()
        print(f"错误: {e}")
        return 1
    except Exception as e:
        print()
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
