#!/usr/bin/env python3
"""
AI 会议内容理解助手 - 启动脚本

支持真实音视频文件转录和 LLM 总结。
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 加载 .env（可选）
def load_env_file():
    """手动加载 .env 文件（不依赖 dotenv 库）"""
    env_path = project_root / ".env"
    if not env_path.exists():
        return
    
    try:
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # 跳过注释和空行
                if not line or line.startswith('#'):
                    continue
                # 解析 key=value
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    # 只设置未设置的环境变量
                    if key not in os.environ:
                        os.environ[key] = value
    except Exception as e:
        # 静默失败，不影响程序运行
        pass

# 加载环境变量
load_env_file()

if __name__ == "__main__":
    import argparse

    # 从环境变量读取默认 provider
    DEFAULT_LLM = os.environ.get("DEFAULT_LLM_PROVIDER", "glm")

    parser = argparse.ArgumentParser(
        description="AI 会议内容理解助手",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python meeting_cli.py                # 使用默认 LLM（智谱 AI）
  python meeting_cli.py --llm mock      # 使用 Mock LLM（演示）
  python meeting_cli.py --llm glm       # 使用智谱 AI
  python meeting_cli.py --llm openai    # 使用 OpenAI

环境变量 (.env 文件):
  ZHIPU_API_KEY        智谱 AI API Key
  OPENAI_API_KEY       OpenAI API Key
  ANTHROPIC_API_KEY    Anthropic API Key
  DEFAULT_LLM_PROVIDER 默认 LLM 提供商 (glm/openai/anthropic/mock)
  DEFAULT_LLM_MODEL    默认模型名称
  WHISPER_MODEL        Whisper 模型大小 (tiny/base/small/medium/large)
        """
    )

    parser.add_argument(
        "--llm", "-l",
        default=DEFAULT_LLM,
        choices=["mock", "glm", "openai", "anthropic"],
        help=f"LLM 提供商（默认: {DEFAULT_LLM}）"
    )

    args = parser.parse_args()

    from meeting_intelligence.cli import main
    main(llm_provider=args.llm)
