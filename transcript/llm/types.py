"""
PR4 Types - 枚举类型和数据结构

定义 PR4 高精度增强模块所需的所有枚举类型和数据结构。
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum


# ============================================================
# 枚举类型
# ============================================================

class MappingQuality(Enum):
    """映射质量等级"""
    HIGH = "high"       # 精确匹配或高相似度
    MEDIUM = "medium"   # embedding 匹配
    LOW = "low"         # 位置回退


class FallbackLevel(Enum):
    """回退级别"""
    NONE = "none"              # 无回退
    SENTENCE = "sentence"      # 单句回退
    CHUNK = "chunk"            # 整块回退
    FINAL = "final"            # 完全失败


class MappingMethod(Enum):
    """映射方法"""
    EXACT = "exact"         # JSON 精确匹配
    EMBEDDING = "embedding" # 相似度匹配
    POSITION = "position"   # 位置回退


# ============================================================
# 数据结构
# ============================================================

@dataclass
class MappingInfo:
    """映射信息（子结构）"""
    quality: MappingQuality
    method: MappingMethod
    trace: Dict[str, Any]
    embedding_similarity: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "quality": self.quality.value,
            "method": self.method.value,
            "embedding_similarity": self.embedding_similarity,
            "trace": self.trace
        }


@dataclass
class FallbackInfo:
    """回退信息（子结构）"""
    level: FallbackLevel
    reason: Optional[str] = None
    history: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "level": self.level.value,
            "reason": self.reason,
            "history": self.history
        }

    def add_history(self, entry: str):
        """添加回退历史记录"""
        self.history.append(entry)


@dataclass
class ConfidenceBreakdown:
    """置信度分解"""
    total: float
    embedding_similarity: Optional[float] = None
    length_ratio: Optional[float] = None
    llm_metadata: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        result = {"total": self.total}
        if self.embedding_similarity is not None:
            result["embedding_similarity"] = self.embedding_similarity
        if self.length_ratio is not None:
            result["length_ratio"] = self.length_ratio
        if self.llm_metadata is not None:
            result["llm_metadata"] = self.llm_metadata
        return result


@dataclass
class SentenceMappingResult:
    """单句映射结果（Mapper 输出）"""
    sentence_index: int
    original_text: str
    enhanced_text: str

    # 映射信息
    mapping_quality: MappingQuality
    mapping_method: MappingMethod
    embedding_similarity: Optional[float] = None

    # 追踪
    mapping_trace: Dict[str, Any] = field(default_factory=dict)

    # 时间戳
    processed_at: str = ""

    def __post_init__(self):
        if not self.processed_at:
            from datetime import datetime
            self.processed_at = datetime.now().isoformat()


@dataclass
class MultiRoundMetadata:
    """多轮增强元数据"""
    round: int                      # 第几轮（2, 3, ...）
    input_sentences: List[Dict]     # 输入的句子列表
    tokens_used: int                # 本轮消耗的 tokens
    model_used: str                 # 使用的模型
    template_used: str              # 使用的模板
    started_at: str
    completed_at: str
    duration_ms: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "round": self.round,
            "input_sentences": self.input_sentences,
            "tokens_used": self.tokens_used,
            "model_used": self.model_used,
            "template_used": self.template_used,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "duration_ms": self.duration_ms
        }


@dataclass
class MultiRoundResult:
    """多轮增强结果"""
    task_name: str                  # "highlights" / "summary" / "action_items"
    content: Any                    # str 或 List[str]（取决于任务类型）

    # 结构化 metadata
    metadata: MultiRoundMetadata

    success: bool
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "task_name": self.task_name,
            "content": self.content,
            "metadata": self.metadata.to_dict(),
            "success": self.success
        }
        if self.error_message:
            result["error_message"] = self.error_message
        return result
