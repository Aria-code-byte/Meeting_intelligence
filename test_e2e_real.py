#!/usr/bin/env python3
"""
端到端测试脚本：验证真实 LLM 完整流程

此脚本验证从音频到总结的完整流程，使用真实的 LLM API。
运行前请设置环境变量：
- OPENAI_API_KEY 或 ANTHROPIC_API_KEY 或 ZHIPU_API_KEY
"""

import os
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))


def check_api_key():
    """检查 API Key 是否设置"""
    openai_key = os.environ.get("OPENAI_API_KEY")
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
    zhipu_key = os.environ.get("ZHIPU_API_KEY")

    if not openai_key and not anthropic_key and not zhipu_key:
        print("❌ 错误: 未设置 API Key")
        print("\n请设置以下环境变量之一:")
        print("  - OPENAI_API_KEY (用于 OpenAI)")
        print("  - ANTHROPIC_API_KEY (用于 Anthropic)")
        print("  - ZHIPU_API_KEY (用于智谱 GLM)")
        print("\n示例:")
        print("  export OPENAI_API_KEY=sk-xxx")
        print("  export ANTHROPIC_API_KEY=sk-ant-xxx")
        print("  export ZHIPU_API_KEY=your-key")
        return False

    return True


def find_test_audio():
    """查找测试音频文件"""
    # 按优先级查找
    possible_paths = [
        "data/raw_audio/audio_20260122_140824.mp3",
        "data/raw_audio/audio_20260122_140824.wav",
        "tests/fixtures/short_meeting.wav",
    ]

    for path in possible_paths:
        if Path(path).exists():
            return path

    return None


def run_e2e_test():
    """运行端到端测试"""

    print("=" * 60)
    print("AI Meeting Assistant - 端到端真实 LLM 测试")
    print("=" * 60)

    # 检查 API Key
    if not check_api_key():
        return 1

    # 确定使用的 provider
    use_openai = bool(os.environ.get("OPENAI_API_KEY"))
    use_anthropic = bool(os.environ.get("ANTHROPIC_API_KEY"))
    use_zhipu = bool(os.environ.get("ZHIPU_API_KEY"))

    if use_zhipu:
        from summarizer.llm import GLMProvider
        llm = GLMProvider(model="glm-4-flash")
        provider_name = "智谱 GLM"
    elif use_openai:
        from summarizer.llm import OpenAIProvider
        llm = OpenAIProvider(model="gpt-3.5-turbo")
        provider_name = "OpenAI"
    else:
        from summarizer.llm import AnthropicProvider
        llm = AnthropicProvider(model="claude-3-haiku-20240307")
        provider_name = "Anthropic"

    print(f"\n使用 LLM Provider: {provider_name}")
    print(f"模型: {llm.model}")

    # 查找测试音频
    audio_path = find_test_audio()

    if audio_path is None:
        print(f"\n❌ 错误: 未找到测试音频文件")
        print("\n请将测试音频放在以下位置之一:")
        for path in [
            "data/raw_audio/audio_20260122_140824.mp3",
            "tests/fixtures/short_meeting.wav"
        ]:
            print(f"  - {path}")
        return 1

    print(f"使用音频: {audio_path}")

    # 检查文件大小
    file_size = Path(audio_path).stat().st_size / 1024  # KB
    if file_size > 10 * 1024:  # > 10MB
        print(f"\n⚠️  警告: 音频文件较大 ({file_size:.0f} KB)")
        print("   这可能会产生较高的 API 费用")
        confirm = input("   继续吗? (y/n): ")
        if confirm.lower() != 'y':
            print("已取消")
            return 1

    # 运行完整流程
    print("\n开始处理...")

    try:
        from summarizer.pipeline import audio_to_summary

        summary = audio_to_summary(
            audio_path=audio_path,
            template_name="general",
            llm_provider=llm
        )

        # 显示结果
        print("\n" + "=" * 60)
        print("✅ 处理完成!")
        print("=" * 60)

        print(f"\n📋 结果信息:")
        print(f"  模板: {summary.template_name}")
        print(f"  模板角色: {summary.template_role}")
        print(f"  LLM: {summary.llm_provider}/{summary.llm_model}")
        print(f"  处理时间: {summary.processing_time:.2f} 秒")
        print(f"  生成 sections: {len(summary.sections)} 个")

        # 显示每个 section 的预览
        print(f"\n📝 内容预览:")
        for section in summary.sections:
            print(f"\n  ## {section.title}")
            preview = section.content[:150] + "..." if len(section.content) > 150 else section.content
            print(f"  {preview}")

        # 检查输出文件
        if summary.output_path and Path(summary.output_path).exists():
            print(f"\n💾 总结文件: {summary.output_path}")

            # 验证 JSON 格式
            import json
            with open(summary.output_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"  ✓ JSON 格式有效")
            print(f"  文件大小: {Path(summary.output_path).stat().st_size} 字节")

        print("\n" + "=" * 60)
        print("✅ 端到端测试通过!")
        print("=" * 60)

        return 0

    except Exception as e:
        print("\n" + "=" * 60)
        print("❌ 测试失败!")
        print("=" * 60)
        print(f"\n错误: {e}")

        import traceback
        print("\n详细错误信息:")
        traceback.print_exc()

        return 1


if __name__ == "__main__":
    sys.exit(run_e2e_test())
