"""
Base Provider Interface
====================
所有AI服务提供商的基类
"""
from typing import Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum


class ProviderType(str, Enum):
    """提供商类型"""
    FALLBACK = "fallback"
    BACKEND = "backend"
    MANUAL = "manual"


@dataclass
class ProviderResult:
    """统一的服务结果"""
    success: bool
    data: Any
    provider: ProviderType
    is_fallback: bool
    error: Optional[str] = None
    processing_time_ms: Optional[int] = None


class BaseProvider:
    """AI服务提供商基类"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.provider_type = ProviderType.FALLBACK

    def is_available(self) -> bool:
        """检查服务是否可用"""
        return True

    def get_provider_info(self) -> Dict[str, Any]:
        """获取提供商信息"""
        return {
            "type": self.provider_type.value,
            "available": self.is_available(),
            "config": {k: "***" if "key" in k.lower() or "secret" in k.lower() else v
                      for k, v in self.config.items()}
        }
