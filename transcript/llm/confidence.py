"""
Confidence Calculator - 置信度计算器

PR4: 多特征加权置信度计算，支持权重重归一和缺失特征处理。
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional, Tuple
from datetime import datetime


@dataclass
class ConfidenceCalculatorConfig:
    """置信度计算器配置"""
    embedding_similarity_weight: float = 0.6
    length_ratio_weight: float = 0.2
    llm_metadata_weight: float = 0.2

    def __post_init__(self):
        total = (
            self.embedding_similarity_weight
            + self.length_ratio_weight
            + self.llm_metadata_weight
        )
        if abs(total - 1.0) > 0.01:
            raise ValueError(f"权重总和应为 1.0，当前为 {total}")

    def to_dict(self) -> Dict[str, float]:
        return {
            "embedding_similarity": self.embedding_similarity_weight,
            "length_ratio": self.length_ratio_weight,
            "llm_metadata": self.llm_metadata_weight,
        }


class ConfidenceCalculator:
    """置信度计算器"""

    def __init__(self, config: Optional[ConfidenceCalculatorConfig] = None):
        """
        初始化计算器

        Args:
            config: 计算器配置，默认使用标准权重
        """
        self.config = config or ConfidenceCalculatorConfig()

    def calculate(
        self,
        original: str,
        enhanced: str,
        embedding_similarity: Optional[float] = None,
        llm_metadata: Optional[Dict[str, Any]] = None
    ) -> "ConfidenceBreakdown":
        """
        计算置信度

        Args:
            original: 原始文本
            enhanced: 增强文本
            embedding_similarity: embedding 相似度（可选）
            llm_metadata: LLM 元数据（可选）

        Returns:
            ConfidenceBreakdown: 包含总分和各特征分值
        """
        from transcript.llm.types import ConfidenceBreakdown

        scores = {}

        # 特征 1: Embedding 相似度（可选）
        scores["embedding_similarity"] = embedding_similarity

        # 特征 2: 长度比率（必须有）
        scores["length_ratio"] = self._calculate_length_ratio_score(original, enhanced)

        # 特征 3: LLM 元数据（可选）
        scores["llm_metadata"] = self._parse_llm_metadata(llm_metadata)

        # 权重重归一
        available = {k: v for k, v in scores.items() if v is not None}
        total_weight = sum(self._get_weight(k) for k in available.keys())

        if total_weight == 0:
            # 所有特征都缺失，返回默认值
            return ConfidenceBreakdown(
                total=0.5,
                embedding_similarity=None,
                length_ratio=scores.get("length_ratio"),
                llm_metadata=None
            )

        renormalized = {
            k: self._get_weight(k) / total_weight
            for k in available.keys()
        }

        # 计算总分
        total = sum(available[k] * renormalized[k] for k in available.keys())

        return ConfidenceBreakdown(
            total=total,
            embedding_similarity=scores.get("embedding_similarity"),
            length_ratio=scores["length_ratio"],
            llm_metadata=scores.get("llm_metadata")
        )

    def _get_weight(self, feature: str) -> float:
        """获取特征权重"""
        weights = self.config.to_dict()
        return weights.get(feature, 0.0)

    def _calculate_length_ratio_score(self, original: str, enhanced: str) -> float:
        """
        计算长度比率得分

        理想范围: 原文长度的 0.8 - 1.5 倍
        分段函数 clamp 到 [0, 1]

        Args:
            original: 原始文本
            enhanced: 增强文本

        Returns:
            float: 长度比率得分 [0, 1]
        """
        orig_len = len(original)
        enh_len = len(enhanced)

        if orig_len == 0:
            return 0.0 if enh_len == 0 else 0.3

        ratio = enh_len / orig_len

        # 分段函数
        if 0.8 <= ratio <= 1.5:
            return 1.0  # 理想范围
        elif 0.5 <= ratio < 0.8:
            # 线性插值: 0.5 → 0.6, 0.8 → 1.0
            return 0.6 + (ratio - 0.5) * (1.0 - 0.6) / (0.8 - 0.5)
        elif 1.5 < ratio <= 3.0:
            # 线性插值: 1.5 → 1.0, 3.0 → 0.2
            return 1.0 - (ratio - 1.5) * (1.0 - 0.2) / (3.0 - 1.5)
        else:
            # 过度压缩或扩展
            return 0.2 if ratio > 3.0 else 0.3

    def _parse_llm_metadata(self, metadata: Optional[Dict[str, Any]]) -> Optional[float]:
        """
        解析 LLM 元数据

        Args:
            metadata: LLM 返回的元数据

        Returns:
            Optional[float]: 元数据分数，无元数据时返回 None
        """
        if metadata is None:
            return None

        if not metadata:
            return 0.5

        finish_reason = metadata.get("finish_reason", "")

        if finish_reason == "stop":
            return 1.0
        elif finish_reason == "length":
            return 0.7  # 可能被截断
        else:
            return 0.5


# ============================================================
# 便捷函数
# ============================================================

def calculate_confidence(
    original: str,
    enhanced: str,
    embedding_similarity: Optional[float] = None,
    llm_metadata: Optional[Dict[str, Any]] = None,
    config: Optional[ConfidenceCalculatorConfig] = None
) -> "ConfidenceBreakdown":
    """
    便捷函数：计算置信度

    Args:
        original: 原始文本
        enhanced: 增强文本
        embedding_similarity: embedding 相似度（可选）
        llm_metadata: LLM 元数据（可选）
        config: 计算器配置（可选）

    Returns:
        ConfidenceBreakdown: 置信度分解结果
    """
    calculator = ConfidenceCalculator(config)
    return calculator.calculate(
        original=original,
        enhanced=enhanced,
        embedding_similarity=embedding_similarity,
        llm_metadata=llm_metadata
    )
