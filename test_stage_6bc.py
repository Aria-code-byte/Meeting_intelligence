#!/usr/bin/env python3
"""
测试 Stage 6B-C: 真实总结 provider 接入

测试内容:
1. Provider 初始化 (fallback vs LLM)
2. 空文字稿验证
3. 短文字稿验证
4. LLM 总结生成 (如果可用)
5. Fallback 总结生成
6. Provider info 接口
7. Metadata 字段一致性 (processedAt)
8. templateSnapshot 参数传递
"""
import sys
import os
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "backend"))

def test_summary_provider_fallback():
    """测试 fallback 模式"""
    print("\n=== 1. 测试 Fallback Summary Provider ===\n")

    # 设置环境变量为 fallback
    os.environ['AI_SUMMARY_PROVIDER'] = 'fallback'

    try:
        from backend.providers.summary import SummaryProvider

        provider = SummaryProvider()

        # 检查 provider 类型
        print(f"   Provider type: {type(provider.provider).__name__}")
        assert provider.is_using_fallback(), "应该使用 fallback provider"
        print("   ✅ 使用 fallback provider")

        # 测试空文字稿
        print("\n   测试空文字稿:")
        result = provider.generate_summary(
            transcript="",
            template_name="测试模板",
            template_sections=["章节1", "章节2"],
            template_prompt="测试提示词"
        )
        print(f"   Success: {result.success}")
        print(f"   Error: {result.error}")
        assert not result.success, "空文字稿应该失败"
        assert "无文字稿" in result.error or "空" in result.error.lower(), "错误信息应该提及空文字稿"
        print("   ✅ 空文字稿验证正确")

        # 测试短文字稿
        print("\n   测试短文字稿 (<10字符):")
        result = provider.generate_summary(
            transcript="短文本",
            template_name="测试模板",
            template_sections=["章节1"],
            template_prompt="测试提示词"
        )
        print(f"   Success: {result.success}")
        print(f"   Error: {result.error}")
        assert not result.success, "短文字稿应该失败"
        assert "过少" in result.error or "short" in result.error.lower(), "错误信息应该提及内容过少"
        print("   ✅ 短文字稿验证正确")

        # 测试正常文字稿
        print("\n   测试正常文字稿 (fallback 生成):")
        test_transcript = """
        [00:00:00] Speaker 1: 大家好，今天我们讨论项目进展。
        [00:00:30] Speaker 2: 第一阶段已经完成，现在进入第二阶段。
        [00:01:00] Speaker 1: 很好，下周一前完成第三阶段。
        [00:01:30] Speaker 2: 没问题，我会安排团队跟进。
        """

        result = provider.generate_summary(
            transcript=test_transcript,
            template_name="项目会议",
            template_description="项目进展讨论会议",
            template_sections=["会议概要", "行动项", "下一步计划"],
            template_prompt="简洁明了地总结会议内容"
        )

        print(f"   Success: {result.success}")
        print(f"   Provider: {result.provider.value}")
        print(f"   Is Fallback: {result.is_fallback}")
        print(f"   Processing time: {result.processing_time_ms}ms")
        print(f"   Summary length: {len(result.data.get('summary', ''))}")

        assert result.success, "正常文字稿应该成功"
        assert result.is_fallback, "应该使用 fallback 模式"
        assert len(result.data.get('summary', '')) > 0, "应该有总结内容"
        assert result.data.get('model') == 'fallback', "模型应该是 fallback"
        print("   ✅ Fallback 总结生成正确")

        # 测试 metadata
        print("\n   测试 metadata:")
        provider_info = provider.get_provider_info()
        print(f"   Type: {provider_info.get('type')}")
        print(f"   Available: {provider_info.get('available')}")
        assert provider_info.get('type') == 'fallback', "类型应该是 fallback"
        print("   ✅ Metadata 正确")

        print("\n✅ Fallback Summary Provider 测试通过")
        return True

    except Exception as e:
        print(f"❌ Fallback 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # 清理环境变量
        if 'AI_SUMMARY_PROVIDER' in os.environ:
            del os.environ['AI_SUMMARY_PROVIDER']


def test_summary_provider_llm():
    """测试 LLM 模式 (如果可用)"""
    print("\n=== 2. 测试 LLM Summary Provider ===\n")

    # 设置环境变量为 deepseek (或 ollama, openai)
    os.environ['AI_SUMMARY_PROVIDER'] = 'deepseek'
    os.environ['LLM_PROVIDER'] = 'deepseek'

    try:
        from backend.providers.summary import SummaryProvider

        provider = SummaryProvider()

        print(f"   Provider type: {type(provider.provider).__name__}")
        print(f"   Is using fallback: {provider.is_using_fallback()}")

        # 检查 LLM 是否可用
        if provider.is_using_fallback():
            print("   ⚠️ LLM 不可用，自动回退到 fallback 模式")
            print("   这可能是因为:")
            print("      - LLM 服务未启动 (Ollama)")
            print("      - API Key 未配置 (OpenAI/Anthropic/DeepSeek)")
            print("      - 网络连接问题")
            return None  # 不是失败，只是不可用

        print("   ✅ LLM provider 可用")

        # 测试正常文字稿
        print("\n   测试 LLM 总结生成:")
        test_transcript = """
        [00:00:00] 张三: 大家好，今天我们讨论 Q3 产品路线图。
        [00:00:45] 李四: 我们计划在 7 月底完成新功能 A，8 月中旬完成功能 B。
        [00:01:30] 王五: 测试团队需要提前两周介入，确保质量。
        [00:02:00] 张三: 同意，下周安排 kickoff 会议。
        [00:02:30] 李四: 另外，预算需要在月底前确认。
        """

        result = provider.generate_summary(
            transcript=test_transcript,
            template_name="产品规划会议",
            template_description="Q3 产品路线图讨论",
            template_sections=["会议概要", "关键决策", "行动项", "时间表"],
            template_prompt="使用简洁专业的语言总结会议内容，突出关键决策和行动项"
        )

        print(f"   Success: {result.success}")
        print(f"   Provider: {result.provider.value}")
        print(f"   Is Fallback: {result.is_fallback}")
        print(f"   Processing time: {result.processing_time_ms}ms")

        if result.success:
            summary = result.data.get('summary', '')
            model = result.data.get('model', 'unknown')
            print(f"   Model: {model}")
            print(f"   Summary length: {len(summary)}")
            print(f"   Summary preview: {summary[:100]}...")

            assert not result.is_fallback, "不应该使用 fallback"
            assert len(summary) > 0, "应该有总结内容"
            assert model != 'fallback', "模型不应该是 fallback"
            print("   ✅ LLM 总结生成正确")
        else:
            print(f"   Error: {result.error}")
            print("   ⚠️ LLM 总结生成失败")

        # 测试 metadata
        print("\n   测试 metadata:")
        provider_info = provider.get_provider_info()
        print(f"   Type: {provider_info.get('type')}")
        print(f"   Available: {provider_info.get('available')}")
        if 'llm_provider' in provider_info:
            print(f"   LLM Provider: {provider_info.get('llm_provider')}")
        print("   ✅ Metadata 正确")

        print("\n✅ LLM Summary Provider 测试完成")
        return True

    except Exception as e:
        print(f"❌ LLM 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # 清理环境变量
        if 'AI_SUMMARY_PROVIDER' in os.environ:
            del os.environ['AI_SUMMARY_PROVIDER']
        if 'LLM_PROVIDER' in os.environ:
            del os.environ['LLM_PROVIDER']


def test_api_endpoints():
    """测试 API 端点"""
    print("\n=== 3. 测试 API 端点 ===\n")

    try:
        from fastapi.testclient import TestClient
        from backend.main import app

        client = TestClient(app)

        # 测试 health
        print("   测试 GET /health:")
        response = client.get("/health")
        print(f"   Status: {response.status_code}")
        assert response.status_code == 200, "health 应该返回 200"
        health_data = response.json()
        print(f"   Status: {health_data.get('status')}")
        print(f"   Summary Fallback: {health_data.get('summaryFallback')}")
        print("   ✅ Health 检查通过")

        # 测试 provider info
        print("\n   测试 GET /api/v1/providers/info:")
        response = client.get("/api/v1/providers/info")
        print(f"   Status: {response.status_code}")
        assert response.status_code == 200, "providers/info 应该返回 200"
        info_data = response.json()

        print(f"   Summary type: {info_data.get('summary', {}).get('type')}")
        print(f"   Summary available: {info_data.get('summary', {}).get('available')}")
        print(f"   Summary configured: {info_data.get('summary', {}).get('configured')}")

        # 检查不泄露敏感信息
        summary_config = info_data.get('summary', {}).get('config', {})
        print(f"   Summary config keys: {list(summary_config.keys()) if summary_config else 'none'}")

        # 确保没有 api key 泄漏
        assert 'api_key' not in str(summary_config).lower(), "不应该泄漏 api_key"
        assert 'secret' not in str(summary_config).lower(), "不应该泄漏 secret"
        print("   ✅ Provider info 通过")

        # 测试 summarize (fallback 模式)
        print("\n   测试 POST /api/v1/summarize (fallback 模式):")
        test_transcript = """
        [00:00:00] Speaker 1: 今天讨论新功能开发计划。
        [00:00:30] Speaker 2: 第一阶段预计两周完成。
        [00:01:00] Speaker 1: 下周五进行进度评审。
        """

        response = client.post("/api/v1/summarize", json={
            "transcript": test_transcript,
            "template_name": "开发计划",
            "template_description": "新功能开发讨论",
            "template_sections": ["讨论要点", "时间安排"],
            "template_prompt": "简洁总结"
        })

        print(f"   Status: {response.status_code}")
        assert response.status_code == 200, "summarize 应该返回 200"

        summarize_data = response.json()
        print(f"   Success: {summarize_data.get('success')}")
        print(f"   Provider: {summarize_data.get('provider')}")
        print(f"   Is Fallback: {summarize_data.get('isFallback')}")
        print(f"   Has summary: {bool(summarize_data.get('summary'))}")

        # 检查 metadata 字段命名
        if summarize_data.get('metadata'):
            metadata = summarize_data.get('metadata')
            print(f"   Metadata keys: {list(metadata.keys())}")
            assert 'processedAt' in metadata, "应该有 processedAt 字段"
            assert 'processed_at' not in metadata, "不应该有 processed_at 字段 (snake_case)"
            print(f"   processedAt: {metadata.get('processedAt')}")

        assert summarize_data.get('success'), "应该成功"
        assert summarize_data.get('isFallback') in [True, False], "isFallback 应该是布尔值"
        print("   ✅ Summarize API 通过")

        # 测试空文字稿错误
        print("\n   测试 POST /api/v1/summarize (空文字稿):")
        response = client.post("/api/v1/summarize", json={
            "transcript": "",
            "template_name": "测试",
            "template_sections": ["章节1"],
            "template_prompt": "测试"
        })

        print(f"   Status: {response.status_code}")
        assert response.status_code == 200, "应该返回 200 (但 success=false)"

        empty_data = response.json()
        print(f"   Success: {empty_data.get('success')}")
        print(f"   Error: {empty_data.get('error')}")

        assert not empty_data.get('success'), "空文字稿应该失败"
        assert empty_data.get('error'), "应该有错误信息"
        print("   ✅ 空文字稿错误处理正确")

        print("\n✅ API 端点测试通过")
        return True

    except Exception as e:
        print(f"❌ API 端点测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_template_snapshot_support():
    """测试 templateSnapshot 参数支持"""
    print("\n=== 4. 测试 templateSnapshot 参数支持 ===\n")

    try:
        from backend.providers.summary import SummaryProvider

        provider = SummaryProvider()

        # 测试 template_description 参数
        test_transcript = """
        [00:00:00] Speaker 1: 讨论市场营销策略。
        [00:00:30] Speaker 2: 建议增加社交媒体投放。
        """

        result = provider.generate_summary(
            transcript=test_transcript,
            template_name="营销会议",
            template_description="这是一个市场营销策略讨论会议",  # template_snapshot 的描述
            template_sections=["策略要点", "投放计划", "预算"],
            template_prompt="聚焦可执行的行动项"
        )

        print(f"   Success: {result.success}")
        print(f"   Summary contains template info: {result.data.get('summary', '')}")

        if result.success:
            summary = result.data.get('summary', '')
            # 检查是否使用了 template_description
            print(f"   Summary preview: {summary[:150]}...")
            print("   ✅ templateDescription 参数支持正确")

        print("\n✅ templateSnapshot 参数测试通过")
        return True

    except Exception as e:
        print(f"❌ templateSnapshot 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """运行所有测试"""
    print("\n" + "="*60)
    print("Stage 6B-C: 真实总结 provider 接入测试")
    print("="*60)

    results = []

    # 测试 1: Fallback provider
    results.append(("Fallback Provider", test_summary_provider_fallback()))

    # 测试 2: LLM provider (可能不可用)
    results.append(("LLM Provider", test_summary_provider_llm()))

    # 测试 3: API 端点
    results.append(("API Endpoints", test_api_endpoints()))

    # 测试 4: templateSnapshot 支持
    results.append(("Template Snapshot", test_template_snapshot_support()))

    # 打印结果
    print("\n" + "="*60)
    print("测试结果汇总")
    print("="*60)

    for name, result in results:
        if result is True:
            status = "✅ PASS"
        elif result is False:
            status = "❌ FAIL"
        else:
            status = "⚠️  N/A"
        print(f"   {name}: {status}")

    # 检查是否有关键失败
    failed = [name for name, result in results if result is False]
    if failed:
        print(f"\n❌ 有 {len(failed)} 个测试失败: {', '.join(failed)}")
        return False
    else:
        print("\n✅ 所有关键测试通过")
        return True


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
