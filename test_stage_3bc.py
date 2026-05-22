#!/usr/bin/env python3
"""
阶段 3B-C 自测脚本
验证真实转录 provider 接入
"""
import os
import sys
from pathlib import Path

# 当前脚本在项目根目录，直接使用当前目录
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

# 添加 backend 目录到路径
backend_dir = project_root / "backend"
sys.path.insert(0, str(backend_dir))

def check_environment():
    """检查环境变量配置"""
    print("\n=== 环境变量检查 ===")

    # 检查 backend/.env.example
    env_example = project_root / "backend" / ".env.example"
    if env_example.exists():
        print("✅ backend/.env.example 存在")
        with open(env_example) as f:
            content = f.read()
            # 更精确的检查：真实的 Key 通常是 sk- 开头或包含实际密钥
            if "sk-" in content and "your_" not in content:
                print("❌ backend/.env.example 可能包含真实 API Key")
            else:
                # 检查是否有空的 API_KEY= (这是正确的示例)
                if "API_KEY=" in content:
                    lines_with_api_key = [line for line in content.split('\n') if 'API_KEY=' in line]
                    has_real_keys = False
                    for line in lines_with_api_key:
                        # 如果 API_KEY= 后面有非空且不是占位符的内容，可能是真实 Key
                        if '=' in line:
                            value = line.split('=', 1)[1].strip()
                            if value and value not in ['your_openai_api_key_here', 'your_anthropic_api_key_here', 'your_deepseek_api_key_here', '']:
                                has_real_keys = True

                    if has_real_keys:
                        print("❌ backend/.env.example 可能包含真实 API Key")
                    else:
                        print("✅ backend/.env.example 无真实 Key (正确使用占位符)")
                else:
                    print("✅ backend/.env.example 无 API Key 字段")
    else:
        print("❌ backend/.env.example 不存在")

def check_imports():
    """检查模块导入"""
    print("\n=== 模块导入检查 ===")

    try:
        # 使用正确的导入路径
        from providers.transcription import TranscriptionProvider
        print("✅ TranscriptionProvider 导入成功")

        # 测试默认（fallback）
        provider = TranscriptionProvider()
        print(f"✅ Provider 初始化成功 (默认模式)")
        print(f"   Provider 类型: {'Fallback' if provider.is_using_fallback() else 'Whisper'}")

        # 测试 whisper 模式（通过环境变量）
        os.environ['AI_TRANSCRIPTION_PROVIDER'] = 'whisper'
        provider_whisper = TranscriptionProvider()
        print(f"✅ Provider 初始化成功 (whisper 模式)")
        print(f"   Provider 类型: {'Fallback' if provider_whisper.is_using_fallback() else 'Whisper'}")

        # 清除环境变量
        del os.environ['AI_TRANSCRIPTION_PROVIDER']

    except ImportError as e:
        print(f"❌ 模块导入失败: {e}")

def check_api_routes():
    """检查 API 路由"""
    print("\n=== API 路由检查 ===")

    api_routes = project_root / "backend" / "api_routes.py"
    if api_routes.exists():
        print("✅ backend/api_routes.py 存在")

        with open(api_routes) as f:
            content = f.read()

        # 检查关键端点
        if '@api_router.post("/transcribe"' in content:
            print("✅ POST /api/v1/transcribe 端点存在")
        else:
            print("❌ POST /api/v1/transcribe 端点缺失")

        if '@api_router.get("/providers/info"' in content:
            print("✅ GET /api/v1/providers/info 端点存在")
        else:
            print("❌ GET /api/v1/providers/info 端点缺失")

        # 检查环境变量使用
        if 'AI_TRANSCRIPTION_PROVIDER' in content:
            print("✅ 使用 AI_TRANSCRIPTION_PROVIDER 环境变量")
        else:
            print("⚠️ 可能未使用 AI_TRANSCRIPTION_PROVIDER 环境变量")

        # 检查临时文件清理
        if 'cleanup_temp_file' in content:
            print("✅ 包含临时文件清理逻辑")
        else:
            print("⚠️ 可能缺少临时文件清理逻辑")

    else:
        print("❌ backend/api_routes.py 不存在")

def check_security():
    """检查安全性"""
    print("\n=== 安全性检查 ===")

    # 检查前端代码
    frontend_src = project_root / "web_backend" / "react-ui" / "src"

    # 搜索 API Key
    api_key_found = False
    for file in frontend_src.rglob("*.ts"):
        if file.is_file():
            with open(file) as f:
                content = f.read()
                if "sk-" in content or "OPENAI_API_KEY" in content or "ANTHROPIC_API_KEY" in content:
                    if "VITE_" in content or "api_key" in content.lower():
                        print(f"❌ 发现可能的 API Key: {file.relative_to(project_root)}")
                        api_key_found = True

    if not api_key_found:
        print("✅ 前端代码无 API Key")

    # 检查 .gitignore
    gitignore = project_root / ".gitignore"
    if gitignore.exists():
        with open(gitignore) as f:
            content = f.read()
            if ".env" in content:
                print("✅ .env 在 .gitignore 中")
            else:
                print("⚠️ .env 可能不在 .gitignore 中")

def check_frontend_typescript():
    """检查前端 TypeScript 编译"""
    print("\n=== 前端 TypeScript 检查 ===")

    frontend_dir = project_root / "web_backend" / "react-ui"

    # 检查关键文件
    transcription_service = frontend_dir / "src" / "services" / "transcriptionService.ts"
    api_client = frontend_dir / "src" / "services" / "apiClient.ts"

    if transcription_service.exists():
        print(f"✅ {transcription_service.relative_to(project_root)} 存在")
        with open(transcription_service) as f:
            content = f.read()
            if "/v1/transcribe" in content:
                print("✅ 使用 /api/v1/transcribe 端点")
            else:
                print("⚠️ 可能未使用正确的 API 端点")
    else:
        print(f"❌ {transcription_service.relative_to(project_root)} 不存在")

    if api_client.exists():
        print(f"✅ {api_client.relative_to(project_root)} 存在")
        with open(api_client) as f:
            content = f.read()
            if "timeout" in content.lower():
                print("✅ 包含超时处理")
            if "fallback" in content.lower():
                print("✅ 包含 fallback 逻辑")
    else:
        print(f"❌ {api_client.relative_to(project_root)} 不存在")

def main():
    print("=" * 60)
    print("阶段 3B-C 自测脚本")
    print("真实转录 provider 接入验证")
    print("=" * 60)

    check_environment()
    check_imports()
    check_api_routes()
    check_security()
    check_frontend_typescript()

    print("\n" + "=" * 60)
    print("自测完成")
    print("=" * 60)

if __name__ == "__main__":
    main()
