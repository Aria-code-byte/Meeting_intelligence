#!/usr/bin/env python3
"""
测试双模板总结功能
使用 mock 模式测试流程
"""

import json
import sys
import time
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

# 加载 .env 文件
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent / ".env"
    load_dotenv(env_path)
except ImportError:
    pass

from meeting_intelligence.cli import create_llm_provider, OUTPUT_DIR


def test_dual_summary(llm_provider: str = "deepseek"):
    """
    使用两个模板生成总结

    Args:
        llm_provider: LLM 提供商 (mock, glm, openai, anthropic, deepseek)
    """
    # 读取增强文字稿
    transcript_file = OUTPUT_DIR / "meeting_01_增强文字稿.txt"

    if not transcript_file.exists():
        print(f"错误: 找不到增强文字稿文件: {transcript_file}")
        return

    with open(transcript_file, "r", encoding="utf-8") as f:
        transcript_text = f.read()

    # 定义两个模板
    templates = [
        {
            "name": "大学生视角",
            "description": "从大学生学习的角度总结会议内容，突出重点知识点、学习要点和实际应用价值。"
        },
        {
            "name": "投资人",
            "description": "总结基本内容、机会点与风险。从投资角度分析项目的商业价值、市场前景和潜在风险。"
        }
    ]

    # 创建 LLM Provider
    print(f"\n使用 LLM Provider: {llm_provider}")
    print(f"转录文本长度: {len(transcript_text)} 字符\n")
    llm = create_llm_provider(llm_provider)

    from summarizer.llm.base import LLMMessage

    # 为每个模板生成总结
    for template in templates:
        print("=" * 60)
        print(f"模板: {template['name']}")
        print(f"描述: {template['description']}")
        print("=" * 60)

        # 构建 Prompt
        prompt = (
            f"你是一名专业会议分析助手。请从【{template['name']}】的视角总结以下会议内容。\n"
            f"总结要求：{template['description']}。\n"
            f"请使用结构化方式输出。\n\n"
            f"会议内容：\n{transcript_text}"
        )

        print("\n正在生成总结...")
        if llm_provider == "mock":
            print("(使用 mock 模式，不需要等待)")
        else:
            print("(这可能需要几十秒...)")

        try:
            # 使用重试机制调用 LLM
            messages = [LLMMessage(role="user", content=prompt)]

            if llm_provider == "mock":
                response = llm.generate(messages, temperature=0.7, max_tokens=2000)
            else:
                response = llm.generate_with_retry(messages, temperature=0.3, max_tokens=4000)

            summary_text = response.content if hasattr(response, 'content') else str(response)

            # 保存总结（Markdown 格式）
            output_file = OUTPUT_DIR / f"meeting_01{template['name']}总结.md"
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(f"# 会议总结 - {template['name']}\n\n")
                f.write(f"**模板描述:** {template['description']}\n")
                f.write(f"**LLM Provider:** {llm_provider}\n")
                f.write(f"**生成时间:** {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write("---\n\n")
                f.write(summary_text)

            print(f"\n✓ 总结生成成功！")
            print(f"  输出文件: {output_file.name}")

            # 显示结果预览
            print("\n" + "-" * 60)
            print("总结预览:")
            print("-" * 60)
            # 显示前 500 字符
            preview = summary_text[:500] + "..." if len(summary_text) > 500 else summary_text
            print(preview)
            print("-" * 60)

        except Exception as e:
            print(f"\n✗ 生成失败: {e}")

        # 模板间添加延迟
        if llm_provider != "mock":
            print("\n等待 5 秒后处理下一个模板...")
            time.sleep(5)
        else:
            print()

    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="测试双模板总结功能")
    parser.add_argument("--llm", "-l", default="deepseek",
                       choices=["mock", "glm", "openai", "anthropic", "deepseek"],
                       help="LLM 提供商（默认: deepseek）")

    args = parser.parse_args()

    # 提示
    if args.llm != "mock":
        print("=" * 60)
        print("注意: 使用真实 LLM API 可能会消耗配额")
        print("建议先用 --llm mock 测试流程")
        print("=" * 60)
        confirm = input("\n是否继续? (y/n): ").strip().lower()
        if confirm != 'y':
            print("已取消")
            sys.exit(0)

    test_dual_summary(llm_provider=args.llm)
