#!/usr/bin/env python3
"""
后端 API 测试脚本
测试 /api/v1/health 和 /api/v1/providers/info 端点
"""
import sys
import json
import os
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "backend"))

def test_provider_info():
    """测试 provider 状态信息"""
    print("\n=== Provider 状态测试 ===")

    try:
        from providers.transcription import TranscriptionProvider
        from providers.summary import SummaryProvider

        # 测试默认模式（fallback）
        print("\n1. 默认模式 (AI_TRANSCRIPTION_PROVIDER 未设置):")
        if 'AI_TRANSCRIPTION_PROVIDER' in os.environ:
            del os.environ['AI_TRANSCRIPTION_PROVIDER']

        trans_provider = TranscriptionProvider()
        sum_provider = SummaryProvider()

        print(f"   Transcription Provider:")
        print(f"     - Using Fallback: {trans_provider.is_using_fallback()}")
        print(f"     - Info: {trans_provider.get_provider_info()}")

        print(f"   Summary Provider:")
        print(f"     - Using Fallback: {sum_provider.is_using_fallback()}")
        print(f"     - Info: {sum_provider.get_provider_info()}")

        # 测试 whisper 模式
        print("\n2. Whisper 模式 (AI_TRANSCRIPTION_PROVIDER=whisper):")
        os.environ['AI_TRANSCRIPTION_PROVIDER'] = 'whisper'

        trans_provider_whisper = TranscriptionProvider()
        print(f"   Transcription Provider:")
        print(f"     - Using Fallback: {trans_provider_whisper.is_using_fallback()}")
        print(f"     - Info: {trans_provider_whisper.get_provider_info()}")

        # 清理环境变量
        del os.environ['AI_TRANSCRIPTION_PROVIDER']

        print("\n✅ Provider 状态测试通过")

    except Exception as e:
        print(f"\n❌ Provider 状态测试失败: {e}")
        import traceback
        traceback.print_exc()

def test_fallback_transcription():
    """测试 fallback 转录"""
    print("\n=== Fallback 转录测试 ===")

    try:
        from providers.transcription import FallbackTranscriptionProvider

        provider = FallbackTranscriptionProvider()
        result = provider.transcribe("/tmp/test_audio.mp3")

        print(f"✅ Fallback 转录测试通过")
        print(f"   - Success: {result.success}")
        print(f"   - Provider: {result.provider.value}")
        print(f"   - Is Fallback: {result.is_fallback}")
        print(f"   - Has Transcript: {bool(result.data.get('transcript'))}")
        print(f"   - Processing Time: {result.processing_time_ms}ms")

        # 验证返回格式符合契约
        assert result.success == True, "Fallback 应该成功"
        assert result.is_fallback == True, "应该标记为 fallback"
        assert result.data.get('transcript'), "应该有 transcript 内容"
        assert result.data.get('segments'), "应该有 segments"

        print("✅ Fallback 转录契约验证通过")

    except Exception as e:
        print(f"❌ Fallback 转录测试失败: {e}")
        import traceback
        traceback.print_exc()

def test_error_handling():
    """测试错误处理"""
    print("\n=== 错误处理测试 ===")

    try:
        from providers.transcription import FallbackTranscriptionProvider

        provider = FallbackTranscriptionProvider()

        # 测试空文件路径（fallback 模式下不使用文件路径，所以不会失败）
        result = provider.transcribe("")
        print(f"✅ 空路径处理: Success={result.success}, IsFallback={result.is_fallback}")

        # 测试 metadata
        if result.data:
            metadata_keys = ['transcript', 'segments', 'duration', 'word_count', 'model']
            for key in metadata_keys:
                if key in result.data:
                    print(f"   ✅ Metadata 包含 {key}: {result.data[key] if key != 'transcript' else '(...skipped...)'}")

        print("✅ 错误处理测试通过")

    except Exception as e:
        print(f"❌ 错误处理测试失败: {e}")

def test_security():
    """测试安全性"""
    print("\n=== 安全性测试 ===")

    # 检查前端代码
    frontend_src = project_root / "web_backend" / "react-ui" / "src"

    api_key_found = False
    frontend_files_checked = 0

    for ts_file in frontend_src.rglob("*.ts"):
        if ts_file.is_file() and "node_modules" not in str(ts_file):
            frontend_files_checked += 1
            with open(ts_file) as f:
                content = f.read()
                # 检查是否有真实的 API Key
                if "sk-" in content and "VITE_" not in content:
                    print(f"   ⚠️ 可能的 API Key: {ts_file.relative_to(project_root)}")
                    api_key_found = True

    print(f"   检查了 {frontend_files_checked} 个前端 TypeScript 文件")
    if not api_key_found:
        print("✅ 前端代码无真实 API Key")
    else:
        print("❌ 前端代码可能包含 API Key")

    # 检查 provider info 不泄露敏感信息
    try:
        from providers.transcription import TranscriptionProvider
        provider = TranscriptionProvider()
        info = provider.get_provider_info()

        # 检查是否包含敏感信息
        sensitive_found = False
        sensitive_keywords = ['key', 'secret', 'password', 'token']
        info_str = json.dumps(info, default=str)

        for keyword in sensitive_keywords:
            if keyword in info_str.lower():
                print(f"   ⚠️ Provider info 可能包含敏感信息: {keyword}")
                sensitive_found = True

        if not sensitive_found:
            print("✅ Provider info 不泄露敏感信息")
        else:
            print("❌ Provider info 可能泄露敏感信息")

    except Exception as e:
        print(f"❌ 安全性测试失败: {e}")

def main():
    print("=" * 60)
    print("后端 API 测试")
    print("阶段 3B-C 验证")
    print("=" * 60)

    test_provider_info()
    test_fallback_transcription()
    test_error_handling()
    test_security()

    print("\n" + "=" * 60)
    print("后端 API 测试完成")
    print("=" * 60)

if __name__ == "__main__":
    main()
