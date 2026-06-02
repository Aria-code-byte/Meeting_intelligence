"""
LLM 增强功能数据模型
"""

from pydantic import BaseModel
from typing import List, Dict, Any, Optional


class TranscriptTurn(BaseModel):
    """说话人轮次"""
    speaker: str
    start: Optional[float] = None
    end: Optional[float] = None
    text: str


class EnhancementRequest(BaseModel):
    """优化请求"""
    transcriptTurns: List[TranscriptTurn]
    provider: str = "deepseek"
    model: str = "deepseek-chat"


class EnhancedTranscriptTurn(BaseModel):
    """优化后的说话人轮次"""
    speaker: str
    start: Optional[float] = None
    end: Optional[float] = None
    text: str


class EnhancementResponse(BaseModel):
    """优化响应"""
    success: bool
    enhancedTranscriptTurns: Optional[List[EnhancedTranscriptTurn]] = None
    provider: str
    model: str
    error: Optional[str] = None
    processingTimeMs: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None
