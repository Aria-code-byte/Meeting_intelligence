"""
Sentence Mapper - 句子映射引擎

PR4: 多策略映射引擎，支持精确匹配、embedding 相似度匹配和位置回退。
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime
import re
import json

from transcript.llm.types import (
    MappingQuality,
    MappingMethod,
    SentenceMappingResult,
)


# ============================================================
# 抽象基类
# ============================================================

class SentenceMapper(ABC):
    """句子映射引擎抽象基类"""

    @abstractmethod
    def map(
        self,
        enhanced_text: str,
        original_sentences: List[Dict],
        progress_callback: Optional[callable] = None
    ) -> List[SentenceMappingResult]:
        """
        执行映射，返回带 trace 的结果

        Args:
            enhanced_text: LLM 返回的增强文本
            original_sentences: 原始句子列表，每项包含 sentence_index, text
            progress_callback: 进度回调

        Returns:
            List[SentenceMappingResult]: 映射结果列表
        """
        pass

    @abstractmethod
    def supports_method(self) -> MappingMethod:
        """返回支持的映射方法名"""
        pass

    def _create_trace(
        self,
        method: str,
        input_size: int,
        output_size: int,
        duration_ms: int,
        **kwargs
    ) -> Dict[str, Any]:
        """创建映射追踪记录"""
        return {
            "method": method,
            "input_sentences": input_size,
            "output_sentences": output_size,
            "duration_ms": duration_ms,
            "timestamp": datetime.now().isoformat(),
            **kwargs
        }


# ============================================================
# ExactMapper - 精确匹配（JSON 编号）
# ============================================================

class ExactMapper(SentenceMapper):
    """基于句子编号的精确匹配"""

    def __init__(self, strict: bool = False):
        """
        初始化 ExactMapper

        Args:
            strict: 严格模式，JSON 解析失败时抛出异常
        """
        self.strict = strict

    def supports_method(self) -> MappingMethod:
        return MappingMethod.EXACT

    def map(
        self,
        enhanced_text: str,
        original_sentences: List[Dict],
        progress_callback: Optional[callable] = None
    ) -> List[SentenceMappingResult]:
        """
        基于 JSON 编号精确映射

        Args:
            enhanced_text: LLM 返回的 JSON 格式增强文本
            original_sentences: 原始句子列表

        Returns:
            List[SentenceMappingResult]

        Raises:
            ParseError: strict=True 且 JSON 解析失败
        """
        from transcript.llm.enhancer import ParseError

        start_time = datetime.now()

        # 尝试解析 JSON
        try:
            parsed = self._parse_llm_output(enhanced_text)
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            if self.strict:
                raise ParseError(f"JSON 解析失败: {e}") from e
            # 非严格模式，返回空结果让调用者降级
            return []

        # 检查 schema
        if not self._is_valid_schema(parsed):
            if self.strict:
                raise ParseError("JSON schema 不符合要求")
            return []

        # 构建 sentence_index 到 句子文本的映射
        enhanced_dict = {
            item["sentence_index"]: item.get("enhanced_text", "")
            for item in parsed.get("sentences", [])
        }

        # 构建结果
        results = []
        for orig in original_sentences:
            idx = orig["sentence_index"]
            if idx in enhanced_dict:
                results.append(SentenceMappingResult(
                    sentence_index=idx,
                    original_text=orig["text"],
                    enhanced_text=enhanced_dict[idx],
                    mapping_quality=MappingQuality.HIGH,
                    mapping_method=MappingMethod.EXACT,
                    mapping_trace=self._create_trace(
                        method="exact",
                        input_size=len(original_sentences),
                        output_size=len(results),
                        duration_ms=int((datetime.now() - start_time).total_seconds() * 1000),
                        matched_indices=len(enhanced_dict)
                    )
                ))

        return results

    def _parse_llm_output(self, output: str) -> Dict[str, Any]:
        """
        解析 LLM 输出

        支持纯 JSON 和 Markdown JSON 代码块
        """
        # 尝试直接解析
        try:
            return json.loads(output)
        except json.JSONDecodeError:
            pass

        # 尝试提取 Markdown 代码块
        if "```json" in output:
            start = output.find("```json") + 7
            end = output.find("```", start)
            if end > start:
                return json.loads(output[start:end].strip())

        # 尝试提取任意代码块
        if "```" in output:
            start = output.find("```") + 3
            # 找到换行符后开始
            newline = output.find("\n", start)
            if newline > start:
                start = newline + 1
            end = output.find("```", start)
            if end > start:
                try:
                    return json.loads(output[start:end].strip())
                except json.JSONDecodeError:
                    pass

        # 都失败，抛出异常
        raise json.JSONDecodeError("无法解析 JSON", output, 0)

    def _is_valid_schema(self, data: Dict[str, Any]) -> bool:
        """
        验证 JSON schema

        要求:
        - 必须有 sentences 字段
        - 每项必须有 sentence_index 和 enhanced_text
        """
        if "sentences" not in data:
            return False

        for item in data["sentences"]:
            if not isinstance(item, dict):
                return False
            if "sentence_index" not in item:
                return False
            if "enhanced_text" not in item:
                return False

        return True


# ============================================================
# PositionMapper - 位置回退映射（复用 PR3）
# ============================================================

class PositionMapper(SentenceMapper):
    """位置回退映射（PR3 策略）"""

    def supports_method(self) -> MappingMethod:
        return MappingMethod.POSITION

    def map(
        self,
        enhanced_text: str,
        original_sentences: List[Dict],
        progress_callback: Optional[callable] = None
    ) -> List[SentenceMappingResult]:
        """
        按位置/长度比例映射（PR3 策略）

        Args:
            enhanced_text: 增强文本
            original_sentences: 原始句子列表

        Returns:
            List[SentenceMappingResult]
        """
        start_time = datetime.now()

        if not original_sentences:
            return []

        # 按标点分割增强文本
        sentences_in_enhanced = self._split_into_sentences(enhanced_text)

        # 如果分割出的句子数量与原始接近，直接映射
        if len(sentences_in_enhanced) == len(original_sentences):
            results = [
                SentenceMappingResult(
                    sentence_index=orig["sentence_index"],
                    original_text=orig["text"],
                    enhanced_text=sentences_in_enhanced[i],
                    mapping_quality=MappingQuality.LOW,
                    mapping_method=MappingMethod.POSITION,
                    mapping_trace=self._create_trace(
                        method="position",
                        input_size=len(original_sentences),
                        output_size=len(original_sentences),
                        duration_ms=int((datetime.now() - start_time).total_seconds() * 1000),
                        strategy="direct_match"
                    )
                )
                for i, orig in enumerate(original_sentences)
            ]
            return results

        # 如果数量不一致，使用比例映射
        results = self._map_by_ratio(
            sentences_in_enhanced,
            original_sentences,
            start_time
        )

        return results

    def _split_into_sentences(self, text: str) -> List[str]:
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

    def _map_by_ratio(
        self,
        enhanced_sentences: List[str],
        original_sentences: List[Dict],
        start_time: datetime
    ) -> List[SentenceMappingResult]:
        """按长度比例映射"""
        result = []
        enhanced_index = 0
        total_enhanced_len = sum(len(s) for s in enhanced_sentences)
        current_len = 0

        for orig in original_sentences:
            # 计算当前原始句子应该占用的增强文本长度
            orig_len = len(orig["text"])
            target_len = int(
                orig_len * total_enhanced_len /
                sum(len(s["text"]) for s in original_sentences)
            )

            # 累积增强文本直到达到目标长度
            enhanced_parts = []
            while (enhanced_index < len(enhanced_sentences) and
                   current_len < target_len):
                enhanced_parts.append(enhanced_sentences[enhanced_index])
                current_len += len(enhanced_sentences[enhanced_index])
                enhanced_index += 1

            result.append(SentenceMappingResult(
                sentence_index=orig["sentence_index"],
                original_text=orig["text"],
                enhanced_text="".join(enhanced_parts),
                mapping_quality=MappingQuality.LOW,
                mapping_method=MappingMethod.POSITION,
                mapping_trace=self._create_trace(
                    method="position",
                    input_size=len(original_sentences),
                    output_size=len(result),
                    duration_ms=int((datetime.now() - start_time).total_seconds() * 1000),
                    strategy="ratio_mapping"
                )
            ))
            current_len = 0

        # 处理剩余的增强文本（如果有）
        while enhanced_index < len(enhanced_sentences):
            if result:
                # 追加到最后一个句子
                last = result[-1]
                last.enhanced_text += " " + enhanced_sentences[enhanced_index]
            enhanced_index += 1

        return result


# ============================================================
# EmbeddingMapper - Embedding 相似度匹配
# ============================================================

class EmbeddingMapper(SentenceMapper):
    """基于 embedding 相似度的一对一匹配"""

    def __init__(
        self,
        similarity_threshold: float = 0.7,
        match_rate_threshold: float = 0.6,
        enable_cache: bool = True
    ):
        """
        初始化 EmbeddingMapper

        Args:
            similarity_threshold: 相似度阈值，低于此值不匹配
            match_rate_threshold: 匹配率阈值，低于此值触发 PositionMapper
            enable_cache: 启用 embedding 缓存
        """
        self.similarity_threshold = similarity_threshold
        self.match_rate_threshold = match_rate_threshold
        self.enable_cache = enable_cache
        self._cache = {} if enable_cache else None

    def supports_method(self) -> MappingMethod:
        return MappingMethod.EMBEDDING

    def map(
        self,
        enhanced_text: str,
        original_sentences: List[Dict],
        progress_callback: Optional[callable] = None
    ) -> List[SentenceMappingResult]:
        """
        基于 embedding 相似度匹配

        Args:
            enhanced_text: 增强文本
            original_sentences: 原始句子列表

        Returns:
            List[SentenceMappingResult]

        Note:
            当前为占位实现，返回空结果触发降级
        """
        # TODO: 实现 embedding 相似度匹配
        # 需要依赖 embedding 服务，暂时返回空列表触发降级
        return []

    def _get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        获取文本的 embedding 向量

        Args:
            texts: 文本列表

        Returns:
            List[List[float]]: embedding 向量列表

        Note:
            占位实现，需要集成实际的 embedding 服务
        """
        # TODO: 集成 embedding 服务（OpenAI / 本地模型）
        raise NotImplementedError("Embedding 服务尚未集成")

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """计算余弦相似度"""
        # TODO: 实现余弦相似度计算
        pass


# ============================================================
# HybridMapper - 混合映射策略
# ============================================================

class HybridMapper(SentenceMapper):
    """混合映射策略：Exact → Embedding → Position"""

    def __init__(
        self,
        similarity_threshold: float = 0.7,
        match_rate_threshold: float = 0.6,
        strict_json: bool = False
    ):
        """
        初始化 HybridMapper

        Args:
            similarity_threshold: 相似度阈值
            match_rate_threshold: 匹配率阈值
            strict_json: 是否严格 JSON 模式
        """
        self.exact_mapper = ExactMapper(strict=strict_json)
        self.embedding_mapper = EmbeddingMapper(
            similarity_threshold=similarity_threshold,
            match_rate_threshold=match_rate_threshold
        )
        self.position_mapper = PositionMapper()

    def supports_method(self) -> MappingMethod:
        return MappingMethod.EXACT  # 主要方法

    def map(
        self,
        enhanced_text: str,
        original_sentences: List[Dict],
        progress_callback: Optional[callable] = None
    ) -> List[SentenceMappingResult]:
        """
        混合映射：按优先级尝试不同策略

        优先级:
        1. ExactMapper（精确匹配）
        2. EmbeddingMapper（相似度匹配）
        3. PositionMapper（位置回退）

        Args:
            enhanced_text: 增强文本
            original_sentences: 原始句子列表

        Returns:
            List[SentenceMappingResult]
        """
        if progress_callback:
            progress_callback("mapping_start", 0)

        # Step 1: 尝试精确匹配
        results = self.exact_mapper.map(enhanced_text, original_sentences)

        if results and len(results) == len(original_sentences):
            # 精确匹配成功
            if progress_callback:
                progress_callback("mapping_complete", 100)
            return results

        # Step 2: 尝试 embedding 匹配
        if progress_callback:
            progress_callback("embedding_mapping", 50)

        results = self.embedding_mapper.map(enhanced_text, original_sentences)

        if results and len(results) >= len(original_sentences) * self.embedding_mapper.match_rate_threshold:
            # embedding 匹配成功
            if progress_callback:
                progress_callback("mapping_complete", 100)
            return results

        # Step 3: 降级到位置映射
        if progress_callback:
            progress_callback("position_fallback", 80)

        results = self.position_mapper.map(enhanced_text, original_sentences)

        if progress_callback:
            progress_callback("mapping_complete", 100)

        return results


# ============================================================
# 便捷函数
# ============================================================

def create_mapper(
    strategy: str = "hybrid",
    **kwargs
) -> SentenceMapper:
    """
    创建 Mapper 实例

    Args:
        strategy: 映射策略 (exact/embedding/position/hybrid/simple)
        **kwargs: 策略特定参数

    Returns:
        SentenceMapper: 映射器实例
    """
    strategy = strategy.lower()

    if strategy == "exact":
        return ExactMapper(strict=kwargs.get("strict", False))
    elif strategy == "embedding":
        return EmbeddingMapper(
            similarity_threshold=kwargs.get("similarity_threshold", 0.7),
            match_rate_threshold=kwargs.get("match_rate_threshold", 0.6)
        )
    elif strategy == "position" or strategy == "simple":
        return PositionMapper()
    elif strategy == "hybrid":
        return HybridMapper(
            similarity_threshold=kwargs.get("similarity_threshold", 0.7),
            match_rate_threshold=kwargs.get("match_rate_threshold", 0.6),
            strict_json=kwargs.get("strict_json", False)
        )
    else:
        raise ValueError(f"未知的映射策略: {strategy}")
