"""
Enhanced Transcript Builder - 增强版转录文档构建模块

PR2 实现：
- 基于固定时间窗口的 chunk 划分（整数毫秒）
- sentence 跨 chunk 匹配
- 增强结果去重（基于 sentence_index）
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple, Set
from enum import Enum
import json
from pathlib import Path
from datetime import datetime


class TimeUnit(Enum):
    """时间单位"""
    MILLISECOND = 1
    SECOND = 1000
    MINUTE = 60000


@dataclass
class TimeWindow:
    """时间窗口（使用整数毫秒）"""
    start_ms: int
    end_ms: int

    def __post_init__(self):
        if self.start_ms < 0:
            raise ValueError(f"start_ms 不能为负数: {self.start_ms}")
        if self.end_ms <= self.start_ms:
            raise ValueError(f"end_ms 必须大于 start_ms: {self.end_ms} <= {self.start_ms}")

    @property
    def duration_ms(self) -> int:
        return self.end_ms - self.start_ms

    @property
    def duration_seconds(self) -> float:
        return self.duration_ms / TimeUnit.SECOND.value

    def overlaps_with(self, other: 'TimeWindow') -> bool:
        """判断是否与另一个时间窗口重叠"""
        return self.start_ms < other.end_ms and self.end_ms > other.start_ms

    def intersection_duration_ms(self, other: 'TimeWindow') -> int:
        """计算与另一个窗口的重叠时长（毫秒）"""
        if not self.overlaps_with(other):
            return 0
        return min(self.end_ms, other.end_ms) - max(self.start_ms, other.start_ms)

    def contains(self, other: 'TimeWindow') -> bool:
        """判断是否完全包含另一个窗口"""
        return self.start_ms <= other.start_ms and self.end_ms >= other.end_ms

    @classmethod
    def from_seconds(cls, start: float, end: float) -> 'TimeWindow':
        """从秒数创建（转换为整数毫秒）"""
        return cls(
            start_ms=int(start * TimeUnit.SECOND.value),
            end_ms=int(end * TimeUnit.SECOND.value)
        )

    def to_seconds_tuple(self) -> Tuple[float, float]:
        """转换为秒数元组"""
        return (self.start_ms / TimeUnit.SECOND.value, self.end_ms / TimeUnit.SECOND.value)


@dataclass
class Sentence:
    """句子（使用整数毫秒）"""
    sentence_index: int           # 唯一编号
    start_ms: int
    end_ms: int
    text: str

    def __post_init__(self):
        if self.sentence_index < 0:
            raise ValueError(f"sentence_index 不能为负数: {self.sentence_index}")
        if self.start_ms < 0:
            raise ValueError(f"start_ms 不能为负数: {self.start_ms}")
        if self.end_ms <= self.start_ms:
            raise ValueError(f"end_ms 必须大于 start_ms: {self.end_ms} <= {self.start_ms}")
        if not self.text:
            raise ValueError("text 不能为空")

    @property
    def duration_ms(self) -> int:
        return self.end_ms - self.start_ms

    @property
    def time_window(self) -> TimeWindow:
        return TimeWindow(self.start_ms, self.end_ms)

    def overlaps_with_chunk(self, chunk: TimeWindow) -> bool:
        """判断是否与 chunk 时间窗口有交集"""
        return self.start_ms < chunk.end_ms and self.end_ms > chunk.start_ms

    @classmethod
    def from_utterance(cls, index: int, utterance: Dict[str, Any]) -> 'Sentence':
        """从 utterance 创建（秒转毫秒）"""
        return cls(
            sentence_index=index,
            start_ms=int(utterance["start"] * TimeUnit.SECOND.value),
            end_ms=int(utterance["end"] * TimeUnit.SECOND.value),
            text=utterance["text"]
        )


@dataclass
class Chunk:
    """分块（使用整数毫秒）"""
    chunk_id: int
    time_window: TimeWindow
    sentence_indices: List[int] = field(default_factory=list)
    actual_overlap_ms_with_previous: int = 0
    actual_overlap_ms_with_next: int = 0

    @property
    def start_ms(self) -> int:
        return self.time_window.start_ms

    @property
    def end_ms(self) -> int:
        return self.time_window.end_ms

    @property
    def duration_ms(self) -> int:
        return self.time_window.duration_ms

    def add_sentence(self, sentence_index: int):
        """添加句子索引"""
        if sentence_index not in self.sentence_indices:
            self.sentence_indices.append(sentence_index)

    def get_matching_sentences(
        self,
        all_sentences: List[Sentence]
    ) -> List[Sentence]:
        """获取所有与当前 chunk 时间有交集的 sentence"""
        matching = []
        for sent in all_sentences:
            if sent.overlaps_with_chunk(self.time_window):
                matching.append(sent)
        return matching


@dataclass
class EnhancedSentence:
    """增强后的句子"""
    sentence_index: int
    start_ms: int
    end_ms: int
    original_text: str
    enhanced_text: str
    confidence: float = 1.0

    def __post_init__(self):
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"confidence 必须在 [0, 1] 范围内: {self.confidence}")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sentence_index": self.sentence_index,
            "start_ms": self.start_ms,
            "end_ms": self.end_ms,
            "original_text": self.original_text,
            "enhanced_text": self.enhanced_text,
            "confidence": self.confidence
        }


@dataclass
class EnhancedTranscriptConfig:
    """增强版转录配置"""
    enabled: bool = False
    chunk_window_seconds: float = 60.0
    chunk_overlap_seconds: float = 10.0
    max_drift_ms: int = 30000  # 最大漂移窗口（毫秒），默认 30 秒

    def __post_init__(self):
        if self.chunk_window_seconds <= 0:
            raise ValueError("chunk_window_seconds 必须 > 0")
        if self.chunk_overlap_seconds < 0:
            raise ValueError("chunk_overlap_seconds 必须 >= 0")
        if self.chunk_overlap_seconds >= self.chunk_window_seconds:
            raise ValueError("chunk_overlap_seconds 必须 < chunk_window_seconds")
        if self.max_drift_ms < 0:
            raise ValueError("max_drift_ms 必须 >= 0")

    @property
    def chunk_window_ms(self) -> int:
        """窗口大小（毫秒）"""
        return int(self.chunk_window_seconds * TimeUnit.SECOND.value)

    @property
    def chunk_overlap_ms(self) -> int:
        """重叠大小（毫秒）"""
        return int(self.chunk_overlap_seconds * TimeUnit.SECOND.value)

    @property
    def hard_max_duration_ms(self) -> int:
        """硬上限（毫秒）"""
        return int(self.chunk_window_seconds * TimeUnit.SECOND.value * 10)  # 10 倍窗口


@dataclass
class EnhancedTranscript:
    """增强版转录文档"""
    metadata: Dict[str, Any]
    sentences: List[EnhancedSentence]
    chunks: List[Chunk]

    @property
    def sentence_count(self) -> int:
        return len(self.sentences)

    @property
    def chunk_count(self) -> int:
        return len(self.chunks)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metadata": self.metadata,
            "sentences": [s.to_dict() for s in self.sentences],
            "chunks": [
                {
                    "chunk_id": c.chunk_id,
                    "start_ms": c.start_ms,
                    "end_ms": c.end_ms,
                    "sentence_indices": c.sentence_indices,
                    "actual_overlap_ms_with_previous": c.actual_overlap_ms_with_previous,
                    "actual_overlap_ms_with_next": c.actual_overlap_ms_with_next,
                }
                for c in self.chunks
            ]
        }

    def save(self, path: str) -> str:
        """保存到磁盘"""
        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)

        return str(output_path)


# ============================================================
# 验证函数（防御性编程）
# ============================================================

def validate_sentences(sentences: List[Sentence]) -> None:
    """
    验证 sentences 时间单调性

    Args:
        sentences: Sentence 列表

    Raises:
        ValueError: 如果时间不单调或有其他问题
    """
    epsilon_ms = 1  # 1 毫秒容差

    for i, sent in enumerate(sentences):
        # 验证基本约束
        if sent.start_ms < 0:
            raise ValueError(f"sentence[{i}].start_ms 不能为负数: {sent.start_ms}")
        if sent.end_ms <= sent.start_ms:
            raise ValueError(
                f"sentence[{i}].end_ms 必须大于 start_ms: "
                f"{sent.end_ms} <= {sent.start_ms}"
            )
        if not sent.text:
            raise ValueError(f"sentence[{i}].text 不能为空")

        # 验证单调性
        if i > 0:
            prev_sent = sentences[i - 1]
            if sent.start_ms < prev_sent.end_ms - epsilon_ms:
                raise ValueError(
                    f"sentence[{i}].start_ms 时间倒退: "
                    f"{sent.start_ms} < previous end_ms {prev_sent.end_ms}"
                )


def validate_chunk_progression(chunks: List[Chunk]) -> None:
    """
    验证 chunk 连续性（内部调试用）

    检查：
    - chunk_id 严格递增
    - time_window.start_ms 单调递增
    - 无时间倒退
    - overlap 区间合理

    Args:
        chunks: Chunk 列表

    Raises:
        AssertionError: 如果连续性有问题
    """
    if not chunks:
        return

    # 验证 chunk_id 严格递增
    for i in range(len(chunks)):
        assert chunks[i].chunk_id == i, f"chunk_id 不连续: expected {i}, got {chunks[i].chunk_id}"

    # 验证时间单调递增
    for i in range(1, len(chunks)):
        prev_chunk = chunks[i - 1]
        curr_chunk = chunks[i]

        assert curr_chunk.start_ms >= prev_chunk.start_ms, \
            f"chunk[{i}].start_ms 时间倒退: {curr_chunk.start_ms} < {prev_chunk.start_ms}"

        # 验证 overlap 不为负数
        assert curr_chunk.actual_overlap_ms_with_previous >= 0, \
            f"chunk[{i}].actual_overlap_ms_with_previous 为负数: {curr_chunk.actual_overlap_ms_with_previous}"

        # 如果声明有 overlap，验证实际时间有交集
        if curr_chunk.actual_overlap_ms_with_previous > 0:
            expected_overlap = prev_chunk.time_window.intersection_duration_ms(curr_chunk.time_window)
            # 允许 1ms 误差
            assert abs(curr_chunk.actual_overlap_ms_with_previous - expected_overlap) <= 1, \
                f"chunk[{i}] 声明的 overlap 与计算不符: " \
                f"declared={curr_chunk.actual_overlap_ms_with_previous}, expected={expected_overlap}"


# ============================================================
# 核心函数
# ============================================================

def build_fixed_chunks(
    total_duration_ms: int,
    window_seconds: float = 60.0,
    overlap_seconds: float = 10.0
) -> List[TimeWindow]:
    """
    构建固定窗口的时间分块（含 overlap）

    Args:
        total_duration_ms: 总时长（毫秒）
        window_seconds: 窗口大小（秒）
        overlap_seconds: 重叠大小（秒）

    Returns:
        TimeWindow 列表

    Example:
        >>> build_fixed_chunks(180000, 60, 10)  # 3分钟音频
        [TimeWindow(0, 60000), TimeWindow(50000, 110000), TimeWindow(100000, 160000), TimeWindow(150000, 180000)]
    """
    if total_duration_ms <= 0:
        return []

    window_ms = int(window_seconds * TimeUnit.SECOND.value)
    overlap_ms = int(overlap_seconds * TimeUnit.SECOND.value)
    step_ms = window_ms - overlap_ms

    if step_ms <= 0:
        raise ValueError(f"窗口大小必须大于重叠: {window_seconds}s > {overlap_seconds}s")

    chunks = []
    current_start_ms = 0
    chunk_id = 0

    while current_start_ms < total_duration_ms:
        current_end_ms = min(current_start_ms + window_ms, total_duration_ms)

        # 最后一个窗口如果太小，合并到前一个
        if current_end_ms - current_start_ms < step_ms / 2:
            if chunks:
                # 扩展前一个窗口的结束时间
                last_chunk = chunks[-1]
                chunks[-1] = TimeWindow(last_chunk.start_ms, current_end_ms)
            break

        chunks.append(TimeWindow(current_start_ms, current_end_ms))

        # 移动到下一个窗口
        current_start_ms += step_ms
        chunk_id += 1

    return chunks


def build_chunks_with_overlap(
    total_duration_ms: int,
    config: EnhancedTranscriptConfig
) -> List[Chunk]:
    """
    构建带 overlap 信息的 chunk 列表

    Args:
        total_duration_ms: 总时长（毫秒）
        config: 增强配置

    Returns:
        Chunk 列表，包含 actual_overlap_ms_* 信息
    """
    # 构建时间窗口
    time_windows = build_fixed_chunks(
        total_duration_ms=total_duration_ms,
        window_seconds=config.chunk_window_seconds,
        overlap_seconds=config.chunk_overlap_seconds
    )

    if not time_windows:
        return []

    # 转换为 Chunk 并计算 overlap
    chunks = []
    for chunk_id, time_window in enumerate(time_windows):
        chunk = Chunk(chunk_id=chunk_id, time_window=time_window)

        # 计算与上一个 chunk 的 overlap
        if chunks:
            prev_chunk = chunks[-1]
            overlap_ms = time_window.intersection_duration_ms(prev_chunk.time_window)
            chunk.actual_overlap_ms_with_previous = overlap_ms
            prev_chunk.actual_overlap_ms_with_next = overlap_ms

        chunks.append(chunk)

    return chunks


def match_sentences_to_chunks(
    sentences: List[Sentence],
    chunks: List[TimeWindow]
) -> List[Chunk]:
    """
    将 sentences 匹配到 chunks（允许跨 chunk）

    Args:
        sentences: Sentence 列表
        chunks: TimeWindow 列表

    Returns:
        Chunk 列表，每个 chunk 包含匹配的 sentence_indices
    """
    result = []

    for chunk_id, time_window in enumerate(chunks):
        chunk = Chunk(chunk_id=chunk_id, time_window=time_window)

        for sentence in sentences:
            if sentence.overlaps_with_chunk(time_window):
                chunk.add_sentence(sentence.sentence_index)

        result.append(chunk)

    return result


@dataclass
class EnhancementProcessor:
    """增强处理器（PR2 占位，PR3-5 实现 LLM 调用）"""

    def process_chunk(
        self,
        chunk: Chunk,
        sentences: List[Sentence],
        progress_callback: Optional[callable] = None
    ) -> Dict[int, EnhancedSentence]:
        """
        处理单个 chunk，返回增强结果

        PR2: 占位实现，直接返回原文
        PR3-5: 将实现 LLM 调用

        Args:
            chunk: 当前 chunk
            sentences: 所有 sentences
            progress_callback: 进度回调

        Returns:
            Dict[sentence_index, EnhancedSentence]
        """
        # PR2 占位：直接返回原文作为"增强"结果
        results = {}

        matching_sentences = chunk.get_matching_sentences(sentences)

        for sent in matching_sentences:
            results[sent.sentence_index] = EnhancedSentence(
                sentence_index=sent.sentence_index,
                start_ms=sent.start_ms,
                end_ms=sent.end_ms,
                original_text=sent.text,
                enhanced_text=sent.text,  # PR2: 使用原文
                confidence=1.0
            )

        if progress_callback:
            progress_callback(f"processed_chunk_{chunk.chunk_id}", len(results))

        return results


def build_enhanced_transcript(
    utterances: List[Dict[str, Any]],
    config: EnhancedTranscriptConfig,
    source_transcript_path: Optional[str] = None,
    progress_callback: Optional[callable] = None
) -> EnhancedTranscript:
    """
    构建增强版转录文档

    Args:
        utterances: utterance 列表，每个包含 {start, end, text}
        config: 增强配置
        source_transcript_path: 源 transcript 路径
        progress_callback: 进度回调

    Returns:
        EnhancedTranscript 实例
    """
    # 1. 转换为 Sentence（使用整数毫秒）
    sentences = [
        Sentence.from_utterance(i, utt)
        for i, utt in enumerate(utterances)
    ]

    if not sentences:
        return EnhancedTranscript(
            metadata={"error": "No sentences provided"},
            sentences=[],
            chunks=[]
        )

    # 2. 验证时间单调性（防御性编程）
    validate_sentences(sentences)

    # 3. 计算总时长
    total_duration_ms = sentences[-1].end_ms

    # 4. 构建 chunks（带 overlap 信息）
    chunks_with_overlap = build_chunks_with_overlap(total_duration_ms, config)

    # 5. 将 sentences 匹配到 chunks
    chunks_with_matches = []
    for chunk in chunks_with_overlap:
        # 复制 chunk 结构，添加 sentence_indices
        chunk_with_matches = Chunk(
            chunk_id=chunk.chunk_id,
            time_window=chunk.time_window,
            actual_overlap_ms_with_previous=chunk.actual_overlap_ms_with_previous,
            actual_overlap_ms_with_next=chunk.actual_overlap_ms_with_next
        )

        for sentence in sentences:
            if sentence.overlaps_with_chunk(chunk.time_window):
                chunk_with_matches.add_sentence(sentence.sentence_index)

        chunks_with_matches.append(chunk_with_matches)

    # 6. 调试模式：验证 chunk 连续性
    if __debug__:
        validate_chunk_progression(chunks_with_matches)

    if progress_callback:
        progress_callback("chunks_matched", len(chunks_with_matches))

    # 7. 处理每个 chunk 并收集增强结果
    #    添加死循环保护（最多处理 10000 个 chunk）
    processor = EnhancementProcessor()
    enhanced_results: Dict[int, EnhancedSentence] = {}

    MAX_CHUNKS = 10000
    for i, chunk in enumerate(chunks_with_matches):
        if i >= MAX_CHUNKS:
            raise RuntimeError(f"chunk 数量超过安全限制 ({MAX_CHUNKS})，可能存在死循环")

        chunk_results = processor.process_chunk(chunk, sentences, progress_callback)

        # 去重：按 sentence_index 合并
        # 策略：保留第一次匹配的结果（简单方案）
        for sent_idx, enhanced_sent in chunk_results.items():
            if sent_idx not in enhanced_results:
                enhanced_results[sent_idx] = enhanced_sent
            # 已存在则跳过（保留第一次）

    if progress_callback:
        progress_callback("enhancement_complete", len(enhanced_results))

    # 8. 构建最终结果
    # 按 sentence_index 排序
    sorted_sentences = sorted(
        enhanced_results.values(),
        key=lambda s: s.sentence_index
    )

    enhanced_transcript = EnhancedTranscript(
        metadata={
            "source_transcript_path": source_transcript_path,
            "total_duration_ms": total_duration_ms,
            "sentence_count": len(sorted_sentences),
            "chunk_count": len(chunks_with_matches),
            "chunk_window_seconds": config.chunk_window_seconds,
            "chunk_overlap_seconds": config.chunk_overlap_seconds,
            "created_at": datetime.now().isoformat()
        },
        sentences=sorted_sentences,
        chunks=chunks_with_matches
    )

    return enhanced_transcript


# ============================================================
# 便捷函数
# ============================================================

def create_sentences_from_utterances(utterances: List[Dict[str, Any]]) -> List[Sentence]:
    """从 utterances 创建 Sentence 列表"""
    return [
        Sentence.from_utterance(i, utt)
        for i, utt in enumerate(utterances)
    ]


def chunk_transcript_by_time(
    utterances: List[Dict[str, Any]],
    window_seconds: float = 60.0,
    overlap_seconds: float = 10.0
) -> List[Dict[str, Any]]:
    """
    便捷函数：按时间窗口分块 transcript

    Args:
        utterances: utterance 列表
        window_seconds: 窗口大小
        overlap_seconds: 重叠大小

    Returns:
        分块信息列表
    """
    sentences = create_sentences_from_utterances(utterances)

    if not sentences:
        return []

    total_duration_ms = sentences[-1].end_ms

    # 使用新的 build_chunks_with_overlap
    config = EnhancedTranscriptConfig(
        chunk_window_seconds=window_seconds,
        chunk_overlap_seconds=overlap_seconds
    )
    chunks = build_chunks_with_overlap(total_duration_ms, config)

    # 匹配 sentences
    chunks_with_matches = []
    for chunk in chunks:
        chunk_with_matches = Chunk(
            chunk_id=chunk.chunk_id,
            time_window=chunk.time_window,
            actual_overlap_ms_with_previous=chunk.actual_overlap_ms_with_previous,
            actual_overlap_ms_with_next=chunk.actual_overlap_ms_with_next
        )

        for sentence in sentences:
            if sentence.overlaps_with_chunk(chunk.time_window):
                chunk_with_matches.add_sentence(sentence.sentence_index)

        chunks_with_matches.append(chunk_with_matches)

    return [
        {
            "chunk_id": c.chunk_id,
            "start_ms": c.start_ms,
            "end_ms": c.end_ms,
            "start_seconds": c.start_ms / 1000,
            "end_seconds": c.end_ms / 1000,
            "sentence_indices": c.sentence_indices,
            "sentence_count": len(c.sentence_indices),
            "actual_overlap_ms_with_previous": c.actual_overlap_ms_with_previous,
            "actual_overlap_ms_with_next": c.actual_overlap_ms_with_next,
        }
        for c in chunks_with_matches
    ]
