"""
Configuration management module.

提供配置文件加载、保存和管理功能。
"""

import os
import yaml
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional, Dict, Any


# 默认配置文件路径
DEFAULT_CONFIG_DIR = Path.home() / ".meeting-assistant"
DEFAULT_CONFIG_PATH = DEFAULT_CONFIG_DIR / "config.yaml"


# ============================================
# 配置数据类
# ============================================

@dataclass
class LLMConfig:
    """LLM 配置"""
    provider: str = "openai"
    model: str = "gpt-3.5-turbo"
    api_key_env: str = "OPENAI_API_KEY"
    timeout: int = 120
    max_retries: int = 3

    def __post_init__(self):
        """验证配置"""
        valid_providers = ["openai", "anthropic"]
        if self.provider not in valid_providers:
            raise ValueError(f"Invalid LLM provider: {self.provider}")


@dataclass
class ASRConfig:
    """ASR 配置"""
    provider: str = "whisper"
    model_size: str = "small"
    language: str = "auto"
    enable_postprocess: bool = True

    def __post_init__(self):
        """验证配置"""
        valid_models = ["tiny", "base", "small", "medium", "large", "large-v2", "large-v3"]
        if self.model_size not in valid_models:
            raise ValueError(f"Invalid Whisper model size: {self.model_size}")


@dataclass
class OutputConfig:
    """输出配置"""
    save_transcript: bool = True
    save_summary: bool = True
    output_dir: str = "data/output"
    formats: list = field(default_factory=lambda: ["json", "markdown"])


@dataclass
class Config:
    """主配置"""
    llm: LLMConfig = field(default_factory=LLMConfig)
    asr: ASRConfig = field(default_factory=ASRConfig)
    output: OutputConfig = field(default_factory=OutputConfig)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Config":
        """从字典创建配置"""
        llm_data = data.get('llm', {})
        asr_data = data.get('asr', {})
        output_data = data.get('output', {})

        return cls(
            llm=LLMConfig(**llm_data) if llm_data else LLMConfig(),
            asr=ASRConfig(**asr_data) if asr_data else ASRConfig(),
            output=OutputConfig(**output_data) if output_data else OutputConfig()
        )

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'llm': asdict(self.llm),
            'asr': asdict(self.asr),
            'output': asdict(self.output)
        }

    @classmethod
    def from_file(cls, path: Path) -> "Config":
        """从文件加载配置"""
        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f) or {}

        return cls.from_dict(data)

    def to_file(self, path: Path):
        """保存配置到文件"""
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, 'w', encoding='utf-8') as f:
            yaml.dump(self.to_dict(), f, allow_unicode=True, default_flow_style=False)

    def get_api_key(self) -> Optional[str]:
        """获取当前配置的 API Key"""
        env_var = self.llm.api_key_env
        return os.environ.get(env_var)


# ============================================
# 全局配置实例
# ============================================

_config: Optional[Config] = None


def get_config(
    config_path: Optional[Path] = None,
    reload: bool = False
) -> Config:
    """
    获取配置（单例）

    Args:
        config_path: 配置文件路径（可选）
        reload: 是否重新加载

    Returns:
        Config 实例
    """
    global _config

    if _config is None or reload:
        # 尝试从多个位置加载配置
        paths_to_try = [
            config_path,
            Path(os.environ.get("MEETING_ASSISTANT_CONFIG", "")),
            DEFAULT_CONFIG_PATH,
            Path("config.yaml"),
        ]

        config_loaded = False
        for path in paths_to_try:
            if path and Path(path).exists():
                try:
                    _config = Config.from_file(Path(path))
                    config_loaded = True
                    break
                except Exception:
                    continue

        if not config_loaded:
            # 使用默认配置
            _config = Config()

    return _config


def init_config(config_path: Optional[Path] = None) -> Path:
    """
    初始化配置文件

    Args:
        config_path: 配置文件路径（可选）

    Returns:
        创建的配置文件路径
    """
    if config_path is None:
        config_path = DEFAULT_CONFIG_PATH

    config_path = Path(config_path)

    # 创建默认配置
    config = Config()
    config.to_file(config_path)

    return config_path


def get_default_config_content() -> str:
    """获取默认配置文件内容（用于初始化）"""
    config = Config()
    import yaml
    return yaml.dump(config.to_dict(), allow_unicode=True, default_flow_style=False)


# ============================================
# 环境变量辅助函数
# ============================================

def setup_env_from_config(config: Config):
    """
    根据配置设置环境变量

    Args:
        config: Config 实例
    """
    # 这里不直接设置 API Key（应该由用户设置）
    # 但可以设置其他配置

    if config.llm.provider:
        os.environ["DEFAULT_LLM_PROVIDER"] = config.llm.provider

    if config.llm.model:
        os.environ["DEFAULT_LLM_MODEL"] = config.llm.model

    if config.asr.model_size:
        os.environ["WHISPER_MODEL_SIZE"] = config.asr.model_size


# ============================================
# 命令行辅助
# ============================================

if __name__ == "__main__":
    # 测试代码
    print("默认配置:")
    print(get_default_config_content())
    print()
    print(f"配置文件位置: {DEFAULT_CONFIG_PATH}")
