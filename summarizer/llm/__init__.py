"""
LLM provider module.

定义 LLM 提供商的抽象接口和具体实现。
"""

from summarizer.llm.base import BaseLLMProvider, LLMMessage, LLMResponse
from summarizer.llm.deepseek import DeepSeekProvider

__all__ = [
    "BaseLLMProvider",
    "LLMMessage",
    "LLMResponse",
    "DeepSeekProvider",
]
