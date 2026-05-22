#!/usr/bin/env python3
"""
阶段 10A：全链路 E2E 回归测试
"""
import sys
import os
from pathlib import Path
import tempfile
import json

# 添加项目路径
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "backend"))

def test_health_endpoint():
    """测试 /api/v1/health"""
    print("\n=== 1. 测试 /api/v1/health ===")
    from fastapi.testclient import TestClient
    from backend.main import app

    client = TestClient(app)
    response = client.get("/api/v1/health")

    print(f"   Status: {response.status_code}")
    assert response.status_code == 200

    data = response.json()
    print(f"   status: {data.get('status')}")
    print(f"   service: {data.get('service')}")
    print(f"   transcriptionFallback: {data.get('transcriptionFallback')}")
    print(f"   summaryFallback: {data.get('summaryFallback')}")

    # 检查不泄露环境变量
    response_str = str(data)
    assert 'api_key' not in response_str.lower()
    assert 'sk-' not in response_str
    print("   ✅ 不泄露敏感信息")

    return True


def test_providers_info():
    """测试 /api/v1/providers/info"""
    print("\n=== 2. 测试 /api/v1/providers/info ===")
    from fastapi.testclient import TestClient
    from backend.main import app

    client = TestClient(app)
    response = client.get("/api/v1/providers/info")

    print(f"   Status: {response.status_code}")
    assert response.status_code == 200

    data = response.json()
    transcription = data.get('transcription', {})
    summary = data.get('summary', {})

    print(f"\n   Transcription:")
    print(f"     type: {transcription.get('type')}")
    print(f"     available: {transcription.get('available')}")
    print(f"     configured: {transcription.get('configured')}")
    print(f"     model: {transcription.get('model', 'N/A')}")

    print(f"\n   Summary:")
    print(f"     type: {summary.get('type')}")
    print(f"     available: {summary.get('available')}")
    print(f"     configured: {summary.get('configured')}")
    print(f"     model: {summary.get('model', 'N/A')}")

    # 检查不泄露 Key
    summary_str = str(summary)
    assert 'api_key' not in summary_str.lower()
    assert 'sk-' not in summary_str
    print("   ✅ 不泄露 API Key")

    # 确认有 model 字段
    assert 'model' in summary or summary.get('type') == 'fallback'
    print("   ✅ summary.model 字段存在")

    return True


def test_transcribe_fallback():
    """测试 fallback 转录"""
    print("\n=== 3. 测试 fallback 转录 ===")
    from fastapi.testclient import TestClient
    from backend.main import app

    client = TestClient(app)

    # 创建临时音频文件
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio:
        temp_audio.write(b"fake audio content for testing")
        temp_audio_path = temp_audio.name

    try:
        with open(temp_audio_path, "rb") as audio_file:
            files = {"file": ("test.wav", audio_file, "audio/wav")}
            response = client.post("/api/v1/transcribe", files=files)

        print(f"   Status: {response.status_code}")
        assert response.status_code == 200

        data = response.json()
        print(f"   success: {data.get('success')}")
        print(f"   provider: {data.get('provider')}")
        print(f"   isFallback: {data.get('isFallback')}")

        if data.get('metadata'):
            metadata = data.get('metadata')
            print(f"   metadata.processedAt: {metadata.get('processedAt')}")
            print(f"   metadata.model: {metadata.get('model')}")
            assert 'processedAt' in metadata
            assert 'processed_at' not in metadata
            print("   ✅ metadata 字段命名正确（camelCase）")

        # 检查不泄露路径
        response_str = str(data)
        assert temp_audio_path not in response_str
        print("   ✅ 不泄露临时文件路径")

        return True

    finally:
        os.unlink(temp_audio_path)


def test_summarize_fallback():
    """测试 fallback 总结"""
    print("\n=== 4. 测试 fallback 总结 ===")
    from fastapi.testclient import TestClient
    from backend.main import app

    client = TestClient(app)

    # 强制使用 fallback
    os.environ['AI_SUMMARY_PROVIDER'] = 'fallback'

    # 重新导入以应用环境变量
    import importlib
    import backend.main
    importlib.reload(backend.main)
    from backend.main import app as app_fallback
    client_fallback = TestClient(app_fallback)

    response = client_fallback.post("/api/v1/summarize", json={
        "transcript": "这是一段测试文字稿，用于验证 fallback 总结功能是否正常工作。我们需要确保 fallback 模式能够生成基本的总结结构，包括会议概要和行动项等章节。",
        "template_name": "测试会议",
        "template_description": "测试会议",
        "template_sections": ["会议概要", "行动项"],
        "template_prompt": "简洁总结"
    })

    print(f"   Status: {response.status_code}")
    assert response.status_code == 200

    data = response.json()
    print(f"   success: {data.get('success')}")
    print(f"   provider: {data.get('provider')}")
    print(f"   isFallback: {data.get('isFallback')}")
    print(f"   templateName: {data.get('templateName')}")

    if data.get('metadata'):
        metadata = data.get('metadata')
        print(f"   metadata.processedAt: {metadata.get('processedAt')}")
        print(f"   metadata.model: {metadata.get('model')}")
        assert metadata.get('model') == 'fallback'
        print("   ✅ metadata.model = fallback")

    # 清理环境变量
    if 'AI_SUMMARY_PROVIDER' in os.environ:
        del os.environ['AI_SUMMARY_PROVIDER']

    return True


def test_summarize_empty_transcript():
    """测试空文字稿"""
    print("\n=== 5. 测试空文字稿 ===")
    from fastapi.testclient import TestClient
    from backend.main import app

    client = TestClient(app)

    response = client.post("/api/v1/summarize", json={
        "transcript": "",
        "template_name": "测试",
        "template_sections": ["章节1"],
        "template_prompt": "测试"
    })

    print(f"   Status: {response.status_code}")
    assert response.status_code == 200

    data = response.json()
    print(f"   success: {data.get('success')}")
    print(f"   error: {data.get('error')}")

    assert not data.get('success')
    assert '无文字稿' in data.get('error', '')
    print("   ✅ 空文字稿返回正确错误")

    return True


def test_summarize_short_transcript():
    """测试短文字稿"""
    print("\n=== 6. 测试短文字稿 ===")
    from fastapi.testclient import TestClient
    from backend.main import app

    client = TestClient(app)

    response = client.post("/api/v1/summarize", json={
        "transcript": "短",
        "template_name": "测试",
        "template_sections": ["章节1"],
        "template_prompt": "测试"
    })

    print(f"   Status: {response.status_code}")
    assert response.status_code == 200

    data = response.json()
    print(f"   success: {data.get('success')}")
    print(f"   error: {data.get('error')}")

    assert not data.get('success')
    assert '过少' in data.get('error', '')
    print("   ✅ 短文字稿返回正确错误")

    return True


def test_security_checks():
    """安全检查"""
    print("\n=== 7. 安全检查 ===")

    # 检查前端代码
    frontend_src = Path("web_backend/react-ui/src")
    has_key = False

    for py_file in frontend_src.rglob("*.ts"):
        content = py_file.read_text()
        if "sk-fdcd" in content or "VITE_OPENAI_API_KEY" in content:
            has_key = True
            print(f"   ❌ 发现 API Key: {py_file}")

    if not has_key:
        print("   ✅ 前端代码无 API Key")

    # 检查 .env.example
    env_example = Path("backend/.env.example")
    if env_example.exists():
        content = env_example.read_text()
        has_real_key = "sk-fdcd" in content or "sk-ant" in content
        if not has_real_key:
            print("   ✅ .env.example 无真实 Key")
        else:
            print("   ❌ .env.example 包含真实 Key")

    # 检查 .gitignore
    gitignore = Path(".gitignore")
    if gitignore.exists():
        content = gitignore.read_text()
        if ".env" in content:
            print("   ✅ .gitignore 包含 .env")
        else:
            print("   ❌ .gitignore 不包含 .env")

    return True


def test_api_contracts():
    """API 契约测试"""
    print("\n=== 8. API 契约验证 ===")
    from fastapi.testclient import TestClient
    from backend.main import app

    client = TestClient(app)

    # 测试 summarize 的完整契约
    response = client.post("/api/v1/summarize", json={
        "transcript": "测试文字稿内容，用于验证 API 契约是否正确返回所有必需字段。",
        "template_name": "契约测试",
        "template_description": "API 契约验证",
        "template_sections": ["测试章节"],
        "template_prompt": "验证"
    })

    data = response.json()

    # 检查所有必需字段
    required_fields = ["success", "provider", "isFallback"]
    for field in required_fields:
        assert field in data, f"缺少字段: {field}"
        print(f"   ✅ 有字段: {field}")

    if data.get('success'):
        assert "summary" in data
        assert "metadata" in data
        assert "processedAt" in data.get("metadata", {})
        assert "model" in data.get("metadata", {})
        print("   ✅ 成功响应包含 summary 和 metadata")
    else:
        assert "error" in data
        assert "metadata" in data
        print("   ✅ 失败响应包含 error 和 metadata")

    # 检查不返回 prompt
    assert "template_prompt" not in data
    print("   ✅ 不返回完整 prompt")

    return True


def run_all_tests():
    """运行所有测试"""
    print("="*60)
    print("阶段 10A：全链路 E2E 回归测试")
    print("="*60)

    tests = [
        ("健康检查", test_health_endpoint),
        ("Provider 信息", test_providers_info),
        ("Fallback 转录", test_transcribe_fallback),
        ("Fallback 总结", test_summarize_fallback),
        ("空文字稿验证", test_summarize_empty_transcript),
        ("短文字稿验证", test_summarize_short_transcript),
        ("安全检查", test_security_checks),
        ("API 契约", test_api_contracts),
    ]

    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, "✅ PASS" if result else "❌ FAIL"))
        except Exception as e:
            results.append((name, f"❌ FAIL: {str(e)}"))
            print(f"   错误: {e}")

    # 打印结果
    print("\n" + "="*60)
    print("测试结果汇总")
    print("="*60)
    for name, result in results:
        print(f"   {name}: {result}")

    all_pass = all("✅ PASS" in r for _, r in results)
    return all_pass


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
