"""
GLM (Zhipu AI) LLM provider.

支持 GLM-4、GLM-3-Turbo 等模型。
使用智谱 AI 官方 SDK 实现。
"""

import os
from typing import List

from summarizer.llm.base import BaseLLMProvider, LLMMessage, LLMResponse


class GLMProvider(BaseLLMProvider):
    """
    智谱 AI LLM 提供商

    支持 GLM-4、GLM-3-Turbo 等模型。
    使用智谱 AI 官方 SDK。
    """

    DEFAULT_MODEL = "glm-4-flash"
    AVAILABLE_MODELS = [
        "glm-4-flash",      # 快速版，推荐
        "glm-4",            # 完整版
        "glm-4-air",        # 轻量版
        "glm-4-plus",       # 增强版
        "glm-3-turbo",      # 旧版 Turbo
    ]

    def __init__(
        self,
        api_key: str = None,
        model: str = DEFAULT_MODEL,
        timeout: int = 120,
        max_retries: int = 3
    ):
        """
        初始化智谱 AI 提供商

        Args:
            api_key: 智谱 API 密钥（默认从环境变量读取）
            model: 模型名称
            timeout: 请求超时时间
            max_retries: 最大重试次数
        """
        super().__init__(api_key, model, timeout, max_retries)

        # 从环境变量读取 API 密钥
        if self.api_key is None:
            self.api_key = os.environ.get("ZHIPU_API_KEY")

        if self.model == "default":
            self.model = self.DEFAULT_MODEL

        # 初始化智谱客户端（延迟导入）
        try:
            from zhipuai import ZhipuAI
            self._client = ZhipuAI(
                api_key=self.api_key,
                timeout=timeout
            )
            self._available = True
        except ImportError:
            self._client = None
            self._available = False

    @property
    def name(self) -> str:
        """提供商名称"""
        return f"glm-{self.model}"

    def _check_availability(self) -> bool:
        """
        检查智谱 API 是否可用

        Returns:
            True 如果可用
        """
        if not self._available:
            return False

        if not self.api_key:
            return False

        # 智谱没有简单的可用性检查端点
        return True

    def generate(
        self,
        messages: List[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> LLMResponse:
        """
        使用智谱 API 生成文本

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
                "智谱 SDK 未安装。请运行: pip install zhipuai"
            )

        if not self.api_key:
            raise RuntimeError(
                "智谱 API 密钥未设置。请设置 ZHIPU_API_KEY 环境变量。"
            )

        # 构建消息列表（智谱格式）
        api_messages = []

        for msg in messages:
            api_messages.append({
                "role": msg.role,
                "content": msg.content
            })

        try:
            # 调用智谱 API（system 消息已在 messages 数组中）
            response = self._client.chat.completions.create(
                model=self.model,
                messages=api_messages,
                temperature=temperature,
                max_tokens=max_tokens
            )

            if not response.choices:
                raise RuntimeError("智谱 API 返回空响应")

            choice = response.choices[0]
            content = choice.message.content or ""

            return LLMResponse(
                content=content,
                model=self.model,
                provider="glm",
                tokens_used=response.usage.total_tokens if response.usage else None,
                finish_reason=choice.finish_reason
            )

        except Exception as e:
            # 分类错误类型
            error_msg = str(e)
            if "api_key" in error_msg.lower() or "authentication" in error_msg.lower() or "401" in error_msg:
                raise RuntimeError(
                    f"智谱 API 认证失败。请检查 API Key: {e}"
                )
            elif "rate" in error_msg.lower() or "limit" in error_msg.lower() or "429" in error_msg:
                raise RuntimeError(
                    f"智谱 API 速率限制。请稍后重试: {e}"
                )
            elif "timeout" in error_msg.lower():
                raise RuntimeError(
                    f"智谱 API 请求超时（超过 {self.timeout} 秒）"
                )
            else:
                raise RuntimeError(f"智谱 API 调用失败: {e}")
