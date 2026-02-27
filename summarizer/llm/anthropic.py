"""
Anthropic LLM provider.

支持 Claude 3 Opus、Sonnet、Haiku 等模型。
使用官方 Anthropic SDK 实现。
"""

import os
from typing import List

from summarizer.llm.base import BaseLLMProvider, LLMMessage, LLMResponse


class AnthropicProvider(BaseLLMProvider):
    """
    Anthropic LLM 提供商

    支持 Claude 3 Opus、Sonnet、Haiku 等模型。
    使用官方 Anthropic SDK。
    """

    DEFAULT_MODEL = "claude-3-haiku-20240307"
    AVAILABLE_MODELS = [
        "claude-3-opus-20240229",
        "claude-3-sonnet-20240229",
        "claude-3-haiku-20240307",
        "claude-3-5-sonnet-20241022"
    ]

    def __init__(
        self,
        api_key: str = None,
        model: str = DEFAULT_MODEL,
        timeout: int = 120,
        max_retries: int = 3
    ):
        """
        初始化 Anthropic 提供商

        Args:
            api_key: Anthropic API 密钥（默认从环境变量读取）
            model: 模型名称
            timeout: 请求超时时间
            max_retries: 最大重试次数
        """
        super().__init__(api_key, model, timeout, max_retries)

        # 从环境变量读取 API 密钥
        if self.api_key is None:
            self.api_key = os.environ.get("ANTHROPIC_API_KEY")

        if self.model == "default":
            self.model = self.DEFAULT_MODEL

        # 初始化 Anthropic 客户端（延迟导入）
        try:
            from anthropic import Anthropic
            self._client = Anthropic(
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
        return f"anthropic-{self.model}"

    def _check_availability(self) -> bool:
        """
        检查 Anthropic 是否可用

        Returns:
            True 如果可用
        """
        if not self._available:
            return False

        if not self.api_key:
            return False

        try:
            # Anthropic 没有简单的可用性检查端点
            # 我们假设客户端初始化成功即表示可用
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
        使用 Anthropic API 生成文本

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
                "Anthropic SDK 未安装。请运行: pip install anthropic"
            )

        if not self.api_key:
            raise RuntimeError(
                "Anthropic API 密钥未设置。请设置 ANTHROPIC_API_KEY 环境变量。"
            )

        # 分离系统消息和用户消息
        # Anthropic API 将系统消息作为单独参数
        system_message = ""
        user_messages = []

        for msg in messages:
            if msg.role == "system":
                system_message = msg.content
            elif msg.role in ("user", "assistant"):
                user_messages.append({
                    "role": msg.role,
                    "content": msg.content
                })

        try:
            # Claude API 调用
            response = self._client.messages.create(
                model=self.model,
                system=system_message if system_message else None,
                messages=user_messages,
                max_tokens=max_tokens,
                temperature=temperature
            )

            # 提取文本内容
            content = ""
            for block in response.content:
                if block.type == "text":
                    content += block.text

            return LLMResponse(
                content=content,
                model=self.model,
                provider="anthropic",
                tokens_used=response.usage.input_tokens + response.usage.output_tokens,
                finish_reason=response.stop_reason
            )

        except Exception as e:
            # 分类错误类型
            error_msg = str(e)
            if "api_key" in error_msg.lower() or "authentication" in error_msg.lower():
                raise RuntimeError(
                    f"Anthropic API 认证失败。请检查 API Key: {e}"
                )
            elif "rate" in error_msg.lower() or "limit" in error_msg.lower():
                raise RuntimeError(
                    f"Anthropic API 速率限制。请稍后重试: {e}"
                )
            elif "timeout" in error_msg.lower():
                raise RuntimeError(
                    f"Anthropic API 请求超时（超过 {self.timeout} 秒）"
                )
            else:
                raise RuntimeError(f"Anthropic API 调用失败: {e}")
