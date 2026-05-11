#!/usr/bin/env python3
"""
依赖检查工具

检查系统是否满足运行要求：
- Python 版本
- FFmpeg
- 必需的 Python 包
"""
import sys
import subprocess
import platform
from pathlib import Path
from typing import List, Tuple, Optional


class DependencyChecker:
    """依赖检查器"""

    def __init__(self):
        self.platform = platform.system()
        self.python_version = sys.version_info
        self.issues: List[str] = []
        self.warnings: List[str] = []

    def check_all(self) -> bool:
        """
        执行所有检查

        Returns:
            True 如果所有必需项都满足
        """
        print("🔍 检查系统依赖...\n")

        self._check_python_version()
        self._check_ffmpeg()
        self._check_pip()

        # 显示结果
        self._print_results()

        return len(self.issues) == 0

    def _check_python_version(self) -> None:
        """检查 Python 版本"""
        min_version = (3, 10)

        print(f"📌 Python 版本: {self.python_version.major}.{self.python_version.minor}.{self.python_version.micro}")

        if self.python_version < min_version:
            self.issues.append(
                f"Python 版本过低：需要 {min_version[0]}.{min_version[1]}+，"
                f"当前 {self.python_version.major}.{self.python_version.minor}"
            )
        else:
            print("   ✅ Python 版本满足要求\n")

    def _check_ffmpeg(self) -> None:
        """检查 FFmpeg 是否安装"""
        print("📌 FFmpeg:")

        try:
            result = subprocess.run(
                ["ffmpeg", "-version"],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                # 解析版本
                first_line = result.stdout.split('\n')[0]
                print(f"   ✅ {first_line}\n")
            else:
                self.issues.append("FFmpeg 未正确安装")

        except FileNotFoundError:
            self.issues.append("FFmpeg 未安装")
            print("   ❌ FFmpeg 未找到")

            # 提供安装建议
            if self.platform == "Linux":
                print("   💡 安装: sudo apt-get install ffmpeg")
            elif self.platform == "Darwin":  # macOS
                print("   💡 安装: brew install ffmpeg")
            elif self.platform == "Windows":
                print("   💡 安装: 从 https://ffmpeg.org/download.html 下载")
            print()

        except subprocess.TimeoutExpired:
            self.warnings.append("FFmpeg 命令超时")
            print("   ⚠️  FFmpeg 命令超时\n")

    def _check_pip(self) -> None:
        """检查 pip 是否可用"""
        print("📌 pip:")

        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                version = result.stdout.strip()
                print(f"   ✅ {version}\n")
            else:
                self.issues.append("pip 未正确安装")

        except FileNotFoundError:
            self.issues.append("pip 未安装")
            print("   ❌ pip 未找到\n")

        except subprocess.TimeoutExpired:
            self.warnings.append("pip 命令超时")
            print("   ⚠️  pip 命令超时\n")

    def _print_results(self) -> None:
        """打印检查结果"""
        if not self.issues and not self.warnings:
            print("✅ 所有依赖检查通过！\n")
            return

        if self.warnings:
            print("\n⚠️  警告:")
            for warning in self.warnings:
                print(f"   - {warning}")
            print()

        if self.issues:
            print("\n❌ 发现问题:")
            for issue in self.issues:
                print(f"   - {issue}")
            print()

    def get_install_command(self) -> Optional[str]:
        """
        获取安装命令

        Returns:
            安装命令字符串
        """
        if self.platform == "Linux":
            return "sudo apt-get update && sudo apt-get install -y ffmpeg python3-pip"
        elif self.platform == "Darwin":  # macOS
            return "brew install ffmpeg"
        elif self.platform == "Windows":
            return "请从 https://ffmpeg.org/download.html 下载并安装 FFmpeg"
        return None


def main():
    """主函数"""
    print("=" * 60)
    print("  AI Meeting Assistant - 依赖检查")
    print("=" * 60)
    print()

    checker = DependencyChecker()
    success = checker.check_all()

    if not success:
        print("\n💡 请先解决上述问题后再运行安装程序。\n")
        return 1

    print("🚀 系统满足要求，可以继续安装！\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
