"""
总结服务
"""

import os
from typing import Optional, Dict, Any, List

from .providers.base import ProviderResult
from .providers.fallback import FallbackSummaryProvider
from .providers.llm import LLMSummaryProvider


class SummaryService:
    """总结服务（工厂模式）"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._init_provider()

    def _init_provider(self):
        """初始化提供商（基于环境变量）"""
        # 从环境变量读取 provider 类型
        provider_type = os.getenv("AI_SUMMARY_PROVIDER", "fallback").lower()

        print(f"[SummaryService] Initializing with provider: {provider_type}")

        if provider_type == "fallback":
            # 强制使用 fallback
            print(f"[SummaryService] Using fallback (forced)")
            self.provider = FallbackSummaryProvider(self.config)
        elif provider_type in ["deepseek", "backend"]:
            # 尝试使用 LLM
            llm_provider = LLMSummaryProvider(self.config)

            if llm_provider.is_available():
                self.provider = llm_provider
                print(f"[SummaryService] Using LLM provider: {provider_type}")
            else:
                print(f"[SummaryService] LLM unavailable, falling back")
                self.provider = FallbackSummaryProvider(self.config)
        else:
            print(f"[SummaryService] Unknown provider: {provider_type}, falling back")
            self.provider = FallbackSummaryProvider(self.config)

    def generate_summary(
        self,
        transcript: str,
        template_name: str,
        template_sections: List[str],
        template_prompt: str,
        **kwargs
    ) -> ProviderResult:
        """生成总结"""
        return self.provider.generate_summary(
            transcript=transcript,
            template_name=template_name,
            template_sections=template_sections,
            template_prompt=template_prompt,
            **kwargs
        )

    def get_provider_info(self) -> Dict[str, Any]:
        """获取提供商信息"""
        info = self.provider.get_provider_info()
        # 添加模型信息
        if hasattr(self.provider, 'llm_client') and self.provider.llm_client:
            info['llm_provider'] = self.provider.llm_client.provider
        return info

    def is_using_fallback(self) -> bool:
        """是否使用回退模式"""
        return isinstance(self.provider, FallbackSummaryProvider)
