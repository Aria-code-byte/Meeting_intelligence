"""
LLM Transcript Enhancer - LLM 转录文本增强器

PR3 轻量版：
- 直接 LLM 调用，整块处理
- 简单错误处理，整块回退
- 支持自定义提示词模板
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Callable
from enum import Enum
import re


class EnhancementError(Exception):
    """增强处理错误基类"""
    pass


class LLMProviderError(EnhancementError):
    """LLM 提供商错误"""
    pass


class ParseError(EnhancementError):
    """解析错误"""
    pass


# ============================================================
# 提示词模板
# ============================================================

DEFAULT_SYSTEM_PROMPT = """你是一个专业的会议文稿编辑助手。

你的任务是：
1. 修正转录文本中的语法错误
2. 添加适当的标点符号
3. 保持说话人的原意不变
4. 保持口语化风格，不过度书面化

请直接输出修正后的文本，不要添加任何解释或格式标记。"""

DEFAULT_USER_PROMPT_TEMPLATE = """请优化以下会议转录文本：

{transcript_text}

要求：
- 保持原意
- 添加标点
- 修正语法
- 输出完整文本"""


@dataclass
class PromptTemplate:
    """提示词模板"""
    name: str
    system_prompt: str
    user_prompt_template: str
    description: str = ""

    def format_user_prompt(self, transcript_text: str) -> str:
        """格式化用户提示词"""
        return self.user_prompt_template.format(transcript_text=transcript_text)


# 预定义模板库
PREDEFINED_TEMPLATES = {
    "general": PromptTemplate(
        name="通用优化",
        system_prompt=DEFAULT_SYSTEM_PROMPT,
        user_prompt_template=DEFAULT_USER_PROMPT_TEMPLATE,
        description="适合大多数场景的通用优化"
    ),
    "technical": PromptTemplate(
        name="技术会议",
        system_prompt="""你是技术会议记录专家。
重点关注技术术语、代码片段、技术决策的准确性。
保持技术准确性，添加适当标点。""",
        user_prompt_template="请优化以下技术会议转录：\n{transcript_text}",
        description="适合技术会议场景"
    ),
    "executive": PromptTemplate(
        name="高管汇报",
        system_prompt="""你是高管汇报材料编辑。
简洁、重点突出、结论导向。
使用商务语言风格。""",
        user_prompt_template="请优化以下会议记录：\n{transcript_text}",
        description="适合高管汇报场景"
    ),
    "minimal": PromptTemplate(
        name="最小改动",
        system_prompt="""你是文稿校对员。
仅修正明显的错误，最小化改动。
只添加必要的标点符号。""",
        user_prompt_template="请校对以下文本：\n{transcript_text}",
        description="仅做最小必要修正"
    ),
}


# ============================================================
# 配置类
# ============================================================

@dataclass
class LLMEnhancerConfig:
    """LLM 增强器配置（轻量版）"""
    enabled: bool = False
    provider: str = "openai"
    model: str = "gpt-4o-mini"
    max_tokens: int = 8000
    temperature: float = 0.3

    # 回退策略（简化版）
    fallback_on_error: bool = True

    # 提示词模板
    template_name: str = "general"
    system_prompt: Optional[str] = None
    user_prompt_template: Optional[str] = None

    def __post_init__(self):
        if self.model is None or not self.model:
            raise ValueError("model 不能为空")
        if self.max_tokens <= 0:
            raise ValueError("max_tokens 必须 > 0")
        if not 0.0 <= self.temperature <= 2.0:
            raise ValueError("temperature 必须在 [0, 2] 范围内")
        if self.template_name and self.template_name not in PREDEFINED_TEMPLATES:
            if not (self.system_prompt and self.user_prompt_template):
                raise ValueError(f"未知模板名称: {self.template_name}，必须提供自定义提示词")

    def get_template(self) -> PromptTemplate:
        """获取提示词模板"""
        # 自定义提示词优先
        if self.system_prompt and self.user_prompt_template:
            return PromptTemplate(
                name="custom",
                system_prompt=self.system_prompt,
                user_prompt_template=self.user_prompt_template,
                description="自定义模板"
            )

        # 使用预定义模板
        return PREDEFINED_TEMPLATES.get(
            self.template_name,
            PREDEFINED_TEMPLATES["general"]
        )


# ============================================================
# 结果类
# ============================================================

@dataclass
class EnhancedTranscriptResult:
    """增强版转录结果"""
    original_text: str
    enhanced_text: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    # 状态信息
    success: bool = True
    error_message: Optional[str] = None
    fallback_used: bool = False

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "original_text": self.original_text,
            "enhanced_text": self.enhanced_text,
            "success": self.success,
            "fallback_used": self.fallback_used,
        }
        if self.metadata:
            result["metadata"] = self.metadata
        if self.error_message:
            result["error_message"] = self.error_message
        return result


# ============================================================
# LLM 增强器
# ============================================================

class LLMTranscriptEnhancer:
    """LLM 转录文本增强器（轻量版）"""

    def __init__(self, config: LLMEnhancerConfig):
        """
        初始化增强器

        Args:
            config: 增强器配置
        """
        self.config = config
        self.provider = self._create_provider()
        self.template = config.get_template()

    def _create_provider(self):
        """创建 LLM Provider"""
        provider_name = self.config.provider.lower()

        if provider_name == "mock":
            from summarizer.llm.mock import MockLLMProvider
            return MockLLMProvider()
        elif provider_name == "openai":
            from summarizer.llm.openai import OpenAIProvider
            return OpenAIProvider(model=self.config.model)
        elif provider_name == "anthropic":
            from summarizer.llm.anthropic import AnthropicProvider
            return AnthropicProvider(model=self.config.model)
        elif provider_name == "glm":
            from summarizer.llm.glm import GLMProvider
            return GLMProvider(model=self.config.model)
        else:
            raise ValueError(f"不支持的 LLM 提供商: {self.config.provider}")

    def enhance(
        self,
        transcript_text: str,
        progress_callback: Optional[Callable] = None
    ) -> EnhancedTranscriptResult:
        """
        增强转录文本（整段处理，不分块）

        Args:
            transcript_text: 原始转录文本（完整文本）
            progress_callback: 进度回调 (stage, progress)

        Returns:
            EnhancedTranscriptResult 实例
        """
        if progress_callback:
            progress_callback("enhancement_start", 0)

        # 构建提示词
        from summarizer.llm.base import LLMMessage

        messages = [
            LLMMessage(role="system", content=self.template.system_prompt),
            LLMMessage(role="user", content=self.template.format_user_prompt(transcript_text))
        ]

        if progress_callback:
            progress_callback("calling_llm", 50)

        # 调用 LLM
        try:
            response = self.provider.generate(
                messages=messages,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature
            )

            # 提取响应内容
            enhanced_text = response.content if hasattr(response, 'content') else str(response)

            if progress_callback:
                progress_callback("enhancement_complete", 100)

            return EnhancedTranscriptResult(
                original_text=transcript_text,
                enhanced_text=enhanced_text.strip(),
                metadata={
                    "provider": self.config.provider,
                    "model": self.config.model,
                    "template": self.template.name,
                    "fallback_used": False
                },
                success=True,
                fallback_used=False
            )

        except Exception as e:
            if self.config.fallback_on_error:
                # 回退：使用原文
                return EnhancedTranscriptResult(
                    original_text=transcript_text,
                    enhanced_text=transcript_text,
                    metadata={
                        "provider": self.config.provider,
                        "model": self.config.model,
                        "template": self.template.name,
                        "fallback_used": True
                    },
                    success=True,
                    error_message=str(e),
                    fallback_used=True
                )
            else:
                raise LLMProviderError(f"LLM 调用失败: {e}") from e


# ============================================================
# 文本处理工具
# ============================================================

def map_enhanced_text_to_sentences(
    enhanced_text: str,
    original_sentences: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    将增强文本映射回原始 sentences

    PR3 轻量版策略：
    - 由于 LLM 返回的是整段文本
    - 需要将增强文本重新分割并映射到原始 sentences
    - 使用简单的按长度比例或标点分割

    Args:
        enhanced_text: LLM 返回的增强文本
        original_sentences: 原始 sentence 列表

    Returns:
        映射后的 sentence 列表
    """
    if not original_sentences:
        return []

    # 策略：按句子数量比例分割增强文本
    # 这是一个简化策略，PR5 可以改进

    # 首先按标点分割增强文本
    sentences_in_enhanced = _split_into_sentences(enhanced_text)

    # 如果分割出的句子数量与原始接近，直接映射
    if len(sentences_in_enhanced) == len(original_sentences):
        return [
            {
                **orig,
                "enhanced_text": sentences_in_enhanced[i]
            }
            for i, orig in enumerate(original_sentences)
        ]

    # 如果数量不一致，使用比例映射
    result = []
    enhanced_index = 0
    total_enhanced_len = sum(len(s) for s in sentences_in_enhanced)
    current_len = 0

    for orig in original_sentences:
        # 计算当前原始句子应该占用的增强文本长度
        orig_len = len(orig["text"])
        target_len = int(orig_len * total_enhanced_len / sum(len(s["text"]) for s in original_sentences))

        # 累积增强文本直到达到目标长度
        enhanced_parts = []
        while enhanced_index < len(sentences_in_enhanced) and current_len < target_len:
            enhanced_parts.append(sentences_in_enhanced[enhanced_index])
            current_len += len(sentences_in_enhanced[enhanced_index])
            enhanced_index += 1

        result.append({
            **orig,
            "enhanced_text": "".join(enhanced_parts)
        })
        current_len = 0

    # 处理剩余的增强文本（如果有）
    while enhanced_index < len(sentences_in_enhanced):
        if result:
            result[-1]["enhanced_text"] += " " + sentences_in_enhanced[enhanced_index]
        enhanced_index += 1

    return result


def _split_into_sentences(text: str) -> List[str]:
    """
    将文本分割成句子

    使用简单规则：按句号、问号、感叹号分割
    """
    # 替换中文标点为统一格式
    text = text.replace("！", "!").replace("？", "?").replace("。", ".")

    # 按标点分割
    parts = re.split(r'([.!?。！？])', text)

    sentences = []
    current = ""

    for i in range(0, len(parts), 2):
        if i < len(parts):
            current += parts[i]
            if i + 1 < len(parts):
                current += parts[i + 1]
                if current.strip():
                    sentences.append(current.strip())
                current = ""

    # 处理剩余部分
    if current.strip():
        sentences.append(current.strip())

    return sentences if sentences else [text]
