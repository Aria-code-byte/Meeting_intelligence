"""
Summary Provider
================
会议总结服务提供商适配器

支持：
- FallbackSummaryProvider: 基于模板的简单总结
- LLMSummaryProvider: 真实 LLM 总结（OpenAI/Anthropic/Ollama/DeepSeek等）
"""
import os
import time
from typing import Optional, Dict, Any, List
from datetime import datetime
from .base import BaseProvider, ProviderResult, ProviderType


class FallbackSummaryProvider(BaseProvider):
    """回退总结提供商（基于模板的简单总结）"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.provider_type = ProviderType.FALLBACK

    def generate_summary(
        self,
        transcript: str,
        template_name: str,
        template_sections: List[str],
        template_prompt: str,
        **kwargs
    ) -> ProviderResult:
        """
        生成回退总结（基于模板的简单格式化）

        Args:
            transcript: 会议文字稿
            template_name: 模板名称
            template_sections: 模板章节
            template_prompt: 模板提示词
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
                is_fallback=True,
                error="当前会议暂无文字稿，无法生成总结。请先上传音频进行转录或手动输入文字稿。",
                processing_time_ms=int((datetime.now() - start_datetime).total_seconds() * 1000)
            )

        if len(transcript) < 10:
            return ProviderResult(
                success=False,
                data=None,
                provider=self.provider_type,
                is_fallback=True,
                error="文字稿内容过少，无法生成有效的总结。请补充更多内容。",
                processing_time_ms=int((datetime.now() - start_datetime).total_seconds() * 1000)
            )

        # 按段落处理文字稿
        transcript_paragraphs = transcript.split('\n')[:5]

        # 构建总结
        summary_parts = [
            f"# 会议总结",
            "",
            f"> 本总结基于「{template_name}」模板生成。",
            "",
            "## 基本信息",
            f"- **模板**: {template_name}",
            f"- **生成方式**: 本地回退模式（未配置真实AI总结服务）",
            f"- **生成时间**: {start_datetime.strftime('%Y-%m-%d %H:%M:%S')}",
            "",
        ]

        # 添加模板章节
        for section in template_sections:
            summary_parts.extend([
                f"## {section}",
                "",
                *transcript_paragraphs,
                "",
                "*请基于以上文字稿进一步整理此章节内容。*",
                "",
            ])

        summary = "\n".join(summary_parts)
        processing_time = int((datetime.now() - start_datetime).total_seconds() * 1000)

        return ProviderResult(
            success=True,
            data={
                "summary": summary,
                "model": "fallback"
            },
            provider=self.provider_type,
            is_fallback=True,
            processing_time_ms=processing_time
        )


class LLMSummaryProvider(BaseProvider):
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


class SummaryProvider:
    """总结提供商工厂（唯一版本）"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._init_provider()

    def _init_provider(self):
        """初始化提供商（基于环境变量）"""
        # 从环境变量读取 provider 类型
        provider_type = os.getenv("AI_SUMMARY_PROVIDER", "fallback").lower()

        print(f"[SummaryProvider] Initializing with provider: {provider_type}")

        if provider_type == "fallback":
            # 强制使用 fallback
            print(f"[SummaryProvider] Using fallback (forced)")
            self.provider = FallbackSummaryProvider(self.config)
        elif provider_type in ["deepseek", "backend"]:
            # 尝试使用 LLM
            llm_provider = LLMSummaryProvider(self.config)

            if llm_provider.is_available():
                self.provider = llm_provider
                print(f"[SummaryProvider] Using LLM provider: {provider_type}")
            else:
                print(f"[SummaryProvider] LLM unavailable, falling back")
                self.provider = FallbackSummaryProvider(self.config)
        else:
            print(f"[SummaryProvider] Unknown provider: {provider_type}, falling back")
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
