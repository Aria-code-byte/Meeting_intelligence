"""
总结功能数据模型
"""

from pydantic import BaseModel
from typing import List, Dict, Any, Optional


class SummarizeRequest(BaseModel):
    """总结请求"""
    transcript: str
    template_name: str
    template_description: Optional[str] = ""
    template_sections: List[str]
    template_prompt: str


class SummarizeResponse(BaseModel):
    """总结响应"""
    success: bool
    summary: Optional[str] = None
    provider: str
    isFallback: bool
    templateId: Optional[str] = None
    templateName: Optional[str] = None
    error: Optional[str] = None
    processingTimeMs: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None
