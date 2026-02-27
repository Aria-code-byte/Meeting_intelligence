"""
Base LLM provider.

定义 LLM 提供商的抽象接口。
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class LLMMessage:
    """LLM 消息"""
    role: str  # "system", "user", "assistant"
    content: str


@dataclass
class LLMResponse:
    """LLM 响应"""
    content: str
    model: str
    provider: str
    tokens_used: Optional[int] = None
    finish_reason: Optional[str] = None


class BaseLLMProvider(ABC):
    """
    LLM 提供商基类

    所有 LLM 提供商必须实现此接口。
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "default",
        timeout: int = 120,
        max_retries: int = 3
    ):
        """
        初始化 LLM 提供商

        Args:
            api_key: API 密钥（可选，可从环境变量读取）
            model: 模型名称
            timeout: 请求超时时间（秒）
            max_retries: 最大重试次数
        """
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.max_retries = max_retries

    @property
    def name(self) -> str:
        """提供商名称"""
        raise NotImplementedError

    @abstractmethod
    def _check_availability(self) -> bool:
        """
        检查提供商是否可用

        Returns:
            True 如果可用
        """
        raise NotImplementedError

    @abstractmethod
    def generate(
        self,
        messages: List[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> LLMResponse:
        """
        生成文本

        Args:
            messages: 消息列表
            temperature: 温度参数 (0-1)
            max_tokens: 最大 token 数

        Returns:
            LLM 响应

        Raises:
            RuntimeError: 如果生成失败
        """
        raise NotImplementedError

    def generate_with_retry(
        self,
        messages: List[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> LLMResponse:
        """
        带重试的生成

        Args:
            messages: 消息列表
            temperature: 温度参数
            max_tokens: 最大 token 数

        Returns:
            LLM 响应

        Raises:
            RuntimeError: 如果所有重试都失败
        """
        import time

        last_error = None

        for attempt in range(self.max_retries):
            try:
                return self.generate(messages, temperature, max_tokens)
            except Exception as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    error_msg = str(e)
                    # 检查是否是速率限制错误
                    is_rate_limit = (
                        "429" in error_msg or
                        "rate" in error_msg.lower() or
                        "limit" in error_msg.lower() or
                        "1302" in error_msg  # 智谱错误码
                    )

                    if is_rate_limit:
                        # 速率限制：等待更长时间
                        wait_time = 5 + (attempt * 5)  # 5, 10, 15 秒
                    else:
                        # 其他错误：指数退避
                        wait_time = 2 ** attempt

                    time.sleep(wait_time)
                else:
                    break

        raise RuntimeError(f"LLM 生成失败（重试 {self.max_retries} 次后）: {last_error}")

    def chat(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> LLMResponse:
        """
        简化的对话接口

        Args:
            system_prompt: 系统提示词
            user_prompt: 用户提示词
            temperature: 温度参数
            max_tokens: 最大 token 数

        Returns:
            LLM 响应
        """
        messages = [
            LLMMessage(role="system", content=system_prompt),
            LLMMessage(role="user", content=user_prompt)
        ]

        return self.generate_with_retry(messages, temperature, max_tokens)
