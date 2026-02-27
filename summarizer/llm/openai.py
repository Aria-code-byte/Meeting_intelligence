"""
OpenAI LLM provider.

支持 GPT-4、GPT-3.5-turbo 等模型。
使用官方 OpenAI SDK 实现。
"""

import os
from typing import List

from summarizer.llm.base import BaseLLMProvider, LLMMessage, LLMResponse


class OpenAIProvider(BaseLLMProvider):
    """
    OpenAI LLM 提供商

    支持 GPT-4、GPT-3.5-turbo 等模型。
    使用官方 OpenAI SDK。
    """

    DEFAULT_MODEL = "gpt-3.5-turbo"
    AVAILABLE_MODELS = [
        "gpt-4",
        "gpt-4-turbo",
        "gpt-4-turbo-preview",
        "gpt-3.5-turbo",
        "gpt-3.5-turbo-16k"
    ]

    def __init__(
        self,
        api_key: str = None,
        model: str = DEFAULT_MODEL,
        timeout: int = 120,
        max_retries: int = 3
    ):
        """
        初始化 OpenAI 提供商

        Args:
            api_key: OpenAI API 密钥（默认从环境变量读取）
            model: 模型名称
            timeout: 请求超时时间
            max_retries: 最大重试次数
        """
        super().__init__(api_key, model, timeout, max_retries)

        # 从环境变量读取 API 密钥
        if self.api_key is None:
            self.api_key = os.environ.get("OPENAI_API_KEY")

        if self.model == "default":
            self.model = self.DEFAULT_MODEL

        # 初始化 OpenAI 客户端（延迟导入，允许在未安装时运行其他功能）
        try:
            from openai import OpenAI
            self._client = OpenAI(
                api_key=self.api_key,
                timeout=timeout,
                max_retries=max_retries
            )
            self._available = True
        except ImportError:
            self._client = None
            self._available = False

    @property
    def name(self) -> str:
        """提供商名称"""
        return f"openai-{self.model}"

    def _check_availability(self) -> bool:
        """
        检查 OpenAI 是否可用

        Returns:
            True 如果可用
        """
        if not self._available:
            return False

        if not self.api_key:
            return False

        try:
            # 尝试列出模型作为可用性检查
            self._client.models.list()
            return True
        except Exception:
            return False

    def generate(
        self,
        messages: List[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> LLMResponse:
        """
        使用 OpenAI API 生成文本

        Args:
            messages: 消息列表
            temperature: 温度参数
            max_tokens: 最大 token 数

        Returns:
            LLM 响应

        Raises:
            RuntimeError: 如果 API 调用失败
        """
        if not self._available:
            raise RuntimeError(
                "OpenAI SDK 未安装。请运行: pip install openai"
            )

        if not self.api_key:
            raise RuntimeError(
                "OpenAI API 密钥未设置。请设置 OPENAI_API_KEY 环境变量。"
            )

        # 构建消息列表
        api_messages = [
            {"role": m.role, "content": m.content}
            for m in messages
        ]

        try:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=api_messages,
                temperature=temperature,
                max_tokens=max_tokens
            )

            if not response.choices:
                raise RuntimeError("OpenAI API 返回空响应")

            choice = response.choices[0]
            content = choice.message.content or ""

            return LLMResponse(
                content=content,
                model=self.model,
                provider="openai",
                tokens_used=response.usage.total_tokens if response.usage else None,
                finish_reason=choice.finish_reason
            )

        except Exception as e:
            # 分类错误类型
            error_msg = str(e)
            if "api_key" in error_msg.lower() or "authentication" in error_msg.lower():
                raise RuntimeError(
                    f"OpenAI API 认证失败。请检查 API Key: {e}"
                )
            elif "rate" in error_msg.lower() or "limit" in error_msg.lower():
                raise RuntimeError(
                    f"OpenAI API 速率限制。请稍后重试: {e}"
                )
            elif "timeout" in error_msg.lower():
                raise RuntimeError(
                    f"OpenAI API 请求超时（超过 {self.timeout} 秒）"
                )
            else:
                raise RuntimeError(f"OpenAI API 调用失败: {e}")
