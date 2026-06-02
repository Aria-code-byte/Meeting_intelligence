"""
总结提供商基类
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class ProviderType(str, Enum):
    """提供商类型"""
    FALLBACK = "fallback"
    BACKEND = "backend"


class ProviderResult:
    """提供商结果"""

    def __init__(
        self,
        success: bool,
        data: Optional[Dict[str, Any]],
        provider: ProviderType,
        is_fallback: bool,
        error: Optional[str] = None,
        processing_time_ms: int = 0
    ):
        self.success = success
        self.data = data or {}
        self.provider = provider
        self.is_fallback = is_fallback
        self.error = error
        self.processing_time_ms = processing_time_ms


class BaseSummaryProvider(ABC):
    """总结提供商基类"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.provider_type = ProviderType.FALLBACK

    @abstractmethod
    def generate_summary(
        self,
        transcript: str,
        template_name: str,
        template_sections: List[str],
        template_prompt: str,
        **kwargs
    ) -> ProviderResult:
        """生成总结"""
        pass

    def get_provider_info(self) -> Dict[str, Any]:
        """获取提供商信息"""
        return {
            "type": self.provider_type,
            "config": self.config
        }
