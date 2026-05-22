#!/usr/bin/env python3
"""
后端 API 验证脚本
使用 FastAPI TestClient 直接测试 API 路由
"""
import sys
import os
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "backend"))

def test_api_with_testclient():
    """使用 TestClient 测试 API"""
    print("\n=== FastAPI TestClient 测试 ===\n")

    try:
        from fastapi.testclient import TestClient
        from main import app

        client = TestClient(app)

        # 测试旧 health 端点
        print("1. 测试 /health:")
        response = client.get("/health")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")

        # 测试新 /api/v1/health 端点
        print("\n2. 测试 /api/v1/health:")
        response = client.get("/api/v1/health")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print(f"   Response: {response.json()}")
        else:
            print(f"   Error: {response.text}")

        # 测试 /api/v1/providers/info
        print("\n3. 测试 /api/v1/providers/info:")
        response = client.get("/api/v1/providers/info")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Transcription Provider: {data.get('transcription', {}).get('type')}")
            print(f"   Transcription Available: {data.get('transcription', {}).get('available')}")
            print(f"   Transcription Configured: {data.get('transcription', {}).get('configured')}")
            print(f"   Summary Provider: {data.get('summary', {}).get('type')}")
        else:
            print(f"   Error: {response.text}")

        # 测试 fallback 模式转录
        print("\n4. 测试 /api/v1/transcribe (fallback 模式):")

        # 创建一个临时音频文件（用于测试）
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio:
            temp_audio.write(b"fake audio content")
            temp_audio_path = temp_audio.name

        try:
            with open(temp_audio_path, "rb") as audio_file:
                files = {"file": ("test.wav", audio_file, "audio/wav")}
                data = {
                    "model_size": "base",
                    "language": "zh"
                }
                response = client.post("/api/v1/transcribe", files=files, data=data)

            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                print(f"   Success: {result.get('success')}")
                print(f"   Provider: {result.get('provider')}")
                print(f"   Is Fallback: {result.get('isFallback')}")
                print(f"   Has Transcript: {bool(result.get('transcript'))}")
                if result.get('metadata'):
                    print(f"   Metadata keys: {list(result.get('metadata', {}).keys())}")
            else:
                print(f"   Error: {response.text}")

        finally:
            # 清理临时文件
            os.unlink(temp_audio_path)

        print("\n✅ TestClient 测试完成")

    except ImportError as e:
        print(f"❌ 导入错误: {e}")
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_api_with_testclient()
