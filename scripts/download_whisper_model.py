#!/usr/bin/env python3
"""
Whisper 模型下载工具

将 Whisper 模型下载到项目本地目录 (data/models/whisper/)

用法:
    python scripts/download_whisper_model.py base
    python scripts/download_whisper_model.py small --mirror
"""

import argparse
import sys
from pathlib import Path


def download_with_mirror(model_size: str) -> bool:
    """
    使用国内镜像下载模型

    Args:
        model_size: 模型大小

    Returns:
        是否成功
    """
    print(f"正在从镜像下载 {model_size} 模型...")

    model_dir = Path(__file__).parent.parent / "data" / "models" / "whisper"
    model_dir.mkdir(parents=True, exist_ok=True)

    # 设置镜像环境变量
    import os
    os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

    try:
        import whisper
        model = whisper.load_model(model_size, download_root=str(model_dir))
        print(f"✓ 模型已保存到: {model_dir / f'{model_size}.pt'}")
        return True
    except Exception as e:
        print(f"✗ 下载失败: {e}")
        return False


def download_manually_guide(model_size: str) -> None:
    """
    显示手动下载指南
    """
    model_dir = Path(__file__).parent.parent / "data" / "models" / "whisper"
    model_dir.mkdir(parents=True, exist_ok=True)

    print("\n" + "=" * 60)
    print("手动下载步骤:")
    print("=" * 60)
    print()
    print("方法 1: 使用镜像站 wget/curl")
    print("-" * 40)
    mirror_url = f"https://hf-mirror.com/openai/whisper-large-v3/resolve/main/{model_size}.pt"
    print(f"cd {model_dir}")
    print(f"wget {mirror_url}")
    print()

    print("方法 2: 浏览器下载")
    print("-" * 40)
    print(f"1. 访问: https://hf-mirror.com/openai/whisper-large-v3/tree/main")
    print(f"2. 下载文件: {model_size}.pt")
    print(f"3. 将文件放到: {model_dir}")
    print()

    print("方法 3: 使用代理")
    print("-" * 40)
    print("export HF_ENDPOINT=https://hf-mirror.com")
    print("python scripts/download_whisper_model.py", model_size)
    print()


def main():
    parser = argparse.ArgumentParser(
        description="下载 Whisper 模型到项目本地目录"
    )
    parser.add_argument(
        "model_size",
        choices=["tiny", "base", "small", "medium", "large"],
        help="模型大小"
    )
    parser.add_argument(
        "--mirror",
        action="store_true",
        help="使用国内镜像 (hf-mirror.com)"
    )
    parser.add_argument(
        "--guide-only",
        action="store_true",
        help="仅显示手动下载指南"
    )

    args = parser.parse_args()

    if args.guide_only:
        download_manually_guide(args.model_size)
        return 0

    if args.mirror:
        success = download_with_mirror(args.model_size)
        return 0 if success else 1

    # 默认尝试直接下载
    print(f"正在下载 {args.model_size} 模型...")
    print("提示: 如果下载失败，请使用 --mirror 参数或 --guide-only 查看手动下载方法")
    print()

    model_dir = Path(__file__).parent.parent / "data" / "models" / "whisper"
    model_dir.mkdir(parents=True, exist_ok=True)

    try:
        import whisper
        model = whisper.load_model(args.model_size, download_root=str(model_dir))
        print(f"✓ 模型已保存到: {model_dir / f'{args.model_size}.pt'}")
        return 0
    except Exception as e:
        print(f"✗ 下载失败: {e}")
        print()
        download_manually_guide(args.model_size)
        return 1


if __name__ == "__main__":
    sys.exit(main())
