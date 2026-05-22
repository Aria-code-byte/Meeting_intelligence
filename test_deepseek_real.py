#!/usr/bin/env python3
"""
测试真实 DeepSeek LLM 调用
验证 API 配置和总结生成
"""
import sys
import os
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "backend"))

def test_deepseek_real():
    """测试真实 DeepSeek API 调用"""
    print("\n=== 真实 DeepSeek LLM 测试 ===\n")

    try:
        from backend.providers.summary import SummaryProvider
        from dotenv import load_dotenv

        # 加载 .env 文件
        load_dotenv(project_root / "backend" / ".env")

        # 检查环境变量
        print("环境变量配置:")
        print(f"  AI_SUMMARY_PROVIDER: {os.getenv('AI_SUMMARY_PROVIDER')}")
        print(f"  LLM_PROVIDER: {os.getenv('LLM_PROVIDER')}")
        print(f"  OPENAI_BASE_URL: {os.getenv('OPENAI_BASE_URL')}")
        print(f"  OPENAI_MODEL: {os.getenv('OPENAI_MODEL')}")
        api_key = os.getenv('OPENAI_API_KEY', '')
        print(f"  OPENAI_API_KEY: {api_key[:10]}...{api_key[-4:]}")

        # 创建 provider
        provider = SummaryProvider()

        print(f"\nProvider 信息:")
        print(f"  Type: {type(provider.provider).__name__}")
        print(f"  Is using fallback: {provider.is_using_fallback()}")

        if provider.is_using_fallback():
            print("\n⚠️ LLM provider 不可用，使用 fallback 模式")
            return False

        print("\n✅ LLM provider 可用")

        # 测试长文字稿
        test_transcript = """
[00:00:00] 张三: 大家好，今天我们讨论 Q3 产品路线图。
[00:00:45] 李四: 我们计划在 7 月底完成新功能 A，8 月中旬完成功能 B。
[00:01:30] 王五: 测试团队需要提前两周介入，确保质量。
[00:02:00] 张三: 同意，下周安排 kickoff 会议。
[00:02:30] 李四: 另外，预算需要在月底前确认，我们需要申请额外的资源。
[00:03:00] 王五: 我来准备预算提案，包括人力和服务器成本。
[00:03:30] 张三: 很好，周五前发给大家审阅。
[00:04:00] 李四: 还有一个问题，关于技术选型，我们倾向于使用 React + TypeScript。
[00:04:30] 王五: 同意，团队对这个技术栈比较熟悉。
[00:05:00] 张三: 那就定了，下周一开始实施。
        """

        print("\n生成总结中...")
        result = provider.generate_summary(
            transcript=test_transcript,
            template_name="产品规划会议",
            template_description="Q3 产品路线图讨论会议",
            template_sections=["会议概要", "关键决策", "行动项", "时间表"],
            template_prompt="使用简洁专业的语言总结会议内容，突出关键决策和行动项，注明负责人和时间"
        )

        print(f"\n结果:")
        print(f"  Success: {result.success}")
        print(f"  Provider: {result.provider.value}")
        print(f"  Is Fallback: {result.is_fallback}")
        print(f"  Processing time: {result.processing_time_ms}ms")

        if result.success:
            summary = result.data.get('summary', '')
            model = result.data.get('model', 'unknown')
            print(f"  Model: {model}")
            print(f"  Summary length: {len(summary)}")

            print(f"\n生成的总结:")
            print("=" * 60)
            print(summary)
            print("=" * 60)

            assert not result.is_fallback, "应该使用真实 LLM"
            assert len(summary) > 100, "总结内容应该足够长"
            print("\n✅ 真实 DeepSeek LLM 调用成功！")
            return True
        else:
            print(f"\n❌ 生成失败: {result.error}")
            return False

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_deepseek_real()
    sys.exit(0 if success else 1)
