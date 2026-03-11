#!/usr/bin/env python3
"""
CLI 工具功能演示脚本

展示 MeetingAssistantCLI 的核心功能，无需交互。
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from meeting_intelligence.cli import (
    Template,
    TemplateStorage,
    PromptBuilder,
    LLMService,
    MeetingAssistantCLI,
)


def print_section(title: str):
    """打印分节标题"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def demo_template_operations():
    """演示模板操作"""
    print_section("1. 模板操作演示")

    # 创建存储
    storage = TemplateStorage()

    # 查看默认模板
    templates = storage.list_templates()
    print(f"\n当前有 {len(templates)} 个模板:")
    for t in templates:
        print(f"  - [{t.name}] {t.description[:50]}...")

    # 添加新模板
    print("\n添加新模板...")
    new_template = Template(
        name="产品经理",
        description="关注产品需求、功能决策、用户反馈和后续行动项"
    )
    if storage.add_template(new_template):
        print(f"  ✓ 模板「{new_template.name}」已添加")

    # 再次查看
    templates = storage.list_templates()
    print(f"\n现在有 {len(templates)} 个模板")

    # 删除模板
    if storage.delete_template("产品经理"):
        print(f"  ✓ 模板「产品经理」已删除")


def demo_prompt_building():
    """演示 Prompt 构建"""
    print_section("2. Prompt 构建演示")

    template = Template(
        name="产品经理",
        description="关注产品需求、功能决策、用户反馈和后续行动项"
    )

    transcript = """
    主持人：今天我们讨论新功能的需求。
    产品经理：用户希望添加数据导出功能。
    开发：技术上可行，需要3天时间。
    """.strip()

    prompt = PromptBuilder.build_prompt(transcript, template)

    print("\n构建的 Prompt:")
    print("-" * 60)
    print(prompt)
    print("-" * 60)


def demo_llm_service():
    """演示 LLM 服务"""
    print_section("3. LLM 服务演示")

    service = LLMService(provider="mock")

    prompt = "请总结会议内容..."

    print("\n调用 LLM 服务...")
    summary = service.generate_summary(prompt)

    print("\n生成的总结:")
    print("-" * 60)
    print(summary)
    print("-" * 60)


def demo_full_workflow():
    """演示完整工作流"""
    print_section("4. 完整工作流演示")

    cli = MeetingAssistantCLI()

    # 步骤 1: 模拟生成文字稿
    print("\n[步骤 1] 生成文字稿...")
    cli.current_transcript = cli.SAMPLE_TRANSCRIPT
    print(f"  ✓ 文字稿已生成 ({len(cli.current_transcript)} 字符)")

    # 步骤 2: 选择模板
    print("\n[步骤 2] 选择模板...")
    templates = cli.storage.list_templates()
    selected = templates[0]
    print(f"  ✓ 使用模板: {selected.name}")

    # 步骤 3: 生成总结
    print("\n[步骤 3] 生成总结...")
    prompt = PromptBuilder.build_prompt(cli.current_transcript, selected)
    summary = cli.llm_service.generate_summary(prompt)

    print("\n生成的会议总结:")
    print("-" * 60)
    print(summary)
    print("-" * 60)


def demo_custom_template():
    """演示自定义模板"""
    print_section("5. 自定义模板演示")

    # 创建不同视角的模板
    templates_to_test = [
        Template("高管视角", "关注战略决策、资源投入和ROI"),
        Template("技术视角", "关注技术方案、架构决策和实现细节"),
        Template("销售视角", "关注客户需求、产品价值和竞争优势"),
    ]

    transcript = "我们讨论了新产品的功能规划和市场策略..."

    for template in templates_to_test:
        print(f"\n模板: {template.name}")
        print(f"描述: {template.description}")

        prompt = PromptBuilder.build_prompt(transcript, template)
        print(f"Prompt 片段: ...{template.name}...{template.description[:30]}...")


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("  AI 会议内容理解助手 - 功能演示")
    print("=" * 60)

    try:
        demo_template_operations()
        demo_prompt_building()
        demo_llm_service()
        demo_full_workflow()
        demo_custom_template()

        print("\n" + "=" * 60)
        print("  演示完成！")
        print("=" * 60)
        print("\n运行交互式 CLI:")
        print("  python -m meeting_intelligence.cli")
        print("\n或:")
        print("  python3 meeting_intelligence/cli.py")
        print()

    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
