#!/usr/bin/env python3
"""
测试 whisper 模式转录
"""
import sys
import os
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "backend"))

def test_whisper_mode():
    """测试 whisper 模式"""
    print("\n=== Whisper 模式测试 ===\n")

    # 设置环境变量启用 whisper
    os.environ['AI_TRANSCRIPTION_PROVIDER'] = 'whisper'

    try:
        from fastapi.testclient import TestClient
        from main import app

        client = TestClient(app)

        # 测试 provider 状态
        print("1. 测试 /api/v1/providers/info (whisper 模式):")
        response = client.get("/api/v1/providers/info")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Transcription Provider: {data.get('transcription', {}).get('type')}")
            print(f"   Transcription Available: {data.get('transcription', {}).get('available')}")
            print(f"   Transcription Configured: {data.get('transcription', {}).get('configured')}")
            if data.get('transcription', {}).get('model'):
                print(f"   Transcription Model: {data.get('transcription', {}).get('model')}")
        else:
            print(f"   Error: {response.text}")

        # 测试转录
        print("\n2. 测试 /api/v1/transcribe (whisper 模式):")

        # 创建一个临时音频文件
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
                if result.get('error'):
                    print(f"   Error: {result.get('error')}")
                if result.get('metadata'):
                    metadata = result.get('metadata')
                    print(f"   Metadata.processedAt: {metadata.get('processedAt')}")
                    print(f"   Metadata.model: {metadata.get('model')}")
                    print(f"   Metadata keys: {list(metadata.keys())}")
            else:
                print(f"   Error: {response.text}")

        finally:
            # 清理临时文件
            os.unlink(temp_audio_path)

        print("\n✅ Whisper 模式测试完成")

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 清理环境变量
        if 'AI_TRANSCRIPTION_PROVIDER' in os.environ:
            del os.environ['AI_TRANSCRIPTION_PROVIDER']

if __name__ == "__main__":
    test_whisper_mode()
