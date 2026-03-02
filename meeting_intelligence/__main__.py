#!/usr/bin/env python3
"""
AI Meeting Assistant - Minimal CLI

最小可运行 CLI 入口。

用法:
    python -m meeting_intelligence input.mp4
    python -m meeting_intelligence input.mp3 --provider glm

流程:
    input_file → ASR → Transcript → generate_summary() → 保存输出
"""

import argparse
import os
import sys
from pathlib import Path

# 加载 .env（可选）
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent / ".env"
    load_dotenv(env_path)
except ImportError:
    pass


def create_llm_provider(provider_name: str, model: str = None):
    """
    创建 LLM Provider

    Args:
        provider_name: Provider 名称 (mock, glm, openai, anthropic)
        model: 模型名称

    Returns:
        LLM Provider 实例
    """
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
            raise RuntimeError(
                "未设置 OPENAI_API_KEY 环境变量\n"
                "请设置: export OPENAI_API_KEY=sk-xxx"
            )
        model = model or os.environ.get("DEFAULT_LLM_MODEL", "gpt-4o-mini")
        return OpenAIProvider(api_key=api_key, model=model)

    elif provider_name == "anthropic":
        from summarizer.llm.anthropic import AnthropicProvider
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError(
                "未设置 ANTHROPIC_API_KEY 环境变量\n"
                "请设置: export ANTHROPIC_API_KEY=sk-ant-xxx"
            )
        model = model or os.environ.get("DEFAULT_LLM_MODEL", "claude-3-5-sonnet-20241022")
        return AnthropicProvider(api_key=api_key, model=model)

    else:
        raise ValueError(f"不支持的 provider: {provider_name}")


def main():
    parser = argparse.ArgumentParser(
        prog="meeting-intelligence",
        description="AI Meeting Assistant - 智能会议总结工具",
        epilog="""
示例:
  # 使用 Mock Provider（无需 API Key）
  python -m meeting_intelligence meeting.mp4

  # 使用 GLM (智谱 AI)
  python -m meeting_intelligence meeting.mp4 --provider glm

  # 使用 OpenAI
  python -m meeting_intelligence meeting.mp4 --provider openai --model gpt-4o

  # 使用 Anthropic
  python -m meeting_intelligence meeting.mp4 --provider anthropic

  # 指定模板
  python -m meeting_intelligence meeting.mp4 --provider glm --template product-manager
        """
    )
    parser.add_argument('input', help='输入文件路径（音频 .mp3/.wav/.m4a 或 视频 .mp4/.mkv/.mov）')
    parser.add_argument('--template', '-t', default='general', help='模板名称（默认: general）')
    parser.add_argument('--provider', '-p', default='mock',
                       choices=['mock', 'glm', 'openai', 'anthropic'],
                       help='LLM 提供商（默认: mock，无需 API Key）')
    parser.add_argument('--model', '-m', help='LLM 模型名称（可选，默认使用环境变量或默认值）')
    parser.add_argument('--no-save', action='store_true', help='不保存结果到文件')

    args = parser.parse_args()
    input_path = Path(args.input)

    # 验证文件存在
    if not input_path.exists():
        print(f"错误: 文件不存在: {args.input}")
        return 1

    # 验证文件格式
    video_extensions = ['.mp4', '.mkv', '.mov']
    audio_extensions = ['.mp3', '.wav', '.m4a']
    ext = input_path.suffix.lower()

    if ext not in video_extensions + audio_extensions:
        print(f"错误: 不支持的文件格式: {ext}")
        print(f"支持的格式: 视频 {video_extensions}, 音频 {audio_extensions}")
        return 1

    # 处理文件
    try:
        print(f"AI Meeting Assistant")
        print(f"=" * 40)
        print(f"输入文件: {input_path}")
        print(f"文件类型: {'视频' if ext in video_extensions else '音频'}")
        print(f"使用模板: {args.template}")
        print(f"LLM Provider: {args.provider}")
        if args.model:
            print(f"LLM Model: {args.model}")
        print()

        # 1. ASR 转写
        print("Step 1: ASR 转写...")
        from asr.transcribe import transcribe
        result = transcribe(str(input_path))
        print(f"  完成! 识别了 {len(result.utterances)} 个片段")
        print(f"  转录文件: {result.output_path}")
        print()

        # 2. 创建 LLM Provider
        print(f"Step 2: 创建 {args.provider.upper()} Provider...")
        llm = create_llm_provider(args.provider, args.model)
        print(f"  完成! 使用模型: {llm.model}")
        print()

        # 3. 生成摘要
        print("Step 3: 生成摘要...")
        from summarizer.generate import generate_summary
        from transcript.types import TranscriptDocument

        # ASR 输出格式与 TranscriptDocument 期望格式不同
        # 需要手动创建 TranscriptDocument
        import json
        with open(result.output_path, 'r', encoding='utf-8') as f:
            asr_data = json.load(f)

        # 创建 TranscriptDocument
        transcript_doc = TranscriptDocument(
            utterances=asr_data['utterances'],
            audio_path=asr_data['audio_path'],
            duration=asr_data['duration'],
            asr_provider=asr_data['asr_provider'],
            created_at=asr_data.get('timestamp'),
            document_path=result.output_path
        )

        summary = generate_summary(
            transcript=transcript_doc,
            template=args.template,
            llm_provider=llm,
            save=not args.no_save
        )

        print(f"  完成! 生成了 {len(summary.sections)} 个章节")
        print(f"  处理时间: {summary.processing_time:.2f} 秒")
        print()

        # 4. 显示结果
        print("=" * 40)
        print("摘要结果:")
        print("=" * 40)
        for section in summary.sections:
            print(f"\n## {section.title}")
            print(section.content)
        print()

        if summary.output_path:
            print(f"摘要文件: {summary.output_path}")

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
