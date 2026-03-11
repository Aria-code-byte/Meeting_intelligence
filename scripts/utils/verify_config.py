#!/usr/bin/env python3
"""
配置验证脚本

验证所有 API 和环境配置是否正确。
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 加载 .env
env_path = project_root / '.env'
if env_path.exists():
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()

print("=" * 50)
print("  AI 会议助手 - 配置验证")
print("=" * 50)

# 1. 检查 .env 文件
print("\n[1] .env 文件检查")
if env_path.exists():
    print(f"✓ .env 文件存在: {env_path}")
else:
    print(f"✗ .env 文件不存在")

# 2. 检查环境变量
print("\n[2] 环境变量检查")
env_vars = {
    'ZHIPU_API_KEY': '智谱 AI API Key',
    'DEFAULT_LLM_PROVIDER': '默认 LLM 提供商',
    'DEFAULT_LLM_MODEL': '默认模型',
    'WHISPER_MODEL': 'Whisper 模型大小',
}

for key, desc in env_vars.items():
    value = os.environ.get(key)
    if value:
        if 'KEY' in key:
            print(f"✓ {desc}: {value[:15]}...")
        else:
            print(f"✓ {desc}: {value}")
    else:
        print(f"✗ {desc}: 未设置")

# 3. 验证 LLM Provider
print("\n[3] LLM Provider 验证")
try:
    from meeting_intelligence.cli import create_llm_provider

    # 测试智谱 AI
    if os.environ.get('ZHIPU_API_KEY'):
        try:
            llm = create_llm_provider('glm')
            print(f"✓ 智谱 AI GLMProvider 创建成功")
        except Exception as e:
            print(f"✗ 智谱 AI 失败: {e}")

    # 测试 Mock
    try:
        llm = create_llm_provider('mock')
        print(f"✓ Mock LLM Provider 创建成功")
    except Exception as e:
        print(f"✗ Mock 失败: {e}")

except ImportError as e:
    print(f"✗ 导入失败: {e}")

# 4. 验证默认配置
print("\n[4] 默认配置")
default_llm = os.environ.get('DEFAULT_LLM_PROVIDER', 'glm')
print(f"默认 LLM Provider: {default_llm}")

# 5. 输出目录
print("\n[5] 输出目录")
output_dir = project_root / 'data' / 'outputs'
output_dir.mkdir(parents=True, exist_ok=True)
print(f"✓ 输出目录: {output_dir}")

# 总结
print("\n" + "=" * 50)
print("  配置验证完成")
print("=" * 50)
print("\n使用方法:")
print("  python meeting_cli.py          # 使用默认 LLM（智谱 AI）")
print("  python meeting_cli.py --llm mock  # 使用 Mock LLM")
print()
