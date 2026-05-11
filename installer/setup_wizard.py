#!/usr/bin/env python3
"""
AI Meeting Assistant - 配置向导

首次运行时引导用户完成基本配置：
1. 选择界面模式（CLI/Web）
2. 配置 LLM Provider
3. 输入 API Key（可选）
4. 下载 Whisper 模型
"""
import os
import sys
import json
import time
from pathlib import Path
from typing import Optional, Dict, Any


class SetupWizard:
    """配置向导"""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.env_path = self.project_root / ".env"
        self.config_path = self.project_root / "config.yaml"
        self.config: Dict[str, Any] = {}

    def run(self) -> bool:
        """
        运行配置向导

        Returns:
            True 如果配置成功
        """
        self._print_welcome()

        # Step 1: 选择界面模式
        interface_mode = self._select_interface_mode()
        if not interface_mode:
            return False
        self.config["interface_mode"] = interface_mode

        # Step 2: 选择 LLM Provider
        llm_provider = self._select_llm_provider()
        if not llm_provider:
            return False

        # Step 3: 配置 API Key（可选）
        api_key = self._input_api_key(llm_provider)
        self.config["llm_provider"] = llm_provider
        if api_key:
            self.config["llm_api_key"] = api_key

        # Step 4: Whisper 模型选择
        whisper_model = self._select_whisper_model()
        if whisper_model:
            self.config["whisper_model"] = whisper_model

        # Step 5: 保存配置
        self._save_config()

        # Step 6: 完成
        self._print_completion()

        return True

    def _print_welcome(self) -> None:
        """显示欢迎界面"""
        print("\n" + "=" * 60)
        print("  🎉 AI Meeting Assistant - 首次配置向导")
        print("=" * 60)
        print()
        print("欢迎使用 AI Meeting Assistant！")
        print("接下来将通过几个简单步骤完成配置。\n")
        print("预计用时: 2-3 分钟")
        print()

        time.sleep(1)

    def _select_interface_mode(self) -> Optional[str]:
        """选择界面模式"""
        print("=" * 60)
        print("  步骤 1/4: 选择界面模式")
        print("=" * 60)
        print()
        print("请选择您偏好的界面模式：\n")
        print("  [1] CLI 交互式菜单（推荐新手）")
        print("      → 菜单导航、拖拽文件上传、操作简单")
        print()
        print("  [2] Web 界面（推荐高级用户）")
        print("      → 浏览器访问、可视化操作、实时预览")
        print()

        while True:
            choice = input("请输入选择 [1-2]（默认: 1）: ").strip() or "1"

            if choice == "1":
                print("\n✅ 已选择: CLI 交互式菜单\n")
                return "cli"
            elif choice == "2":
                print("\n✅ 已选择: Web 界面\n")
                return "web"
            else:
                print("❌ 无效的选择，请输入 1 或 2\n")

    def _select_llm_provider(self) -> Optional[str]:
        """选择 LLM Provider"""
        print("=" * 60)
        print("  步骤 2/4: 选择 LLM 服务商")
        print("=" * 60)
        print()
        print("LLM 用于转录增强和会议总结。\n")

        providers = {
            "1": ("deepseek", "DeepSeek", "国产，速度快，价格优，推荐"),
            "2": ("glm", "智谱 GLM", "国产模型，稳定可靠"),
            "3": ("openai", "OpenAI GPT", "国际领先，需要国际网络"),
            "4": ("anthropic", "Anthropic Claude", "强大能力，需要国际网络"),
            "5": ("mock", "测试模式", "不使用真实 API，仅测试"),
        }

        print("请选择 LLM 服务商：\n")
        for key, (id, name, desc) in providers.items():
            default = "（默认）" if id == "deepseek" else ""
            print(f"  [{key}] {name}")
            print(f"      → {desc} {default}")
            print()

        while True:
            choice = input("请输入选择 [1-5]（默认: 1）: ").strip() or "1"

            if choice in providers:
                provider_id, name, _ = providers[choice]
                print(f"\n✅ 已选择: {name}\n")
                return provider_id
            else:
                print("❌ 无效的选择，请输入 1-5\n")

    def _input_api_key(self, provider: str) -> Optional[str]:
        """输入 API Key（可选）"""
        print("=" * 60)
        print("  步骤 3/4: 配置 API Key（可选）")
        print("=" * 60)
        print()

        if provider == "mock":
            print("ℹ️  测试模式不需要 API Key\n")
            return None

        provider_names = {
            "deepseek": "DeepSeek",
            "glm": "智谱 GLM",
            "openai": "OpenAI",
            "anthropic": "Anthropic Claude"
        }

        env_var_names = {
            "deepseek": "DEEPSEEK_API_KEY",
            "glm": "ZHIPU_API_KEY",
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY"
        }

        provider_name = provider_names.get(provider, provider)
        env_var = env_var_names.get(provider, f"{provider.upper()}_API_KEY")

        # 检查是否已配置
        existing_key = os.environ.get(env_var)
        if existing_key:
            print(f"✅ 检测到已配置的 {provider_name} API Key")
            use_existing = input("是否使用已配置的 Key？[Y/n]: ").strip().lower()
            if use_existing != 'n':
                print()
                return existing_key

        print(f"📝 {provider_name} API Key 配置")
        print()
        print("您可以：")
        print("  1. 现在输入 API Key")
        print("  2. 跳过，稍后在 .env 文件中配置")
        print()

        while True:
            api_key = input(f"请输入 {env_var}（留空跳过）: ").strip()

            if not api_key:
                print("\n⚠️  已跳过 API Key 配置")
                print("   稍后请在 .env 文件中配置，或使用环境变量\n")
                return None

            # 简单验证
            if len(api_key) < 10:
                print("❌ API Key 长度似乎不正确，请重新输入\n")
                continue

            print(f"\n✅ API Key 已配置（{api_key[:8]}...）\n")
            return api_key

    def _select_whisper_model(self) -> Optional[str]:
        """选择 Whisper 模型"""
        print("=" * 60)
        print("  步骤 4/4: 选择 Whisper 模型")
        print("=" * 60)
        print()
        print("Whisper 用于语音转文字（ASR）。\n")

        models = {
            "1": ("tiny", "~40MB", "最快，准确率较低"),
            "2": ("base", "~140MB", "平衡，推荐", "（默认）"),
            "3": ("small", "~460MB", "较准确"),
            "4": ("medium", "~1.5GB", "准确，较慢"),
            "5": ("large", "~2.9GB", "最准确，最慢"),
        }

        print("请选择 Whisper 模型大小：\n")
        for key, (name, size, desc, *extra) in models.items():
            extra_str = extra[0] if extra else ""
            print(f"  [{key}] {name:8} - {size:8} → {desc} {extra_str}")
            print()

        print("💡 提示：")
        print("  - 首次使用会自动下载模型")
        print("  - 模型会缓存到本地，后续无需重复下载")
        print("  - 如果网络不佳，推荐使用 base 模型\n")

        while True:
            choice = input("请输入选择 [1-5]（默认: 2）: ").strip() or "2"

            if choice in models:
                model_name, size, desc, *_ = models[choice]
                print(f"\n✅ 已选择: {model_name} 模型 ({size})\n")
                return model_name
            else:
                print("❌ 无效的选择，请输入 1-5\n")

    def _save_config(self) -> None:
        """保存配置到 .env 文件"""
        print("=" * 60)
        print("  保存配置")
        print("=" * 60)
        print()

        # 读取现有的 .env（如果存在）
        existing_env = {}
        if self.env_path.exists():
            with open(self.env_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        existing_env[key] = value

        # 更新配置
        llm_provider = self.config.get("llm_provider", "deepseek")

        # 环境变量映射
        env_vars = {
            "DEFAULT_LLM_PROVIDER": llm_provider,
            "WHISPER_MODEL_SIZE": self.config.get("whisper_model", "base"),
            "FIRST_RUN": "false",
        }

        # 添加 API Key（如果提供）
        if "llm_api_key" in self.config:
            if llm_provider == "deepseek":
                env_vars["DEEPSEEK_API_KEY"] = self.config["llm_api_key"]
            elif llm_provider == "glm":
                env_vars["ZHIPU_API_KEY"] = self.config["llm_api_key"]
            elif llm_provider == "openai":
                env_vars["OPENAI_API_KEY"] = self.config["llm_api_key"]
            elif llm_provider == "anthropic":
                env_vars["ANTHROPIC_API_KEY"] = self.config["llm_api_key"]

        # 保存配置（保留现有注释和其他配置）
        with open(self.env_path, 'w') as f:
            f.write("# AI Meeting Assistant - Environment Configuration\n")
            f.write("# Generated by setup wizard\n")
            f.write(f"# Generated at: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")

            # 写入配置
            for key, value in env_vars.items():
                if isinstance(value, str) and ' ' in value:
                    f.write(f'{key}="{value}"\n')
                else:
                    f.write(f'{key}={value}\n')

        print(f"✅ 配置已保存到: {self.env_path.name}\n")

        # 保存界面模式偏好
        config_file = self.project_root / ".config" / "preferences.json"
        config_file.parent.mkdir(exist_ok=True)
        with open(config_file, 'w') as f:
            json.dump({
                "interface_mode": self.config.get("interface_mode", "cli"),
                "configured_at": time.strftime('%Y-%m-%d %H:%M:%S')
            }, f, indent=2)
        print(f"✅ 界面偏好已保存\n")

    def _print_completion(self) -> None:
        """显示完成信息"""
        interface_mode = self.config.get("interface_mode", "cli")
        interface_desc = "CLI 交互式菜单" if interface_mode == "cli" else "Web 界面"

        print("\n" + "=" * 60)
        print("  ✅ 配置完成！")
        print("=" * 60)
        print()
        print("您的配置：")
        print(f"  • 界面模式: {interface_desc}")
        print(f"  • LLM 服务: {self.config.get('llm_provider', 'deepseek')}")
        print(f"  • Whisper 模型: {self.config.get('whisper_model', 'base')}")
        print()
        print("🚀 开始使用：")
        if interface_mode == "cli":
            print("   python -m meeting_intelligence.cli")
        else:
            print("   cd web_backend && streamlit run app.py")
        print()
        print("📖 文档: README.md")
        print()


def is_first_run() -> bool:
    """检查是否首次运行"""
    env_path = Path(__file__).parent.parent / ".env"
    if not env_path.exists():
        return True

    # 检查 FIRST_RUN 标记
    with open(env_path, 'r') as f:
        for line in f:
            if line.strip().startswith('FIRST_RUN='):
                return 'false' not in line.lower()

    return True


def main():
    """主函数"""
    if not is_first_run():
        print("✅ 已经完成过初始配置")
        print("   如需重新配置，请删除 .env 文件后重新运行\n")
        return 0

    wizard = SetupWizard()
    success = wizard.run()

    if success:
        return 0
    else:
        print("\n❌ 配置已取消\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
