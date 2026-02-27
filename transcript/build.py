"""
Transcript building - 从 ASR 结果生成原始会议文档
"""

from typing import Optional
from pathlib import Path

from asr.types import TranscriptionResult
from transcript.types import TranscriptDocument


def build_transcript(
    asr_result: TranscriptionResult,
    save: bool = True,
    output_path: Optional[str] = None,
    *,
    enable_enhanced: bool = False,
    enhanced_config: Optional = None
) -> TranscriptDocument:
    """
    从 ASR 转写结果构建原始会议文档

    Args:
        asr_result: ASR 转写结果
        save: 是否保存到磁盘（默认 True）
        output_path: 输出文件路径（可选，默认自动生成）
        enable_enhanced: 是否启用增强版处理（默认 False）
        enhanced_config: 增强版配置（可选，默认使用 60s 窗口 + 10s overlap）

    Returns:
        TranscriptDocument 实例

    Raises:
        ValueError: 如果 asr_result 无效
    """
    # 验证 ASR 结果
    if not isinstance(asr_result, TranscriptionResult):
        raise ValueError(
            f"asr_result 必须是 TranscriptionResult 类型，"
            f"实际类型: {type(asr_result)}"
        )

    # 构建 utterance 列表（从 TranscriptionResult 转换）
    utterances = []
    for utt in asr_result.utterances:
        utterances.append({
            "start": utt.start,
            "end": utt.end,
            "text": utt.text
        })

    # 创建文档，记录源 ASR 工件路径以保持可追溯性
    document = TranscriptDocument(
        utterances=utterances,
        audio_path=asr_result.audio_path,
        duration=asr_result.duration,
        asr_provider=asr_result.asr_provider,
        source_transcript_path=asr_result.transcript_path
    )

    # 保存到磁盘
    if save:
        document.save(output_path)

    # PR2: enhanced 处理（如果启用）
    if enable_enhanced:
        # 导入 enhanced_builder（避免循环依赖）
        from transcript.enhanced_builder import build_enhanced_transcript, EnhancedTranscriptConfig

        # 使用提供的配置或默认配置
        if enhanced_config is None:
            enhanced_config = EnhancedTranscriptConfig(
                enabled=True,
                chunk_window_seconds=60.0,
                chunk_overlap_seconds=10.0
            )

        # 构建 enhanced transcript
        utterances_list = [
            {"start": utt.start, "end": utt.end, "text": utt.text}
            for utt in asr_result.utterances
        ]

        enhanced = build_enhanced_transcript(
            utterances=utterances_list,
            config=enhanced_config,
            source_transcript_path=asr_result.transcript_path
        )

        # 保存 enhanced 文档
        enhanced_path = None
        if document.document_path:
            doc_path = Path(document.document_path)
            enhanced_filename = doc_path.stem + "_enhanced" + doc_path.suffix
            enhanced_path = str(doc_path.parent / enhanced_filename)
            enhanced_path = enhanced.save(enhanced_path)

        # 更新 asr_result 的 enhanced_transcript_path（如果可以）
        # 注意：TranscriptionResult 是不可变数据类，这里仅记录
        if hasattr(asr_result, 'enhanced_transcript_path'):
            object.__setattr__(asr_result, 'enhanced_transcript_path', enhanced_path)

    return document


def format_timestamp(seconds: float) -> str:
    """
    格式化时间戳为人类可读格式

    Args:
        seconds: 时间（秒）

    Returns:
        格式化的时间字符串 [MM:SS]
    """
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"[{minutes:02d}:{secs:02d}]"


def group_utterances_into_paragraphs(
    utterances: list,
    max_gap: float = 3.0
) -> list:
    """
    将语音片段分组为段落

    Args:
        utterances: 语音片段列表
        max_gap: 最大间隔时间（秒），超过此间隔则分段

    Returns:
        段落列表，每个段落包含多个 utterance
    """
    if not utterances:
        return []

    paragraphs = []
    current_paragraph = [utterances[0]]

    for i in range(1, len(utterances)):
        prev_end = utterances[i - 1]["end"]
        curr_start = utterances[i]["start"]
        gap = curr_start - prev_end

        if gap <= max_gap:
            # 连续发言，加入当前段落
            current_paragraph.append(utterances[i])
        else:
            # 间隔过大，开始新段落
            paragraphs.append(current_paragraph)
            current_paragraph = [utterances[i]]

    # 添加最后一个段落
    if current_paragraph:
        paragraphs.append(current_paragraph)

    return paragraphs


def get_transcript_stats(document: TranscriptDocument) -> dict:
    """
    获取文档统计信息

    Args:
        document: TranscriptDocument 实例

    Returns:
        统计信息字典
    """
    total_words = sum(
        len(u["text"].split())
        for u in document.utterances
    )

    # 计算平均语速（字/分钟）
    if document.duration > 0:
        words_per_minute = (total_words / document.duration) * 60
    else:
        words_per_minute = 0

    # 计算有效发言时间（去掉静音）
    speaking_time = sum(
        u["end"] - u["start"]
        for u in document.utterances
    )

    # 计算发言占比
    if document.duration > 0:
        speaking_ratio = speaking_time / document.duration
    else:
        speaking_ratio = 0

    return {
        "total_utterances": document.utterance_count,
        "total_words": total_words,
        "duration_seconds": document.duration,
        "duration_formatted": format_timestamp(document.duration),
        "speaking_time_seconds": speaking_time,
        "speaking_time_formatted": format_timestamp(speaking_time),
        "words_per_minute": round(words_per_minute, 1),
        "speaking_ratio": round(speaking_ratio * 100, 1),
        "asr_provider": document.asr_provider
    }
