"""
回退总结提供商（基于模板的简单总结）
"""

import time
from typing import Optional, Dict, Any, List
from datetime import datetime

from .base import BaseSummaryProvider, ProviderResult, ProviderType


class FallbackSummaryProvider(BaseSummaryProvider):
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
