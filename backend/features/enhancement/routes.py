"""
LLM 增强功能 API 路由
"""

from fastapi import APIRouter
from typing import List
from datetime import datetime

from .models import (
    TranscriptTurn,
    EnhancementRequest,
    EnhancementResponse,
    EnhancedTranscriptTurn
)
from .service import EnhancementService


router = APIRouter(prefix="/api/v1/enhancement", tags=["enhancement"])

# 创建服务实例
enhancement_service = EnhancementService()


@router.post("/enhance", response_model=EnhancementResponse)
async def enhance_transcript(request: EnhancementRequest) -> EnhancementResponse:
    """
    LLM 文字稿优化接口

    使用 DeepSeek 等大语言模型优化会议转录文本
    """
    start_time = datetime.now()

    try:
        # 转换数据格式
        transcript_turns = [
            TranscriptTurn(
                speaker=turn.speaker,
                start=turn.start,
                end=turn.end,
                text=turn.text
            )
            for turn in request.transcriptTurns
        ]

        # 添加调试日志
        print(f"[Enhancement] 收到增强请求: {len(transcript_turns)} 个 turns")
        for i, turn in enumerate(transcript_turns[:3]):  # 只打印前 3 个
            print(f"[Enhancement]   原始 turn {i}: [{turn.speaker}] {turn.text[:50]}...")

        # 调用 DeepSeek 优化
        enhanced_turns = await enhancement_service.enhance_transcript(transcript_turns)

        # 添加调试日志
        print(f"[Enhancement] 增强完成: {len(enhanced_turns)} 个 turns")
        for i, turn in enumerate(enhanced_turns[:3]):  # 只打印前 3 个
            print(f"[Enhancement]   增强 turn {i}: [{turn.speaker}] {turn.text[:50]}...")

        processing_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)

        return EnhancementResponse(
            success=True,
            enhancedTranscriptTurns=[
                EnhancedTranscriptTurn(
                    speaker=turn.speaker,
                    start=turn.start,
                    end=turn.end,
                    text=turn.text
                )
                for turn in enhanced_turns
            ],
            provider=request.provider,
            model=request.model,
            processingTimeMs=processing_time_ms,
            metadata={
                "processedAt": start_time.isoformat(),
                "turnCount": len(enhanced_turns)
            }
        )

    except Exception as e:
        processing_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
        error_detail = getattr(e, 'detail', str(e)) if hasattr(e, 'detail') else str(e)
        return EnhancementResponse(
            success=False,
            provider=request.provider,
            model=request.model,
            error=error_detail,
            processingTimeMs=processing_time_ms,
            metadata={"processedAt": start_time.isoformat()}
        )


@router.get("/providers")
async def get_providers():
    """获取可用的优化提供商"""
    return {
        "providers": [
            {"id": "deepseek", "name": "DeepSeek", "models": ["deepseek-chat"]},
            {"id": "openai", "name": "OpenAI", "models": ["gpt-4o-mini", "gpt-4"]},
            {"id": "anthropic", "name": "Anthropic", "models": ["claude-3-5-sonnet"]},
            {"id": "glm", "name": "智谱 GLM", "models": ["glm-4-flash"]}
        ],
        "default": "deepseek"
    }
