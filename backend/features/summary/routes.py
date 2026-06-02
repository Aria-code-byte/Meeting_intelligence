"""
总结功能 API 路由
"""

from fastapi import APIRouter
from typing import List, Dict, Any
from datetime import datetime

from .models import SummarizeRequest, SummarizeResponse
from .service import SummaryService


router = APIRouter(prefix="/api/v1", tags=["summary"])

# 创建服务实例
summary_service = SummaryService()


@router.post("/summarize", response_model=SummarizeResponse)
async def summarize(request: SummarizeRequest) -> SummarizeResponse:
    """
    生成会议总结

    使用 LLM 或回退模式生成会议总结
    """
    start_time = datetime.now()

    try:
        # 调用服务生成总结
        result = summary_service.generate_summary(
            transcript=request.transcript,
            template_name=request.template_name,
            template_sections=request.template_sections,
            template_prompt=request.template_prompt,
            template_description=request.template_description
        )

        processing_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)

        if result.success:
            return SummarizeResponse(
                success=True,
                summary=result.data.get("summary"),
                provider=str(result.provider),
                isFallback=result.is_fallback,
                templateName=request.template_name,
                processingTimeMs=processing_time_ms,
                metadata={
                    "processedAt": start_time.isoformat(),
                    "model": result.data.get("model", "unknown")
                }
            )
        else:
            return SummarizeResponse(
                success=False,
                provider=str(result.provider),
                isFallback=result.is_fallback,
                error=result.error,
                processingTimeMs=processing_time_ms,
                metadata={"processedAt": start_time.isoformat()}
            )

    except Exception as e:
        processing_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
        return SummarizeResponse(
            success=False,
            provider="error",
            isFallback=True,
            error=f"总结生成异常: {str(e)}",
            processingTimeMs=processing_time_ms,
            metadata={"processedAt": start_time.isoformat()}
        )


@router.get("/provider-info")
async def get_provider_info() -> Dict[str, Any]:
    """获取总结提供商信息"""
    return summary_service.get_provider_info()
