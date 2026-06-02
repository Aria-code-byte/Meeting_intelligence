"""
LLM 总结提供商（真实调用）
"""

import os
import time
from typing import Optional, Dict, Any, List
from datetime import datetime

from .base import BaseSummaryProvider, ProviderResult, ProviderType


class LLMSummaryProvider(BaseSummaryProvider):
    """LLM 总结提供商（真实调用）"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.provider_type = ProviderType.BACKEND
        self.llm_client = None
        self._init_llm_client()

    def _init_llm_client(self):
        """初始化 LLM 客户端"""
        try:
            from backend.llm_client import LLMClient
            self.llm_client = LLMClient()
        except ImportError:
            try:
                # Fallback for when running from backend/ directory
                from llm_client import LLMClient
                self.llm_client = LLMClient()
            except ImportError:
                self.llm_client = None

    def is_available(self) -> bool:
        """检查 LLM 是否可用"""
        return self.llm_client is not None and self.llm_client.is_configured()

    def generate_summary(
        self,
        transcript: str,
        template_name: str,
        template_sections: List[str],
        template_prompt: str,
        template_description: str = "",
        **kwargs
    ) -> ProviderResult:
        """
        使用 LLM 生成总结

        Args:
            transcript: 会议文字稿
            template_name: 模板名称
            template_sections: 模板章节
            template_prompt: 模板提示词
            template_description: 模板描述
            **kwargs: 额外参数

        Returns:
            ProviderResult with summary
        """
        start_time = time.time()
        start_datetime = datetime.now()

        # 验证 transcript 非空
        transcript = transcript.strip()
        if not transcript:
            return ProviderResult(
                success=False,
                data=None,
                provider=self.provider_type,
                is_fallback=False,
                error="当前会议暂无文字稿，无法生成总结",
                processing_time_ms=int((datetime.now() - start_datetime).total_seconds() * 1000)
            )

        if len(transcript) < 10:
            return ProviderResult(
                success=False,
                data=None,
                provider=self.provider_type,
                is_fallback=False,
                error="文字稿内容过少，无法生成有效的总结",
                processing_time_ms=int((datetime.now() - start_datetime).total_seconds() * 1000)
            )

        if not self.is_available():
            return ProviderResult(
                success=False,
                data=None,
                provider=self.provider_type,
                is_fallback=False,
                error="LLM service not configured",
                processing_time_ms=int((datetime.now() - start_datetime).total_seconds() * 1000)
            )

        try:
            print(f"[LLMSummaryProvider] Calling LLM API...")
            print(f"[LLMSummaryProvider] Provider: {self.llm_client.provider}")
            print(f"[LLMSummaryProvider] Transcript length: {len(transcript)}")

            summary = self.llm_client.generate_summary(
                transcript=transcript,
                template_name=template_name,
                template_description=template_description,
                template_sections=template_sections,
                template_prompt=template_prompt
            )

            processing_time = int((datetime.now() - start_datetime).total_seconds() * 1000)

            # 验证返回的总结不为空
            if not summary or not summary.strip():
                return ProviderResult(
                    success=False,
                    data=None,
                    provider=self.provider_type,
                    is_fallback=False,
                    error="LLM 返回空总结",
                    processing_time_ms=processing_time
                )

            # 提取模型信息
            model = "unknown"
            if self.llm_client.provider == "deepseek":
                model = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

            return ProviderResult(
                success=True,
                data={
                    "summary": summary,
                    "model": model
                },
                provider=self.provider_type,
                is_fallback=False,
                processing_time_ms=processing_time
            )

        except Exception as e:
            error_msg = str(e)
            print(f"[LLMSummaryProvider] ERROR: {error_msg}")
            return ProviderResult(
                success=False,
                data=None,
                provider=self.provider_type,
                is_fallback=False,
                error=error_msg,
                processing_time_ms=int((datetime.now() - start_datetime).total_seconds() * 1000)
            )
