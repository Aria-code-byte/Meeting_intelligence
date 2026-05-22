#!/usr/bin/env python3
"""
阶段 6B-C 最终验收补漏测试
"""
import sys
import os
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "backend"))

def test_api_response_structure():
    """测试 /api/v1/summarize 响应结构"""
    print("\n=== 测试 API 响应结构 ===\n")

    from fastapi.testclient import TestClient
    from backend.main import app

    client = TestClient(app)

    # 测试真实 provider
    print("1. 真实 provider 响应结构:")
    response = client.post("/api/v1/summarize", json={
        "transcript": """
        [00:00:00] 张三: 今天讨论项目进度。
        [00:00:30] 李四: 第一阶段已完成，进入第二阶段。
        [00:01:00] 王五: 下周五进行评审。
        """,
        "template_name": "项目进度会议",
        "template_description": "项目进度讨论",
        "template_sections": ["讨论要点", "下一步计划"],
        "template_prompt": "简洁总结"
    })

    if response.status_code == 200:
        data = response.json()
        print(f"   success: {data.get('success')}")
        print(f"   provider: {data.get('provider')}")
        print(f"   isFallback: {data.get('isFallback')}")
        print(f"   templateName: {data.get('templateName')}")
        print(f"   error: {data.get('error')}")

        if data.get('metadata'):
            metadata = data.get('metadata')
            print(f"   metadata.keys: {list(metadata.keys())}")
            print(f"   metadata.processedAt: {metadata.get('processedAt')}")
            print(f"   metadata.model: {metadata.get('model')}")
            print(f"   是否有 processed_at: {'processed_at' in metadata}")

        # 检查是否返回敏感信息
        response_str = str(data)
        print(f"   是否包含 API Key: {'api_key' in response_str.lower() or 'sk-' in response_str}")
        print(f"   是否包含完整 prompt: {'template_prompt' in response_str}")
        print(f"   是否包含环境变量: {'OPENAI_API_KEY' in response_str}")

    print("\n2. Fallback provider 响应结构:")
    os.environ['AI_SUMMARY_PROVIDER'] = 'fallback'

    # 需要重新创建 app 来应用新的环境变量
    import importlib
    import backend.main
    importlib.reload(backend.main)
    from backend.main import app as app_fallback
    client_fallback = TestClient(app_fallback)

    response = client_fallback.post("/api/v1/summarize", json={
        "transcript": "测试文字稿内容",
        "template_name": "测试",
        "template_description": "测试",
        "template_sections": ["章节1"],
        "template_prompt": "测试"
    })

    if response.status_code == 200:
        data = response.json()
        print(f"   success: {data.get('success')}")
        print(f"   provider: {data.get('provider')}")
        print(f"   isFallback: {data.get('isFallback')}")
        if data.get('metadata'):
            metadata = data.get('metadata')
            print(f"   metadata.processedAt: {metadata.get('processedAt')}")

    # 清理环境变量
    if 'AI_SUMMARY_PROVIDER' in os.environ:
        del os.environ['AI_SUMMARY_PROVIDER']


def test_transcript_validation():
    """测试 transcript 验证"""
    print("\n=== 测试 Transcript 验证 ===\n")

    from fastapi.testclient import TestClient
    from backend.main import app

    client = TestClient(app)

    # 空 transcript
    print("1. 空 transcript:")
    response = client.post("/api/v1/summarize", json={
        "transcript": "",
        "template_name": "测试",
        "template_sections": ["章节1"],
        "template_prompt": "测试"
    })
    data = response.json()
    print(f"   success: {data.get('success')}")
    print(f"   error: {data.get('error')}")

    # 短 transcript
    print("\n2. 短 transcript (<10字符):")
    response = client.post("/api/v1/summarize", json={
        "transcript": "短文本",
        "template_name": "测试",
        "template_sections": ["章节1"],
        "template_prompt": "测试"
    })
    data = response.json()
    print(f"   success: {data.get('success')}")
    print(f"   error: {data.get('error')}")


def test_provider_status():
    """测试 provider 状态接口"""
    print("\n=== 测试 Provider 状态接口 ===\n")

    from fastapi.testclient import TestClient
    from backend.main import app

    client = TestClient(app)

    response = client.get("/api/v1/providers/info")
    data = response.json()

    if 'summary' in data:
        summary = data['summary']
        print(f"   summary.type: {summary.get('type')}")
        print(f"   summary.available: {summary.get('available')}")
        print(f"   summary.configured: {summary.get('configured')}")
        print(f"   summary.config: {summary.get('config')}")

        # 检查是否泄漏敏感信息
        config_str = str(summary.get('config', {}))
        print(f"   config 是否包含 API Key: {'api_key' in config_str.lower() or 'sk-' in config_str}")


def test_template_snapshot():
    """测试 templateSnapshot 支持"""
    print("\n=== 测试 Template Snapshot 支持 ===\n")

    from backend.providers.summary import SummaryProvider

    provider = SummaryProvider()

    # 测试使用 templateSnapshot 参数
    result = provider.generate_summary(
        transcript="测试文字稿内容，用于验证 templateSnapshot 支持。",
        template_name="已删除模板的快照",
        template_description="这是一个已删除模板的快照",
        template_sections=["讨论要点", "行动项"],
        template_prompt="使用快照模板生成总结"
    )

    print(f"   success: {result.success}")
    if result.success:
        summary = result.data.get('summary', '')
        print(f"   是否包含模板名称: {'已删除模板的快照' in summary}")
        print(f"   templateName 是否被使用: {result.data.get('model')}")


def check_security():
    """安全检查"""
    print("\n=== 安全检查 ===\n")

    # 检查 .env.example
    env_example = Path('backend/.env.example')
    if env_example.exists():
        content = env_example.read_text()
        has_real_key = 'sk-fdcd' in content or 'sk-ant' in content
        print(f"   .env.example 是否包含真实 Key: {has_real_key}")

    # 检查前端环境变量
    frontend_env = Path('web_backend/react-ui/.env.example')
    if frontend_env.exists():
        content = frontend_env.read_text()
        has_vite_key = 'VITE_OPENAI_API_KEY' in content
        print(f"   前端是否有 VITE_OPENAI_API_KEY: {has_vite_key}")

    # 检查 .gitignore
    gitignore = Path('.gitignore')
    if gitignore.exists():
        content = gitignore.read_text()
        ignores_env = '.env' in content
        print(f"   .gitignore 是否包含 .env: {ignores_env}")


if __name__ == "__main__":
    print("="*60)
    print("阶段 6B-C 最终验收补漏测试")
    print("="*60)

    test_api_response_structure()
    test_transcript_validation()
    test_provider_status()
    test_template_snapshot()
    check_security()

    print("\n" + "="*60)
    print("测试完成")
    print("="*60)
