"""
DeepSeek LLM provider.

支持 DeepSeek-V3、DeepSeek-Chat 等模型。
使用 DeepSeek API（与 OpenAI SDK 兼容）。
"""

import os
from typing import List

from summarizer.llm.base import BaseLLMProvider, LLMMessage, LLMResponse


class DeepSeekProvider(BaseLLMProvider):
    """
    DeepSeek LLM 提供商

    支持 DeepSeek-V3、DeepSeek-Chat 等模型。
    使用 OpenAI SDK，只需修改 base_url。
    """

    DEFAULT_MODEL = "deepseek-chat"
    AVAILABLE_MODELS = [
        "deepseek-chat",      # 对话模型
        "deepseek-reasoner",  # 推理模型
        "deepseek-coder",     # 代码模型
    ]

    # DeepSeek API 基础 URL
    BASE_URL = "https://api.deepseek.com"

    def __init__(
        self,
        api_key: str = None,
        model: str = DEFAULT_MODEL,
        timeout: int = 120,
        max_retries: int = 3
    ):
        """
        初始化 DeepSeek 提供商

        Args:
            api_key: DeepSeek API 密钥（默认从环境变量读取）
            model: 模型名称
            timeout: 请求超时时间
            max_retries: 最大重试次数
        """
        super().__init__(api_key, model, timeout, max_retries)

        # 从环境变量读取 API 密钥
        if self.api_key is None:
            self.api_key = os.environ.get("DEEPSEEK_API_KEY")

        if self.model == "default":
            self.model = self.DEFAULT_MODEL

        # 初始化 DeepSeek 客户端（使用 OpenAI SDK）
        try:
            from openai import OpenAI
            self._client = OpenAI(
                api_key=self.api_key,
                base_url=self.BASE_URL,
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
        return f"deepseek-{self.model}"

    def _check_availability(self) -> bool:
        """
        检查 DeepSeek API 是否可用

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
        使用 DeepSeek API 生成文本

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
                "DeepSeek API 密钥未设置。请设置 DEEPSEEK_API_KEY 环境变量。"
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
                raise RuntimeError("DeepSeek API 返回空响应")

            choice = response.choices[0]
            content = choice.message.content or ""

            return LLMResponse(
                content=content,
                model=self.model,
                provider="deepseek",
                tokens_used=response.usage.total_tokens if response.usage else None,
                finish_reason=choice.finish_reason
            )

        except Exception as e:
            # 分类错误类型
            error_msg = str(e)
            if "api_key" in error_msg.lower() or "authentication" in error_msg.lower() or "401" in error_msg:
                raise RuntimeError(
                    f"DeepSeek API 认证失败。请检查 API Key: {e}"
                )
            elif "rate" in error_msg.lower() or "limit" in error_msg.lower() or "429" in error_msg:
                raise RuntimeError(
                    f"DeepSeek API 速率限制。请稍后重试: {e}"
                )
            elif "timeout" in error_msg.lower():
                raise RuntimeError(
                    f"DeepSeek API 请求超时（超过 {self.timeout} 秒）"
                )
            else:
                raise RuntimeError(f"DeepSeek API 调用失败: {e}")
