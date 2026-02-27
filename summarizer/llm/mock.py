"""
Mock LLM provider for testing.

模拟 LLM 提供商，用于测试和开发。
"""

from typing import List

from summarizer.llm.base import BaseLLMProvider, LLMMessage, LLMResponse


class MockLLMProvider(BaseLLMProvider):
    """
    Mock LLM 提供商

    用于测试和开发，返回预设的响应。
    """

    DEFAULT_RESPONSE = """
这是一个模拟的总结响应。

## 会议总结
本次会议讨论了项目进展和下一步计划。

## 关键要点
- 项目按计划进行
- 需要协调资源
- 下周进行代码审查

## 行动项
- 完成单元测试
- 更新文档
- 安排团队会议
"""

    def __init__(
        self,
        api_key: str = "mock-key",
        model: str = "mock-model",
        timeout: int = 10,
        max_retries: int = 1,
        mock_response: str = None
    ):
        """
        初始化 Mock 提供商

        Args:
            api_key: API 密钥（忽略）
            model: 模型名称（忽略）
            timeout: 超时时间（忽略）
            max_retries: 重试次数（忽略）
            mock_response: 模拟响应内容
        """
        super().__init__(api_key, model, timeout, max_retries)
        self.mock_response = mock_response or self.DEFAULT_RESPONSE

    @property
    def name(self) -> str:
        """提供商名称"""
        return "mock-provider"

    def _check_availability(self) -> bool:
        """Mock 提供商始终可用"""
        return True

    def generate(
        self,
        messages: List[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> LLMResponse:
        """
        返回模拟响应

        Args:
            messages: 消息列表（忽略）
            temperature: 温度参数（忽略）
            max_tokens: 最大 token 数（忽略）

        Returns:
            模拟的 LLM 响应
        """
        return LLMResponse(
            content=self.mock_response,
            model=self.model,
            provider="mock",
            tokens_used=100,
            finish_reason="stop"
        )

    def set_response(self, response: str) -> None:
        """
        设置模拟响应内容

        Args:
            response: 响应内容
        """
        self.mock_response = response
