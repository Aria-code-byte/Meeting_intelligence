"""
LLM Transcript Enhancer - LLM 转录文本增强器（深度重构版）

核心改进：
- 语义块合并（Context Windowing）：将破碎的 ASR 句子合并为具备上下文的文本块
- 强化 Prompt 设计：Few-shot 示例 + 负面约束
- 调试日志：支持 --debug 开关
- 改进 Fallback 机制
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Callable
from enum import Enum
import re
import logging

# 配置日志
logger = logging.getLogger(__name__)


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
# 强化版提示词模板（基于真实测试优化）
# ============================================================

REFINER_SYSTEM_PROMPT = """你是一位专业的会议纪要整理专家。你的任务是修正 ASR 转录中的错误。

### 负面约束（必须遵守）：
- **不要**添加原句中没有的内容
- **不要**改变说话人的原意和语气
- **不要**过度书面化，保持口语风格
- **不要**添加任何解释、前缀或后缀

### 修正准则：
1. 修正同音错别字：严格对照下表修正
2. 删除语气词：剔除"就是"、"那个"、"然后"、"呃"、"是吧"等冗余词
3. 补全标点：在合适的位置添加逗号、句号和问号
4. 保持第一人称叙述：保留"我"的主语位置

### 同音错别字对照表（必须修正）：
| 错误 | 正确 | 语境 |
|------|------|------|
| 蓝哥舞 | 蓝哥我 | 主语 |
| 18线骗案 | 18线偏远 | 地点 |
| 偏案/偏偏 | 偏远 | 地点 |
| 带/代/待 | 贷 | 贷款相关 |
| 车带 | 车贷 | 汽车贷款 |
| 房带 | 房贷 | 住房贷款 |
| 消费带 | 消费贷 | 消费贷款 |
| 唱吃 | 偿债 | 债务 |
| 平穷/频钦 | 贫穷 | 经济状况 |
| 花杯/花费 | 花呗 | 支付产品 |
| 签 | 向 | 方向/对象 |
| 是吧（句末） | （删除） | 冗余词 |"""


REFINER_FEW_SHOT_EXAMPLES = """### Few-shot 示例：

**示例 1**
输入：起这么夸张的标题的但听完今天的课程之后你就会发现其实蓝哥今天给这些课程起的名字一点点也不夸张
输出：起这么夸张的标题，但听完今天的课程之后，你就会发现其实蓝哥给这些课程起的名字，一点也不夸张。

**示例 2**
输入：蓝哥舞从一个东北的18线骗案的小镇来自这个平穷的是吧下岗职工在家庭的孩子
输出：蓝哥我从一个东北的18线偏远小镇，一个贫穷的下岗职工家庭的孩子。

**示例 3**
输入：因为我家里边穷了然后我当时在带款买车卖房我当时买完车就都是贷款的
输出：因为家里穷了，所以我当时在贷款买车卖房，买完后都是贷款的。

**示例 4**
输入：然后当时车带然后签我的亲戚朋友包括建设银行当时有一个消费带我也带了15万多
输出：当时车贷，然后向亲戚朋友借款，包括建设银行有一个消费贷，我也贷了15万多。

**示例 5**
输入：我欠了41.4万然后呢每个月车带房带京东信用卡花杯
输出：我欠了**41.4万**，每个月车贷、房贷、京东信用卡花呗。"""


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
        system_prompt=REFINER_SYSTEM_PROMPT,
        user_prompt_template=f"""{REFINER_FEW_SHOT_EXAMPLES}

### 待处理文本：
{{transcript_text}}

### 输出要求：
直接输出修正后的文本，不要添加任何解释。""",
        description="适合大多数场景的通用优化（带 Few-shot 示例）"
    ),
    "technical": PromptTemplate(
        name="技术会议",
        system_prompt=REFINER_SYSTEM_PROMPT + "\n\n### 技术会议特殊要求：\n- 保留技术术语准确性\n- 保留代码片段和命令",
        user_prompt_template=f"""{REFINER_FEW_SHOT_EXAMPLES}

### 待处理文本：
{{transcript_text}}

### 输出要求：
直接输出修正后的文本，不要添加任何解释。""",
        description="适合技术会议场景"
    ),
    "executive": PromptTemplate(
        name="高管汇报",
        system_prompt=REFINER_SYSTEM_PROMPT + "\n\n### 高管汇报特殊要求：\n- 使用商务语言风格\n- 简洁、重点突出、结论导向",
        user_prompt_template=f"""{REFINER_FEW_SHOT_EXAMPLES}

### 待处理文本：
{{transcript_text}}

### 输出要求：
直接输出修正后的文本，不要添加任何解释。""",
        description="适合高管汇报场景"
    ),
    "minimal": PromptTemplate(
        name="最小改动",
        system_prompt=REFINER_SYSTEM_PROMPT + "\n\n### 最小改动要求：\n- 仅修正明显的错误\n- 只添加必要的标点符号\n- 最大化保留原文",
        user_prompt_template=f"""{REFINER_FEW_SHOT_EXAMPLES}

### 待处理文本：
{{transcript_text}}

### 输出要求：
直接输出修正后的文本，不要添加任何解释。""",
        description="仅做最小必要修正"
    ),
    "speech-to-text-refiner": PromptTemplate(
        name="个人叙述精修",
        system_prompt=REFINER_SYSTEM_PROMPT + "\n\n### 个人叙述特殊要求：\n- 保持第一人称叙述风格\n- 加粗核心数字（金额、年份、时间）",
        user_prompt_template=f"""{REFINER_FEW_SHOT_EXAMPLES}

### 待处理文本：
{{transcript_text}}

### 输出要求：
- 加粗核心数字（金额、年份、时间）
- 直接输出修正后的文本，不要添加任何解释。""",
        description="专门用于修正个人叙述/演讲的转录文本"
    ),
}


# ============================================================
# 配置类
# ============================================================

@dataclass
class LLMEnhancerConfig:
    """LLM 增强器配置（深度重构版）"""
    enabled: bool = False
    provider: str = "openai"
    model: str = "gpt-4o-mini"
    max_tokens: int = 8000
    temperature: float = 0.3  # 保持默认温度兼容性

    # 语义块合并配置
    merge_blocks: bool = True  # 是否启用语义块合并
    min_block_size: int = 300  # 最小块大小（字符数）
    max_block_size: int = 1500  # 最大块大小（字符数）
    min_block_duration: float = 15.0  # 最小时长（秒）

    # 回退策略
    fallback_on_error: bool = True

    # 调试模式
    debug: bool = False

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
# LLM 增强器（深度重构版）
# ============================================================

class LLMTranscriptEnhancer:
    """LLM 转录文本增强器（深度重构版）"""

    def __init__(self, config: LLMEnhancerConfig):
        """
        初始化增强器

        Args:
            config: 增强器配置
        """
        self.config = config
        self.provider = self._create_provider()
        self.template = config.get_template()

        # 配置日志
        if config.debug:
            logging.basicConfig(level=logging.DEBUG)
            logger.setLevel(logging.DEBUG)

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

    def _merge_utterances_to_blocks(
        self,
        utterances: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        将破碎的 ASR 句子合并为具备上下文的文本块

        策略：
        1. 按时间顺序合并连续的 utterances
        2. 每个块至少包含 min_block_size 字符或 min_block_duration 秒
        3. 每个块不超过 max_block_size 字符

        Args:
            utterances: 原始 utterance 列表

        Returns:
            合并后的文本块列表
        """
        if not utterances:
            return []

        if not self.config.merge_blocks:
            # 不合并，直接返回单块
            return [{
                "text": " ".join(u["text"] for u in utterances),
                "start": utterances[0]["start"],
                "end": utterances[-1]["end"],
                "utterance_count": len(utterances)
            }]

        blocks = []
        current_block = {
            "text": "",
            "start": utterances[0]["start"],
            "end": utterances[0]["end"],
            "utterance_indices": []
        }

        for i, u in enumerate(utterances):
            current_text = current_block["text"] + " " + u["text"]
            current_duration = u["end"] - current_block["start"]

            # 检查是否应该开始新块
            should_split = (
                len(current_text) > self.config.max_block_size or
                (len(current_text) >= self.config.min_block_size and
                 current_duration >= self.config.min_block_duration)
            )

            if should_split and len(current_text) > self.config.min_block_size:
                # 保存当前块
                current_block["text"] = current_block["text"].strip()
                current_block["utterance_count"] = len(current_block["utterance_indices"])
                blocks.append(current_block)

                # 开始新块
                current_block = {
                    "text": u["text"],
                    "start": u["start"],
                    "end": u["end"],
                    "utterance_indices": [i]
                }
            else:
                # 继续累加到当前块
                current_block["text"] = current_text.strip()
                current_block["end"] = u["end"]
                current_block["utterance_indices"].append(i)

        # 添加最后一个块
        if current_block["text"]:
            current_block["utterance_count"] = len(current_block["utterance_indices"])
            blocks.append(current_block)

        logger.debug(f"合并 {len(utterances)} 个 utterances 为 {len(blocks)} 个块")
        return blocks

    def _clean_enhanced_text(self, text: str) -> str:
        """
        清洗增强后的文本

        Args:
            text: 待清洗的文本

        Returns:
            清洗后的文本
        """
        if not text:
            return text

        # 去除首尾空格
        text = text.strip()

        # 替换多个连续空格为单个空格
        text = re.sub(r' +', ' ', text)

        # 去除换行符（除非是段落分隔）
        text = re.sub(r'(?<!\n)\n(?!\n)', ' ', text)

        # 去除标点符号前的空格
        text = re.sub(r'\s+([，。！？；：、,\.!?;:])', r'\1', text)

        # 标准化引号
        text = text.replace('"', '"').replace('"', '"')

        # 去除段落间的多余空行
        text = re.sub(r'\n{3,}', '\n\n', text)

        return text.strip()

    def enhance(
        self,
        transcript_text: str,
        progress_callback: Optional[Callable] = None
    ) -> EnhancedTranscriptResult:
        """
        增强转录文本（深度重构版）

        Args:
            transcript_text: 原始转录文本（完整文本）
            progress_callback: 进度回调 (stage, progress)

        Returns:
            EnhancedTranscriptResult 实例
        """
        if progress_callback:
            progress_callback("enhancement_start", 0)

        # 预处理
        transcript_text = transcript_text.strip()
        transcript_text = re.sub(r' +', ' ', transcript_text)

        # 构建提示词
        from summarizer.llm.base import LLMMessage

        system_prompt = self.template.system_prompt
        user_prompt = self.template.format_user_prompt(transcript_text)

        # 调试日志
        if self.config.debug:
            logger.debug(f"=== System Prompt ===\n{system_prompt}")
            logger.debug(f"=== User Prompt ===\n{user_prompt[:500]}...")

        messages = [
            LLMMessage(role="system", content=system_prompt),
            LLMMessage(role="user", content=user_prompt)
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

            # 调试日志
            if self.config.debug:
                logger.debug(f"=== LLM Response ===\n{enhanced_text[:500]}...")

            # 后处理清洗
            enhanced_text = self._clean_enhanced_text(enhanced_text)

            if progress_callback:
                progress_callback("enhancement_complete", 100)

            return EnhancedTranscriptResult(
                original_text=transcript_text,
                enhanced_text=enhanced_text,
                metadata={
                    "provider": self.config.provider,
                    "model": self.config.model,
                    "template": self.template.name,
                    "fallback_used": False,
                    "blocks_merged": False
                },
                success=True,
                fallback_used=False
            )

        except Exception as e:
            logger.error(f"LLM 调用失败: {e}")
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

    def enhance_utterances(
        self,
        utterances: List[Dict[str, Any]],
        progress_callback: Optional[Callable] = None
    ) -> EnhancedTranscriptResult:
        """
        增强 utterances 列表（带语义块合并）

        Args:
            utterances: 原始 utterance 列表
            progress_callback: 进度回调

        Returns:
            EnhancedTranscriptResult 实例
        """
        if not utterances:
            return EnhancedTranscriptResult(
                original_text="",
                enhanced_text="",
                metadata={"error": "empty_utterances"},
                success=False
            )

        if progress_callback:
            progress_callback("merging_blocks", 10)

        # 合并为语义块
        blocks = self._merge_utterances_to_blocks(utterances)

        if len(blocks) == 1:
            # 单块，直接处理
            result = self.enhance(blocks[0]["text"], progress_callback)
            result.metadata["blocks_merged"] = False
            result.metadata["original_utterance_count"] = len(utterances)
            return result

        # 多块处理：逐块增强后合并
        enhanced_blocks = []
        original_text = " ".join(u["text"] for u in utterances)

        for i, block in enumerate(blocks):
            if progress_callback:
                progress_callback(f"processing_block_{i+1}", 10 + (i * 80 // len(blocks)))

            result = self.enhance(block["text"])
            if result.success:
                enhanced_blocks.append(result.enhanced_text)
            else:
                # 块失败，使用原文
                enhanced_blocks.append(block["text"])

        # 合并所有块
        enhanced_text = " ".join(enhanced_blocks)

        # 最终清洗
        enhanced_text = self._clean_enhanced_text(enhanced_text)

        if progress_callback:
            progress_callback("enhancement_complete", 100)

        return EnhancedTranscriptResult(
            original_text=original_text,
            enhanced_text=enhanced_text,
            metadata={
                "provider": self.config.provider,
                "model": self.config.model,
                "template": self.template.name,
                "blocks_merged": True,
                "block_count": len(blocks),
                "original_utterance_count": len(utterances)
            },
            success=True,
            fallback_used=False
        )


# ============================================================
# 文本处理工具
# ============================================================

def preprocess_utterances(
    utterances: List[Dict[str, Any]],
    min_gap_ms: int = 500,
    max_chunk_duration_ms: int = 30000
) -> List[Dict[str, Any]]:
    """
    预处理 utterances，将小片段合并为语义块

    Args:
        utterances: 原始 utterance 列表
        min_gap_ms: 最小时间间隔（毫秒）
        max_chunk_duration_ms: 最大块时长（毫秒）

    Returns:
        合并后的 utterance 列表
    """
    if not utterances:
        return []

    result = []
    current_chunk = {
        "start": utterances[0]["start"],
        "end": utterances[0]["end"],
        "text": utterances[0]["text"],
        "utterance_indices": [0]
    }

    for i in range(1, len(utterances)):
        curr = utterances[i]
        gap_ms = int(curr["start"] * 1000) - int(current_chunk["end"] * 1000)
        chunk_duration = int(current_chunk["end"] * 1000) - int(current_chunk["start"] * 1000)

        should_merge = (
            gap_ms < min_gap_ms and
            chunk_duration < max_chunk_duration_ms
        )

        if should_merge:
            current_chunk["end"] = curr["end"]
            current_chunk["text"] += " " + curr["text"]
            current_chunk["utterance_indices"].append(i)
        else:
            result.append(current_chunk)
            current_chunk = {
                "start": curr["start"],
                "end": curr["end"],
                "text": curr["text"],
                "utterance_indices": [i]
            }

    result.append(current_chunk)
    return result


def clean_enhanced_text(text: str) -> str:
    """
    清洗增强后的文本

    Args:
        text: 待清洗的文本

    Returns:
        清洗后的文本
    """
    if not text:
        return text

    text = text.strip()
    text = re.sub(r' +', ' ', text)
    text = re.sub(r'(?<!\n)\n(?!\n)', ' ', text)
    text = re.sub(r'\s+([，。！？；：、,\.!?;:])', r'\1', text)
    text = text.replace('"', '"').replace('"', '"')
    text = re.sub(r'\n{3,}', '\n\n', text)

    return text.strip()


def map_enhanced_text_to_sentences(
    enhanced_text: str,
    original_sentences: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    将增强文本映射回原始 sentences

    Args:
        enhanced_text: LLM 返回的增强文本
        original_sentences: 原始 sentence 列表

    Returns:
        映射后的 sentence 列表
    """
    if not original_sentences:
        return []

    sentences_in_enhanced = _split_into_sentences(enhanced_text)

    if len(sentences_in_enhanced) == len(original_sentences):
        return [
            {**orig, "enhanced_text": sentences_in_enhanced[i]}
            for i, orig in enumerate(original_sentences)
        ]

    # 比例映射
    result = []
    enhanced_index = 0
    total_enhanced_len = sum(len(s) for s in sentences_in_enhanced)
    current_len = 0

    for orig in original_sentences:
        orig_len = len(orig["text"])
        target_len = int(orig_len * total_enhanced_len / sum(len(s["text"]) for s in original_sentences))

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

    while enhanced_index < len(sentences_in_enhanced):
        if result:
            result[-1]["enhanced_text"] += " " + sentences_in_enhanced[enhanced_index]
        enhanced_index += 1

    return result


def _split_into_sentences(text: str) -> List[str]:
    """
    将文本分割成句子

    Args:
        text: 输入文本

    Returns:
        句子列表
    """
    text = text.replace("！", "!").replace("？", "?").replace("。", ".")
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

    if current.strip():
        sentences.append(current.strip())

    return sentences if sentences else [text]
