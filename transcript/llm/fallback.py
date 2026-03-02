"""
Fallback Engine - 回退引擎

PR4: 根据置信度和规则决定是否回退到原文。
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime
import copy

from transcript.llm.types import (
    FallbackLevel,
    FallbackInfo,
    ConfidenceBreakdown,
    MappingQuality,
    MappingMethod,
)
from transcript.llm.confidence import ConfidenceCalculator, ConfidenceCalculatorConfig


@dataclass
class FallbackConfig:
    """回退配置"""
    # 单句回退控制
    enable_per_sentence_fallback: bool = False
    confidence_threshold: float = 0.6
    embedding_similarity_threshold: float = 0.7

    # 长度比率阈值
    min_length_ratio: float = 0.3
    max_length_ratio: float = 3.0

    # 回退到原文
    fallback_to_original: bool = True

    def __post_init__(self):
        if not 0.0 <= self.confidence_threshold <= 1.0:
            raise ValueError(f"confidence_threshold 必须在 [0, 1] 范围内: {self.confidence_threshold}")
        if not 0.0 <= self.embedding_similarity_threshold <= 1.0:
            raise ValueError(f"embedding_similarity_threshold 必须在 [0, 1] 范围内: {self.embedding_similarity_threshold}")
        if self.min_length_ratio < 0:
            raise ValueError(f"min_length_ratio 必须 >= 0: {self.min_length_ratio}")
        if self.max_length_ratio <= self.min_length_ratio:
            raise ValueError(f"max_length_ratio 必须 > min_length_ratio: {self.max_length_ratio} <= {self.min_length_ratio}")


@dataclass
class SentenceCandidate:
    """句子候选项（包含原文和增强文本）"""
    sentence_index: int
    original_text: str
    enhanced_text: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    # 映射信息
    mapping_quality: Optional[MappingQuality] = None
    mapping_method: Optional[MappingMethod] = None
    embedding_similarity: Optional[float] = None
    mapping_trace: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if not self.original_text:
            raise ValueError("original_text 不能为空")
        if self.enhanced_text is None:
            raise ValueError("enhanced_text 不能为 None")


@dataclass
class EnhancedSentence:
    """增强后的句子（PR4 扩展版本）"""
    sentence_index: int
    start_ms: int
    end_ms: int
    original_text: str
    enhanced_text: str

    # PR3 字段
    confidence: float = 1.0

    # PR4 扩展字段（结构化）
    mapping: Optional["MappingInfo"] = None
    fallback: Optional["FallbackInfo"] = None
    scores: Optional["ConfidenceBreakdown"] = None

    def __post_init__(self):
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"confidence 必须在 [0, 1] 范围内: {self.confidence}")

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = {
            "sentence_index": self.sentence_index,
            "start_ms": self.start_ms,
            "end_ms": self.end_ms,
            "original_text": self.original_text,
            "enhanced_text": self.enhanced_text,
            "confidence": self.confidence
        }
        if self.mapping:
            result["mapping"] = self.mapping.to_dict()
        if self.fallback:
            result["fallback"] = self.fallback.to_dict()
        if self.scores:
            result["scores"] = self.scores.to_dict()
        return result


class FallbackEngine:
    """回退引擎

    Priority 0: LLM 调用失败/JSON 解析失败 → CHUNK fallback
    Priority 1: 单句质量问题 → SENTENCE fallback
    Priority 2: 继续处理 → 接受增强文本
    """

    def __init__(
        self,
        config: Optional[FallbackConfig] = None,
        confidence_calculator: Optional[ConfidenceCalculator] = None
    ):
        """
        初始化回退引擎

        Args:
            config: 回退配置
            confidence_calculator: 置信度计算器（可选，默认创建新实例）
        """
        self.config = config or FallbackConfig()
        self.confidence_calculator = confidence_calculator or ConfidenceCalculator()

    def process_sentences(
        self,
        candidates: List[SentenceCandidate],
        progress_callback: Optional[Callable] = None
    ) -> List[EnhancedSentence]:
        """
        处理句子候选项，应用回退逻辑

        Args:
            candidates: 句子候选项列表
            progress_callback: 进度回调

        Returns:
            List[EnhancedSentence]: 处理后的增强句子列表
        """
        results = []

        for i, candidate in enumerate(candidates):
            if progress_callback:
                progress_callback("processing_sentence", i / len(candidates) * 100)

            result = self._process_single_sentence(candidate)
            results.append(result)

        if progress_callback:
            progress_callback("fallback_complete", 100)

        return results

    def _process_single_sentence(self, candidate: SentenceCandidate) -> EnhancedSentence:
        """
        处理单个句子

        Args:
            candidate: 句子候选项

        Returns:
            EnhancedSentence: 处理后的增强句子
        """
        from transcript.llm.types import MappingInfo, FallbackInfo

        # 计算置信度
        breakdown = self.confidence_calculator.calculate(
            original=candidate.original_text,
            enhanced=candidate.enhanced_text,
            embedding_similarity=candidate.embedding_similarity
        )

        # 判断是否需要回退
        fallback_decision = self._should_fallback(candidate, breakdown)

        if fallback_decision["should_fallback"]:
            # 回退到原文
            fallback_info = FallbackInfo(
                level=fallback_decision["level"],
                reason=fallback_decision["reason"],
                history=[fallback_decision["reason"]]
            )
            enhanced_text = candidate.original_text
            confidence = 0.0
        else:
            # 接受增强文本
            fallback_info = FallbackInfo(level=FallbackLevel.NONE)
            enhanced_text = candidate.enhanced_text
            confidence = breakdown.total

        # 构建 mapping info
        mapping_info = None
        if candidate.mapping_quality and candidate.mapping_method:
            mapping_info = MappingInfo(
                quality=candidate.mapping_quality,
                method=candidate.mapping_method,
                trace=candidate.mapping_trace or {},
                embedding_similarity=candidate.embedding_similarity
            )

        return EnhancedSentence(
            sentence_index=candidate.sentence_index,
            start_ms=candidate.metadata.get("start_ms", 0),
            end_ms=candidate.metadata.get("end_ms", 0),
            original_text=candidate.original_text,
            enhanced_text=enhanced_text,
            confidence=confidence,
            mapping=mapping_info,
            fallback=fallback_info,
            scores=breakdown
        )

    def _should_fallback(
        self,
        candidate: SentenceCandidate,
        breakdown: ConfidenceBreakdown
    ) -> Dict[str, Any]:
        """
        判断是否需要回退

        Args:
            candidate: 句子候选项
            breakdown: 置信度分解

        Returns:
            Dict: {"should_fallback": bool, "level": FallbackLevel, "reason": str}
        """
        # Priority 1: 单句回退（如果启用）
        if self.config.enable_per_sentence_fallback:
            # 检查置信度阈值
            if breakdown.total < self.config.confidence_threshold:
                return {
                    "should_fallback": True,
                    "level": FallbackLevel.SENTENCE,
                    "reason": f"low_confidence:{breakdown.total:.2f}"
                }

            # 检查 embedding 相似度阈值（仅当有 embedding 数据时）
            if (breakdown.embedding_similarity is not None
                and breakdown.embedding_similarity < self.config.embedding_similarity_threshold):
                return {
                    "should_fallback": True,
                    "level": FallbackLevel.SENTENCE,
                    "reason": f"semantic_drift:{breakdown.embedding_similarity:.2f}"
                }

        # 检查长度比率异常（无论是否启用单句回退）
        length_ratio = len(candidate.enhanced_text) / max(len(candidate.original_text), 1)
        if length_ratio > self.config.max_length_ratio:
            return {
                "should_fallback": True,
                "level": FallbackLevel.SENTENCE,
                "reason": f"excessive_expansion:{length_ratio:.2f}"
            }

        if length_ratio < self.config.min_length_ratio:
            return {
                "should_fallback": True,
                "level": FallbackLevel.SENTENCE,
                "reason": f"excessive_compression:{length_ratio:.2f}"
            }

        # 不需要回退
        return {
            "should_fallback": False,
            "level": FallbackLevel.NONE,
            "reason": None
        }

    def create_chunk_fallback(
        self,
        original_sentences: List[Dict],
        reason: str = "chunk_level_failure"
    ) -> List[EnhancedSentence]:
        """
        创建整块回退结果

        Args:
            original_sentences: 原始句子列表
            reason: 回退原因

        Returns:
            List[EnhancedSentence]: 全部使用原文的增强句子列表
        """
        from transcript.llm.types import FallbackInfo

        results = []
        for orig in original_sentences:
            fallback_info = FallbackInfo(
                level=FallbackLevel.CHUNK,
                reason=reason,
                history=[reason]
            )

            results.append(EnhancedSentence(
                sentence_index=orig["sentence_index"],
                start_ms=orig.get("start_ms", 0),
                end_ms=orig.get("end_ms", 0),
                original_text=orig["text"],
                enhanced_text=orig["text"],  # 使用原文
                confidence=0.0,
                fallback=fallback_info
            ))

        return results


# ============================================================
# 便捷函数
# ============================================================

def apply_fallback(
    candidates: List[SentenceCandidate],
    config: Optional[FallbackConfig] = None,
    progress_callback: Optional[Callable] = None
) -> List[EnhancedSentence]:
    """
    便捷函数：应用回退逻辑

    Args:
        candidates: 句子候选项列表
        config: 回退配置
        progress_callback: 进度回调

    Returns:
        List[EnhancedSentence]: 处理后的增强句子列表
    """
    engine = FallbackEngine(config)
    return engine.process_sentences(candidates, progress_callback)
