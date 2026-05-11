"""
统一配置管理模块

提供配置的加载、保存、验证功能。
配置优先级: 命令行参数 > 环境变量 > 用户配置 > 默认配置
"""
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Union
from dataclasses import dataclass, field


@dataclass
class LLMConfig:
    """LLM 配置"""
    provider: str = "deepseek"  # 默认使用 DeepSeek
    model: str = ""
    api_key: Optional[str] = None
    timeout: int = 60
    max_retries: int = 3
    temperature: float = 0.3

    def __post_init__(self):
        """根据 provider 设置默认 model"""
        if not self.model:
            self.model = self._get_default_model()

    def _get_default_model(self) -> str:
        """获取 provider 的默认模型"""
        default_models = {
            "deepseek": "deepseek-chat",
            "glm": "glm-4-flash",
            "openai": "gpt-4o-mini",
            "anthropic": "claude-3-5-sonnet-20241022",
            "mock": "mock"
        }
        return default_models.get(self.provider, "deepseek-chat")


@dataclass
class ASRConfig:
    """ASR 配置"""
    provider: str = "faster-whisper"
    model: str = "base"
    device: str = "auto"  # auto, cpu, cuda
    language: str = "auto"
    speaker_diarization: bool = False  # 发言人识别（即将支持）


@dataclass
class UIConfig:
    """界面配置"""
    mode: str = "cli"  # cli, web
    theme: str = "default"
    show_progress: bool = True


@dataclass
class SystemConfig:
    """系统配置"""
    project_root: Path = field(default_factory=lambda: Path(__file__).parent.parent)
    cache_dir: Path = field(init=False)
    models_dir: Path = field(init=False)
    data_dir: Path = field(init=False)
    outputs_dir: Path = field(init=False)
    first_run: bool = field(init=False)

    def __post_init__(self):
        """初始化路径"""
        self.cache_dir = self.project_root / ".cache"
        self.models_dir = self.project_root / "data" / "models"
        self.data_dir = self.project_root / "data"
        self.outputs_dir = self.project_root / "data" / "outputs"
        self.first_run = self._check_first_run()

    def _check_first_run(self) -> bool:
        """检查是否首次运行"""
        env_path = self.project_root / ".env"
        if not env_path.exists():
            return True
        # 检查 FIRST_RUN 标记
        try:
            with open(env_path, 'r') as f:
                for line in f:
                    if 'FIRST_RUN' in line and 'false' in line.lower():
                        return False
        except Exception:
            pass
        return True


@dataclass
class Config:
    """统一配置"""
    llm: LLMConfig = field(default_factory=LLMConfig)
    asr: ASRConfig = field(default_factory=ASRConfig)
    ui: UIConfig = field(default_factory=UIConfig)
    system: SystemConfig = field(default_factory=SystemConfig)

    @classmethod
    def load(cls, config_path: Optional[Path] = None) -> "Config":
        """
        加载配置

        Args:
            config_path: 配置文件路径（可选）

        Returns:
            Config 实例
        """
        # 1. 创建默认配置
        config = cls()

        # 2. 从环境变量加载
        config._load_from_env()

        # 3. 从配置文件加载（如果提供）
        if config_path and config_path.exists():
            config._load_from_file(config_path)

        # 4. 验证配置
        config._validate()

        return config

    def _load_from_env(self) -> None:
        """从环境变量加载配置"""
        # LLM 配置
        if provider := os.environ.get("DEFAULT_LLM_PROVIDER"):
            self.llm.provider = provider
        if model := os.environ.get("DEFAULT_LLM_MODEL"):
            self.llm.model = model
        if api_key := os.environ.get("DEEPSEEK_API_KEY"):
            self.llm.api_key = api_key
        if api_key := os.environ.get("ZHIPU_API_KEY"):
            self.llm.api_key = api_key
        if api_key := os.environ.get("OPENAI_API_KEY"):
            self.llm.api_key = api_key
        if api_key := os.environ.get("ANTHROPIC_API_KEY"):
            self.llm.api_key = api_key

        # ASR 配置
        if model := os.environ.get("WHISPER_MODEL_SIZE"):
            self.asr.model = model

        # UI 配置
        if mode := os.environ.get("UI_MODE"):
            self.ui.mode = mode

    def _load_from_file(self, config_path: Path) -> None:
        """从配置文件加载"""
        try:
            import yaml
            with open(config_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}

            # 更新配置
            if llm_config := data.get("llm"):
                for key, value in llm_config.items():
                    if hasattr(self.llm, key):
                        setattr(self.llm, key, value)

            if asr_config := data.get("asr"):
                for key, value in asr_config.items():
                    if hasattr(self.asr, key):
                        setattr(self.asr, key, value)

            if ui_config := data.get("ui"):
                for key, value in ui_config.items():
                    if hasattr(self.ui, key):
                        setattr(self.ui, key, value)

        except ImportError:
            # yaml 未安装，跳过
            pass
        except Exception as e:
            print(f"警告: 加载配置文件失败 - {e}")

    def _validate(self) -> None:
        """验证配置"""
        # 验证 LLM provider
        valid_providers = {"deepseek", "glm", "openai", "anthropic", "mock"}
        if self.llm.provider not in valid_providers:
            raise ValueError(f"无效的 LLM provider: {self.llm.provider}")

        # 验证 Whisper 模型
        valid_models = {"tiny", "base", "small", "medium", "large"}
        if self.asr.model not in valid_models:
            raise ValueError(f"无效的 Whisper 模型: {self.asr.model}")

        # 验证 UI 模式
        if self.ui.mode not in {"cli", "web"}:
            raise ValueError(f"无效的 UI 模式: {self.ui.mode}")

    def save_env(self, env_path: Optional[Path] = None) -> None:
        """
        保存配置到 .env 文件

        Args:
            env_path: .env 文件路径（默认: 项目根目录/.env）
        """
        if env_path is None:
            env_path = self.system.project_root / ".env"

        env_vars = {
            "DEFAULT_LLM_PROVIDER": self.llm.provider,
            "DEFAULT_LLM_MODEL": self.llm.model,
            "WHISPER_MODEL_SIZE": self.asr.model,
            "UI_MODE": self.ui.mode,
            "FIRST_RUN": "false",
        }

        # 添加 API Key
        if self.llm.provider == "deepseek" and self.llm.api_key:
            env_vars["DEEPSEEK_API_KEY"] = self.llm.api_key
        elif self.llm.provider == "glm" and self.llm.api_key:
            env_vars["ZHIPU_API_KEY"] = self.llm.api_key
        elif self.llm.provider == "openai" and self.llm.api_key:
            env_vars["OPENAI_API_KEY"] = self.llm.api_key
        elif self.llm.provider == "anthropic" and self.llm.api_key:
            env_vars["ANTHROPIC_API_KEY"] = self.llm.api_key

        # 写入文件
        with open(env_path, 'w', encoding='utf-8') as f:
            f.write("# AI Meeting Assistant - Environment Configuration\n")
            f.write("# Generated by config_manager.py\n\n")

            for key, value in env_vars.items():
                if isinstance(value, str) and ' ' in value:
                    f.write(f'{key}="{value}"\n')
                else:
                    f.write(f'{key}={value}\n')


# 全局配置实例
_global_config: Optional[Config] = None


def get_config(reload: bool = False) -> Config:
    """
    获取全局配置实例

    Args:
        reload: 是否重新加载

    Returns:
        Config 实例
    """
    global _global_config

    if _global_config is None or reload:
        _global_config = Config.load()

    return _global_config


def reset_config() -> None:
    """重置全局配置"""
    global _global_config
    _global_config = None
