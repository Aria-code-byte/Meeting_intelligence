"""
WhisperX Transcription Service
============================
WhisperX + pyannote.audio 说话人分离转录服务

功能：
- 使用 WhisperX 进行高精度语音识别
- 支持词级时间戳对齐
- 使用 pyannote.audio 进行说话人分离
- 生成结构化的对话轮次（turns）
- 阶段 10B-5-Q：音频预处理和质量诊断

环境变量配置：
- WHISPERX_MODEL: 模型名称（默认: large-v3-turbo）
- WHISPERX_LANGUAGE: 语言代码（默认: zh）
- WHISPERX_DEVICE: 设备类型（默认: auto）
- WHISPERX_COMPUTE_TYPE: 计算类型（默认: 空，自动选择）
- WHISPERX_BATCH_SIZE: 批处理大小（默认: 16）
- WHISPERX_SKIP_ALIGN: 是否跳过对齐（默认: false）
- DIARIZATION_ENABLED: 是否启用说话人分离（默认: true）
- PYANNOTE_DIARIZE_MODEL: pyannote 模型（默认: pyannote/speaker-diarization-community-1）
- HF_TOKEN: Hugging Face token（pyannote 需要）
- HUGGINGFACE_TOKEN: HF_TOKEN 别名
- DIARIZATION_MERGE_GAP: 合并间隔秒数（默认: 1.0）
- DIARIZATION_MIN_SPEAKERS: 最少说话人数（默认: 1）
- DIARIZATION_MAX_SPEAKERS: 最多说话人数（默认: 4）
"""

import os
import sys
import re
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import time
import subprocess
import tempfile
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 环境变量读取
def _get_env(key: str, default: Any = None) -> Any:
    """安全读取环境变量"""
    value = os.getenv(key, default)
    if value is None or value == "":
        return default
    # 布尔值转换
    if isinstance(default, bool):
        return str(value).lower() in ("true", "1", "yes", "on")
    # 整数转换
    if isinstance(default, int):
        try:
            return int(value)
        except ValueError:
            return default
    return value


# ============================================================
# 环境变量配置（带默认值）
# ============================================================

WHISPERX_MODEL = _get_env("WHISPERX_MODEL", "large-v3-turbo")
WHISPERX_LANGUAGE = _get_env("WHISPERX_LANGUAGE", "zh")
WHISPERX_DEVICE = _get_env("WHISPERX_DEVICE", "auto")
WHISPERX_COMPUTE_TYPE = _get_env("WHISPERX_COMPUTE_TYPE", None)
WHISPERX_BATCH_SIZE = _get_env("WHISPERX_BATCH_SIZE", 16)
WHISPERX_SKIP_ALIGN = _get_env("WHISPERX_SKIP_ALIGN", False)
# 阶段 10B-5-Q5：新增 initial_prompt 支持（默认禁用，避免兼容性问题）
WHISPER_INITIAL_PROMPT = _get_env("WHISPER_INITIAL_PROMPT", "")
WHISPER_INITIAL_PROMPT_ENABLED = _get_env("WHISPER_INITIAL_PROMPT_ENABLED", "false").lower() in ("true", "1", "yes")

# Diarization 配置
DIARIZATION_ENABLED = _get_env("DIARIZATION_ENABLED", True)
PYANNOTE_DIARIZE_MODEL = _get_env("PYANNOTE_DIARIZE_MODEL", "pyannote/speaker-diarization-community-1")
HF_TOKEN = _get_env("HF_TOKEN") or _get_env("HUGGINGFACE_TOKEN")
DIARIZATION_MERGE_GAP = _get_env("DIARIZATION_MERGE_GAP", 1.0)
# 阶段 10B-5-Q：新增说话人数量配置
DIARIZATION_MIN_SPEAKERS = _get_env("DIARIZATION_MIN_SPEAKERS", 1)
DIARIZATION_MAX_SPEAKERS = _get_env("DIARIZATION_MAX_SPEAKERS", 4)
# 阶段 10B-5-Q4：最小 turn 配置
MIN_TURN_CHARS = _get_env("MIN_TURN_CHARS", 4)  # 最小 turn 字符数
MIN_TURN_DURATION = _get_env("MIN_TURN_DURATION", 0.4)  # 最小 turn 时长（秒）
SHORT_TURN_MERGE_STRATEGY = _get_env("SHORT_TURN_MERGE_STRATEGY", "merge_to_gap")  # 短 turn 合并策略


# ============================================================
# 阶段 10B-5-Q4：短 turn 合并与噪声过滤函数
# ============================================================

def merge_short_turns(
    turns: List[Dict[str, Any]],
    stats: Dict[str, int]
) -> List[Dict[str, Any]]:
    """
    合并过短的 turns，避免词语被切断

    策略：
    1. 检测过短 turn（字符数 < MIN_TURN_CHARS 或时长 < MIN_TURN_DURATION）
    2. 尝试合并到相邻 turn
    3. 优先合并到同 speaker turn
    4. 如果前后 speaker 不同，合并到 gap 更小的一侧

    Args:
        turns: 原始 turns
        stats: 统计信息字典（会被修改）

    Returns:
        合并后的 turns
    """
    if not turns:
        return turns

    merged_turns = []
    i = 0
    stats["short_turn_merged"] = 0

    while i < len(turns):
        current_turn = turns[i]
        current_text = current_turn.get("text", "")
        current_duration = (current_turn.get("end", 0) - current_turn.get("start", 0))
        current_speaker = current_turn.get("speaker", "UNKNOWN")

        # 检查是否为过短 turn
        is_short = (
            len(current_text) < MIN_TURN_CHARS or
            current_duration < MIN_TURN_DURATION
        )

        if not is_short:
            # 正常长度 turn，直接添加
            merged_turns.append(current_turn)
            i += 1
            continue

        # 尝试合并过短 turn
        merged = False

        # 策略 1: 尝试合并到前一个 turn（同 speaker）
        if merged_turns and not merged:
            prev_turn = merged_turns[-1]
            prev_speaker = prev_turn.get("speaker", "UNKNOWN")
            gap_to_prev = current_turn.get("start", 0) - prev_turn.get("end", 0)

            if prev_speaker == current_speaker and gap_to_prev < 1.0:
                # 合并到前一个 turn
                prev_turn["text"] += current_text
                prev_turn["end"] = current_turn.get("end", prev_turn["end"])
                stats["short_turn_merged"] += 1
                merged = True

        # 策略 2: 尝试合并到后一个 turn（同 speaker）
        if not merged and i + 1 < len(turns):
            next_turn = turns[i + 1]
            next_speaker = next_turn.get("speaker", "UNKNOWN")
            gap_to_next = next_turn.get("start", 0) - current_turn.get("end", 0)

            if next_speaker == current_speaker and gap_to_next < 1.0:
                # 合并到后一个 turn（需要修改后一个 turn）
                next_turn["text"] = current_text + next_turn["text"]
                next_turn["start"] = current_turn.get("start", next_turn["start"])
                stats["short_turn_merged"] += 1
                merged = True

        # 策略 3: 如果无法合并，但非常短，合并到 gap 更小的一侧
        if not merged and len(current_text) <= 2:
            if merged_turns:
                gap_to_prev = current_turn.get("start", 0) - merged_turns[-1].get("end", 0)
                if i + 1 < len(turns):
                    gap_to_next = turns[i + 1].get("start", 0) - current_turn.get("end", 0)

                    if gap_to_prev < gap_to_next:
                        # 合并到前一个
                        merged_turns[-1]["text"] += current_text
                        merged_turns[-1]["end"] = current_turn.get("end", merged_turns[-1]["end"])
                        stats["short_turn_merged"] += 1
                        merged = True
                    elif gap_to_next < gap_to_prev:
                        # 合并到后一个
                        turns[i + 1]["text"] = current_text + turns[i + 1]["text"]
                        turns[i + 1]["start"] = current_turn.get("start", turns[i + 1]["start"])
                        stats["short_turn_merged"] += 1
                        merged = True

        # 如果仍然无法合并，保留但输出警告
        if not merged:
            preview = current_text[:20] + "..." if len(current_text) > 20 else current_text
            print(f"[WhisperX] warning: 无法合并短 turn (speaker={current_speaker}, text='{preview}')")
            merged_turns.append(current_turn)

        i += 1

    return merged_turns


def dedupe_repeated_phrases(text: str) -> str:
    """
    压缩连续重复的短语或词

    例如：
    "阳和。阳和。阳和。" -> "阳和。"
    "好的。好的。" -> "好的。"

    Args:
        text: 原始文本

    Returns:
        压缩后的文本
    """
    if not text:
        return text

    compressed_count = 0

    # 检测连续重复的短句（以标点结尾）
    # 匹配模式：短句 + 标点 + 重复3次以上
    pattern = r'([^\s。！？；：、]{1,8}[。！？；：、])\1{2,}'

    def replace_repeated(match):
        nonlocal compressed_count
        repeated_phrase = match.group(1)
        compressed_count += 1
        return repeated_phrase  # 只保留一次

    result = re.sub(pattern, replace_repeated, text)

    if compressed_count > 0:
        print(f"[WhisperX] 压缩了 {compressed_count} 个重复短语")

    return result


def is_transcript_polluted(text: str) -> bool:
    """
    检测transcript是否被污染

    阶段 10B-5-Q5：质量检测，避免使用污染的transcript

    污染特征：
    1. 包含 [?] artifact
    2. 包含  replacement character
    3. 中文逐字空格比例过高
    4. 异常符号比例过高

    Args:
        text: 待检测的文本

    Returns:
        bool: 是否被污染
    """
    if not text:
        return False

    # 1. 检测 [?] artifact
    if '[?]' in text or '[？]' in text:
        print("[WhisperX] ⚠️ 检测到 [?] artifact")
        return True

    # 2. 检测 replacement character
    if '' in text:
        print("[WhisperX] ⚠️ 检测到 replacement character")
        return True

    # 3. 检测中文逐字空格模式
    # 计算中文字符之间的空格数量
    cjk_chars = len(re.findall(r'[一-鿿]', text))
    spaces = text.count(' ')
    if cjk_chars > 10:  # 至少10个中文字符才检测
        space_ratio = spaces / cjk_chars
        if space_ratio > 0.5:  # 空格数量超过中文字符的50%
            print(f"[WhisperX] ⚠️ 检测到中文逐字空格模式 (space_ratio={space_ratio:.2f})")
            return True

    # 4. 检测异常符号比例
    # 计算 [、]、{、}、<、> 等异常符号的数量
    abnormal_chars = len(re.findall(r'[\[\]{}<>]', text))
    if len(text) > 20:  # 至少20个字符才检测
        abnormal_ratio = abnormal_chars / len(text)
        if abnormal_ratio > 0.1:  # 异常符号超过10%
            print(f"[WhisperX] ⚠️ 检测到高比例异常符号 (abnormal_ratio={abnormal_ratio:.2f})")
            return True

    return False


def clean_replacement_chars(text: str) -> str:
    """
    清理 Unicode replacement character 和其他 alignment artifacts

    阶段 10B-5-Q5：增强清理，确保移除所有污染字符

    Args:
        text: 原始文本

    Returns:
        清理后的文本
    """
    if not text:
        return text

    original_length = len(text)
    artifacts_found = {}

    # 检测和移除各种 artifacts
    # 1. Unicode replacement character
    replacement_count = text.count('')
    if replacement_count > 0:
        artifacts_found['replacement_char'] = replacement_count
        text = text.replace('', '')

    # 2. 阶段 10B-5-Q5：明确移除 [?] artifact
    question_artifact_count = text.count('[?]')
    if question_artifact_count > 0:
        artifacts_found['question_artifact'] = question_artifact_count
        text = text.replace('[?]', '')

    # 3. 移除其他常见 artifacts
    # 移除孤立的 [?] 标记（可能有空格变体）
    text = re.sub(r'\[\?\]', '', text)
    # 移除孤立的 [？] 标记（中文问号）
    text = re.sub(r'\[？\]', '', text)

    # 4. 移除异常的Unicode字符
    text = text.replace('', '')  # Replacement character
    text = text.replace('', '')  # Object replacement character

    if artifacts_found:
        total_artifacts = sum(artifacts_found.values())
        print(f"[WhisperX] 清理了 {total_artifacts} 个 artifacts: {artifacts_found}")
        print(f"[WhisperX]   - 文本长度从 {original_length} 减少到 {len(text)}")

    return text


# ============================================================
# 阶段 10B-5-Q3：智能 token 拼接与空格清理函数
# ============================================================

def cleanup_cjk_spacing(text: str) -> str:
    """
    清理 CJK（中日韩）文本中的多余空格

    阶段 10B-5-Q5：增强处理，确保所有中文字符之间无空格

    规则：
    1. 中文字符之间的空格（包括所有CJK范围）
    2. 中文字符与标点之间的空格
    3. 标点与中文字符之间的空格
    4. 英文标点转换为中文标点
    5. 防止逐字空格问题（"要 是 外 人"）

    Args:
        text: 原始文本

    Returns:
        清理后的文本
    """
    if not text:
        return ""

    original_length = len(text)

    # 1. 去除中文字符之间的空格（扩展CJK字符范围）
    # CJK 统一表意文字范围：U+4E00–U+9FFF
    # CJK 扩展-A：U+3400–U+4DBF
    # CJK 扩展-B：U+20000–U+2A6DF
    # CJK 扩展-C：U+2A700–U+2B73F
    # CJK 扩展-D：U+2B740–U+2B81F
    # CJK 扩展-E：U+2B820–U+2CEAF
    # CJK 扩展-F：U+2CEB0–U+2EBEF
    # CJK 兼容：U+F900–U+FAFF
    # 此外还包括常见的中文标点

    # 构建CJK字符类（包括常见中文标点）
    cjk_pattern = r'[一-鿿㐀-䶿豈-﫿　-〿＀-￯，。！？；：、""''（）【】《》]'

    # 去除CJK字符之间的空格
    text = re.sub(f'(?<={cjk_pattern})\\s+(?={cjk_pattern})', '', text)

    # 2. 去除中文与标点之间的空格（两侧）
    # 包括中文和英文标点
    punctuation_chars = "，。！？；：、,.!?;:\"'\'"
    text = re.sub(rf'\s+([{punctuation_chars}])', r'\1', text)
    text = re.sub(rf'([{punctuation_chars}])\s+', r'\1', text)

    # 3. 英文标点转换为中文标点（在中文上下文中）
    # 仅当标点前后有中文字符时转换
    text = re.sub(r'(?<=[一-鿿]),(?=[一-鿿])', '，', text)
    text = re.sub(r'(?<=[一-鿿])\.(?=[一-鿿])', '。', text)
    text = re.sub(r'(?<=[一-鿿])!(?=[一-鿿])', '！', text)
    text = re.sub(r'(?<=[一-鿿])\?(?=[一-鿿])', '？', text)
    text = re.sub(r'(?<=[一-鿿]):(?=[一-鿿])', '：', text)
    text = re.sub(r'(?<=[一-鿿]);(?=[一-鿿])', '；', text)

    # 4. 阶段 10B-5-Q5：特别处理逐字空格问题
    # 如果发现模式如"X Y Z"（都是单个中文字符），合并它们
    # 检测连续的单字+空格模式
    single_char_space_pattern = r'([一-鿿])\s+([一-鿿])'
    if re.search(single_char_space_pattern, text):
        print(f"[WhisperX] ⚠️ 检测到逐字空格模式，正在清理...")
        # 递归清理直到没有逐字空格
        while re.search(single_char_space_pattern, text):
            text = re.sub(single_char_space_pattern, r'\1\2', text)

    # 5. 去除多余空格（但保留英文单词之间的空格）
    text = re.sub(r'\s+', ' ', text)

    cleaned_length = len(text)
    if original_length != cleaned_length:
        print(f"[WhisperX] CJK空格清理：长度从 {original_length} 减少到 {cleaned_length}")

    return text.strip()


def join_tokens_smart(tokens: List[str], language: str = "zh") -> str:
    """
    智能拼接 token，根据语言选择合适的拼接方式

    Args:
        tokens: token 列表
        language: 语言代码（zh/en/ja 等）

    Returns:
        拼接后的文本
    """
    if not tokens:
        return ""

    # 清理每个 token 的首尾空格
    tokens = [t.strip() for t in tokens if t.strip()]

    if not tokens:
        return ""

    # 对于中文，直接拼接（不用空格）
    if language == "zh":
        # 先尝试直接拼接
        text = "".join(tokens)

        # 然后清理空格（处理可能存在的英文单词）
        text = cleanup_cjk_spacing(text)

        return text

    # 对于英文等语言，用空格拼接
    return " ".join(tokens)


# ============================================================
# 阶段 10B-5-Q2：中文可读性后处理函数
# ============================================================

def postprocess_chinese_text(text: str, max_length: int = 80) -> str:
    """
    后处理中文文本，提升可读性

    阶段 10B-5-Q4：优化断句策略，减少激进分割

    策略：
    1. 先清理 CJK 空格（重要！）
    2. 对过长文本进行保守断句
    3. 不改变原始内容
    4. 不通过空格提升可读性
    5. 主要靠断句、换行和保守标点

    Args:
        text: 原始文本
        max_length: 单句最大字符数（默认 80，阶段 10B-5-Q4 从 50 提高）

    Returns:
        处理后的文本
    """
    if not text:
        return ""

    # 先清理空格（不再 early return）
    text = cleanup_cjk_spacing(text)

    # 如果文本长度适中，直接返回
    if len(text) <= max_length:
        return text

    # 阶段 10B-5-Q4：对过长文本进行更保守的断句
    # 优先按强标点分割（。！？）
    segments = re.split(r'([。！？])', text)

    # 重建句子，保持标点
    rebuilt = []
    current = ""

    for i, seg in enumerate(segments):
        if seg in "。！？":
            current += seg
            # 句末标点，结束当前句
            rebuilt.append(current)
            current = ""
        else:
            current += seg

    # 添加剩余部分
    if current:
        rebuilt.append(current)

    # 阶段 10B-5-Q4：如果没有强标点，检查是否需要按长度分割
    # 只有当文本特别长时（> 150 字符）才进行长度分割
    if not rebuilt and len(text) > 150:
        # 按弱标点分割（；，）
        weak_segments = re.split(r'([；，])', text)

        weak_rebuilt = []
        weak_current = ""

        for seg in weak_segments:
            if seg in "；，":
                weak_current += seg
                # 弱标点也作为分割点
                weak_rebuilt.append(weak_current)
                weak_current = ""
            else:
                weak_current += seg

        if weak_current:
            weak_rebuilt.append(weak_current)

        if weak_rebuilt:
            rebuilt = weak_rebuilt

    # 如果仍然没有合适的分割点，且文本超长，按字符数分割
    if not rebuilt and len(text) > max_length:
        # 按字符数分割（最后手段）
        segments = []
        for i in range(0, len(text), max_length):
            segments.append(text[i:i + max_length])
        rebuilt = segments

    # 用换行连接各段
    result = "\n".join(rebuilt)

    return result


def normalize_turns_text(turns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    标准化 turns 的文本，提升可读性

    阶段 10B-5-Q5-R：修复污染处理逻辑，先清理再检测

    Args:
        turns: 原始 turns

    Returns:
        标准化后的 turns
    """
    normalized_turns = []
    stats = {
        "total_turns": len(turns),
        "long_turns": 0,
        "modified_turns": 0,
        "polluted_turns": 0,     # 检测到污染的 turn
        "cleaned_turns": 0,      # 清理后恢复正常的 turn
        "skipped_turns": 0,      # 跳过的 turn
    }

    for turn in turns:
        speaker = turn.get("speaker", "UNKNOWN")
        start = turn.get("start", 0)
        end = turn.get("end", 0)
        text = turn.get("text", "")

        if not text:
            continue

        # 阶段 10B-5-Q5-R：先清理异常字符，再检测污染
        original_text = text
        text = clean_replacement_chars(text)

        # 阶段 10B-5-Q4：压缩重复短语
        text = dedupe_repeated_phrases(text)

        # 检测是否仍然污染
        if is_transcript_polluted(text):
            stats["polluted_turns"] += 1
            print(f"[WhisperX] ⚠️ turn text清理后仍然污染，尝试 fallback")

            # 阶段 10B-5-Q5-R：fallback 到原始文本，再清理一次
            text = clean_replacement_chars(original_text)
            text = dedupe_repeated_phrases(text)

            # 如果仍然污染，跳过该 turn
            if is_transcript_polluted(text):
                stats["skipped_turns"] += 1
                print(f"[WhisperX] ⚠️ turn text无法恢复，跳过该turn (speaker={speaker}, preview={text[:30]})")
                continue
            else:
                stats["cleaned_turns"] += 1

        # 阶段 10B-5-Q4：长turn阈值提高到80字符
        is_long = len(text) > 80

        # 后处理文本
        processed_text = postprocess_chinese_text(text)

        # 统计
        if is_long:
            stats["long_turns"] += 1
        if processed_text != text:
            stats["modified_turns"] += 1

        # 警告过长 turn
        if is_long:
            preview = text[:30] + "..." if len(text) > 30 else text
            print(f"[WhisperX] warning: long turn detected (length={len(text)}), preview: {preview}")

        normalized_turns.append({
            "speaker": speaker,
            "start": start,
            "end": end,
            "text": processed_text
        })

    print(f"[WhisperX] normalize_turns_text 统计:")
    print(f"[WhisperX]   - 总 turns: {stats['total_turns']}")
    print(f"[WhisperX]   - 长 turns (>80字符): {stats['long_turns']}")
    print(f"[WhisperX]   - 修改的 turns: {stats['modified_turns']}")
    print(f"[WhisperX]   - 污染 turns: {stats['polluted_turns']}")
    print(f"[WhisperX]   - 跳过 turns: {stats['skipped_turns']}")

    # 阶段 10B-5-Q5-R3：Fallback 逻辑
    # 如果所有 turns 都被跳过，但原始 turns 不为空，使用原始 turns
    if not normalized_turns and turns and stats['skipped_turns'] > 0:
        print(f"[WhisperX] ⚠️ 所有 turns 都被跳过，使用原始 turns 作为 fallback")
        # 使用原始 turns，只做基础清理
        for turn in turns:
            text = turn.get("text", "")
            if not text:
                continue
            # 只做基础清理，不检测污染
            text = clean_replacement_chars(text)
            normalized_turns.append({
                "speaker": turn.get("speaker", "UNKNOWN"),
                "start": turn.get("start", 0),
                "end": turn.get("end", 0),
                "text": text
            })
        print(f"[WhisperX] Fallback 后恢复了 {len(normalized_turns)} 个 turns")

    return normalized_turns


# ============================================================
# 阶段 10B-5-Q：音频预处理函数
# ============================================================

def preprocess_audio_with_ffmpeg(
    input_path: str,
    output_dir: Optional[str] = None
) -> Tuple[str, Dict[str, Any]]:
    """
    使用 ffmpeg 预处理音频文件

    转换为适合 WhisperX 的格式：
    - 单声道 (mono)
    - 16kHz 采样率
    - WAV 格式

    Args:
        input_path: 输入音频文件路径
        output_dir: 输出目录（可选，默认使用系统临时目录）

    Returns:
        (output_path, audio_info) 元组
        - output_path: 预处理后的音频文件路径
        - audio_info: 音频信息字典

    Raises:
        FileNotFoundError: 输入文件不存在
        RuntimeError: ffmpeg 处理失败
    """
    input_path_obj = Path(input_path)
    if not input_path_obj.exists():
        raise FileNotFoundError(f"输入文件不存在: {input_path}")

    # 创建输出文件路径
    if output_dir is None:
        output_dir = tempfile.gettempdir()

    output_path = Path(output_dir) / f"{input_path_obj.stem}_processed.wav"

    # 构建 ffmpeg 命令
    # -vn: 禁用视频
    # -ac 1: 单声道
    # -ar 16000: 16kHz 采样率
    # -y: 覆盖输出文件
    cmd = [
        "ffmpeg",
        "-i", str(input_path),
        "-vn",  # 禁用视频
        "-ac", "1",  # 单声道
        "-ar", "16000",  # 16kHz
        "-acodec", "pcm_s16le",  # PCM 16-bit little-endian
        "-y",  # 覆盖输出文件
        str(output_path)
    ]

    print(f"[WhisperX] 开始音频预处理...")
    print(f"[WhisperX] 输入: {input_path}")
    print(f"[WhisperX] 输出: {output_path}")

    try:
        # 执行 ffmpeg 命令
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5分钟超时
        )

        if result.returncode != 0:
            raise RuntimeError(f"ffmpeg 处理失败: {result.stderr}")

        # 获取音频信息
        audio_info = get_audio_info(str(output_path))
        print(f"[WhisperX] 音频预处理成功")
        print(f"[WhisperX] 格式: {audio_info.get('format')}, 采样率: {audio_info.get('sample_rate')}, 声道: {audio_info.get('channels')}, 时长: {audio_info.get('duration')}s")

        return str(output_path), audio_info

    except subprocess.TimeoutExpired:
        raise RuntimeError("ffmpeg 处理超时（5分钟）")
    except FileNotFoundError:
        raise RuntimeError("ffmpeg 未安装，请先安装 ffmpeg")


def get_audio_info(file_path: str) -> Dict[str, Any]:
    """
    获取音频文件信息

    Args:
        file_path: 音频文件路径

    Returns:
        音频信息字典
    """
    try:
        # 使用 ffprobe 获取音频信息
        cmd = [
            "ffprobe",
            "-v", "quiet",
            "-show_entries",
            "format=duration,format_name",
            "-show_entries",
            "stream=codec_type,channels,sample_rate",
            "-of",
            "json",
            file_path
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode != 0:
            return {}

        import json
        info = json.loads(result.stdout)

        # 提取关键信息
        format_info = info.get("format", {})
        streams = info.get("streams", [])

        # 找到音频流
        audio_stream = None
        for stream in streams:
            if stream.get("codec_type") == "audio":
                audio_stream = stream
                break

        return {
            "duration": float(format_info.get("duration", 0)),
            "format": format_info.get("format_name", "unknown"),
            "sample_rate": int(audio_stream.get("sample_rate", 0)) if audio_stream else 0,
            "channels": int(audio_stream.get("channels", 0)) if audio_stream else 0,
        }

    except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError, KeyError, ValueError):
        return {}


# ============================================================
# 辅助函数
# ============================================================

def clean_text(text: str) -> str:
    """
    清理文本内容

    Args:
        text: 原始文本

    Returns:
        清理后的文本
    """
    if not text:
        return ""

    # 移除多余空格
    text = " ".join(text.split())

    # 移除首尾空格
    text = text.strip()

    return text


def join_words(words: List[Dict[str, Any]], separator: str = " ") -> str:
    """
    将词列表拼接为文本

    Args:
        words: 词列表，每个词包含 "word" 字段
        separator: 分隔符

    Returns:
        拼接后的文本
    """
    if not words:
        return ""

    return separator.join(w.get("word", "") for w in words)


def speaker_for_segment(words: List[Dict[str, Any]]) -> Optional[str]:
    """
    确定片段的主要说话人

    Args:
        words: 词列表，每个词包含 "speaker" 字段

    Returns:
        出现次数最多的说话人标签
    """
    if not words:
        return None

    # 统计每个说话人的词数
    speaker_counts: Dict[str, int] = {}
    for word in words:
        speaker = word.get("speaker")
        if speaker:
            speaker_counts[speaker] = speaker_counts.get(speaker, 0) + 1

    if not speaker_counts:
        return None

    # 返回词数最多的说话人
    return max(speaker_counts.items(), key=lambda x: x[1])[0]


def add_turn(turns: List[Dict[str, Any]], speaker: str, start: float, end: float, text: str) -> None:
    """
    添加一个对话轮次

    如果与前一个轮次的说话人相同且间隔较小，则合并

    Args:
        turns: 轮次列表（会被修改）
        speaker: 说话人标签
        start: 开始时间（秒）
        end: 结束时间（秒）
        text: 文本内容
    """
    if not text.strip():
        return

    text = clean_text(text)

    # 类型安全：确保 start 和 end 是数字
    try:
        start_num = float(start) if start is not None else 0.0
        end_num = float(end) if end is not None else 0.0
    except (ValueError, TypeError):
        # 如果转换失败，使用默认值
        start_num = 0.0
        end_num = 0.0

    # 检查是否可以合并到上一个轮次
    if turns:
        last_turn = turns[-1]
        try:
            last_end = float(last_turn.get("end", 0))
            gap = start_num - last_end

            # 同一说话人且间隔较小，合并
            if (last_turn.get("speaker") == speaker and
                gap <= DIARIZATION_MERGE_GAP):
                last_turn["end"] = end_num
                last_turn["text"] += " " + text
                return
        except (ValueError, TypeError):
            # 如果计算 gap 失败，不合并，直接添加新轮次
            pass

    # 添加新轮次
    turns.append({
        "speaker": speaker,
        "start": round(start_num, 2),
        "end": round(end_num, 2),
        "text": text
    })


def build_turns(
    segments: List[Dict[str, Any]],
    diarization_enabled: bool = True,
    language: str = "zh"  # 阶段 10B-5-Q3：新增 language 参数
) -> List[Dict[str, Any]]:
    """
    从片段构建对话轮次

    阶段 10B-5-Q5：优化文本来源策略，优先使用segment.text

    文本来源优先级：
    1. segment.text：WhisperX转录的高质量文本（首选）
    2. word-level text：仅用于speaker边界判断，不作为最终文本来源

    Speaker边界判断：
    1. 如果 segment.words 中有 word-level speaker：按 word.speaker 切分
    2. 如果没有 word-level speaker：使用 segment.speaker 或多数原则 fallback
    3. 完全没有 speaker 信息：使用 UNKNOWN 或 SPEAKER

    Args:
        segments: WhisperX 片段列表
        diarization_enabled: 是否启用了说话人分离
        language: 语言代码（用于智能 token 拼接）

    Returns:
        对话轮次列表
    """
    turns: List[Dict[str, Any]] = []

    # 阶段 10B-5-Q2：统计信息
    stats = {
        "split_by_speaker_change": 0,
        "split_by_gap": 0,
        "words_processed": 0,
        "unknown_speaker": 0,
        "segment_text_used": 0,  # 阶段 10B-5-Q5：新增统计
        "word_text_used": 0,      # 阶段 10B-5-Q5：新增统计
    }

    if not segments:
        return turns

    for segment in segments:
        start = segment.get("start", 0)
        end = segment.get("end", 0)
        segment_text = segment.get("text", "")
        words = segment.get("words", [])

        if not segment_text.strip():
            continue

        if diarization_enabled:
            # 检查是否有 word-level speaker
            has_word_speaker = any(
                w.get("speaker") for w in words if isinstance(w, dict)
            )

            if has_word_speaker:
                # 阶段 10B-5-Q5-R：恢复正确的 word-level 文本重建
                # Q5 错误地把 segment.text 复制到每个子 turn，现在修复
                current_speaker = None
                current_words = []
                current_start = None
                last_word_end = None

                for word in words:
                    word_speaker = word.get("speaker")
                    word_text = word.get("word", "")
                    word_start = word.get("start")
                    word_end = word.get("end")

                    if not word_text:
                        continue

                    stats["words_processed"] += 1

                    # 首次初始化
                    if current_speaker is None:
                        current_speaker = word_speaker or "UNKNOWN"
                        if current_speaker == "UNKNOWN":
                            stats["unknown_speaker"] += 1
                        current_words = [word_text]
                        current_start = word_start if word_start is not None else start
                        last_word_end = word_end if word_end is not None else current_start
                        continue

                    # 计算与上一个词的 gap
                    gap = None
                    if last_word_end is not None and word_start is not None:
                        gap = word_start - last_word_end

                    # 阶段 10B-5-Q2：检测 speaker 变化或长 gap
                    speaker_changed = word_speaker and word_speaker != current_speaker
                    long_gap = gap and gap > 0.8  # 0.8秒 gap 切分

                    if speaker_changed or long_gap:
                        # speaker 变化或长 gap，结束当前 turn
                        if current_words:
                            # 阶段 10B-5-Q5-R：使用 word-level 重建文本
                            turn_text = join_tokens_smart(current_words, language)
                            turn_end = last_word_end if last_word_end else current_start

                            if speaker_changed:
                                stats["split_by_speaker_change"] += 1
                            elif long_gap:
                                stats["split_by_gap"] += 1

                            add_turn(turns, current_speaker, current_start, turn_end, turn_text)
                            stats["word_text_used"] += 1

                        # 开始新 turn
                        current_speaker = word_speaker or "UNKNOWN"
                        if current_speaker == "UNKNOWN":
                            stats["unknown_speaker"] += 1
                        current_words = [word_text]
                        current_start = word_start if word_start is not None else start
                        last_word_end = word_end if word_end is not None else current_start
                    else:
                        # 同一 speaker 且 gap 较短，累加词
                        current_words.append(word_text)
                        last_word_end = word_end if word_end is not None else last_word_end

                # 处理最后一个 turn
                if current_words:
                    # 阶段 10B-5-Q5-R：使用 word-level 重建文本
                    turn_text = join_tokens_smart(current_words, language)
                    turn_end = end
                    add_turn(turns, current_speaker or "UNKNOWN", current_start, turn_end, turn_text)
                    stats["word_text_used"] += 1

            else:
                # 优先级 2: 没有 word-level speaker，使用 segment.text
                segment_speaker = segment.get("speaker")
                if segment_speaker:
                    add_turn(turns, segment_speaker, start, end, segment_text)
                    stats["segment_text_used"] += 1
                else:
                    # 优先级 3: 使用多数原则 fallback
                    fallback_speaker = speaker_for_segment(words)
                    if fallback_speaker:
                        add_turn(turns, fallback_speaker, start, end, segment_text)
                    else:
                        # 完全没有 speaker 信息
                        add_turn(turns, "UNKNOWN", start, end, segment_text)
                        stats["unknown_speaker"] += 1
        else:
            # 没有说话人分离，使用 "SPEAKER"
            add_turn(turns, "SPEAKER", start, end, segment_text)

    # 阶段 10B-5-Q4：合并过短的 turns
    turns = merge_short_turns(turns, stats)

    # 阶段 10B-5-Q2：输出统计信息
    print(f"[WhisperX] build_turns 统计:")
    print(f"[WhisperX]   - speaker change 切分: {stats['split_by_speaker_change']}")
    print(f"[WhisperX]   - gap 切分: {stats['split_by_gap']}")
    print(f"[WhisperX]   - 处理词数: {stats['words_processed']}")
    print(f"[WhisperX]   - 未知说话人: {stats['unknown_speaker']}")
    print(f"[WhisperX]   - 短 turn 合并: {stats.get('short_turn_merged', 0)}")

    return turns


# ============================================================
# 主要转录函数
# ============================================================

def transcribe_with_whisperx(
    audio_path: str,
    model: Optional[str] = None,
    language: Optional[str] = None,
    device: Optional[str] = None,
    compute_type: Optional[str] = None,
    batch_size: Optional[int] = None,
    skip_align: Optional[bool] = None,
    diarization_enabled: Optional[bool] = None,
    hf_token: Optional[str] = None,
    initial_prompt: Optional[str] = None  # 阶段 10B-5-Q5：新增 initial_prompt
) -> Dict[str, Any]:
    """
    使用 WhisperX + pyannote 进行转录和说话人分离

    Args:
        audio_path: 音频文件路径
        model: WhisperX 模型名称（覆盖环境变量）
        language: 语言代码（覆盖环境变量）
        device: 设备类型（覆盖环境变量）
        compute_type: 计算类型（覆盖环境变量）
        batch_size: 批处理大小（覆盖环境变量）
        skip_align: 是否跳过对齐（覆盖环境变量）
        diarization_enabled: 是否启用说话人分离（覆盖环境变量）
        hf_token: Hugging Face token（覆盖环境变量）

    Returns:
        转录结果字典：
        {
            "text": "完整文字稿",
            "language": "zh",
            "provider": "whisperx",
            "model": "large-v3-turbo",
            "segments": [],
            "turns": [...],
            "diarizationEnabled": true,
            "diarizationProvider": "pyannote",
            "diarizationModel": "pyannote/speaker-diarization-community-1",
            "alignmentStatus": "success",  # "success" | "skipped" | "failed"
            "alignmentError": null,  # 失败时的错误信息
            "raw": {}
        }

    Raises:
        FileNotFoundError: 音频文件不存在
        ImportError: WhisperX 或 pyannote 未安装
        RuntimeError: 转录过程出错
        ValueError: 无效的参数
    """
    start_time = time.time()
    stage_times = {}  # 阶段 10B-5-Q3：阶段耗时统计

    # ============================================================
    # 参数准备（使用传入值或环境变量默认值）
    # ============================================================

    model = model or WHISPERX_MODEL
    language = language or WHISPERX_LANGUAGE
    device = device or WHISPERX_DEVICE
    batch_size = batch_size if batch_size is not None else WHISPERX_BATCH_SIZE
    skip_align = skip_align if skip_align is not None else WHISPERX_SKIP_ALIGN
    diarization_enabled = diarization_enabled if diarization_enabled is not None else DIARIZATION_ENABLED
    hf_token = hf_token or HF_TOKEN
    # 阶段 10B-5-Q5：新增 initial_prompt 参数（默认禁用，避免兼容性问题）
    use_initial_prompt = WHISPER_INITIAL_PROMPT_ENABLED and bool(WHISPER_INITIAL_PROMPT)
    initial_prompt = initial_prompt if initial_prompt is not None else (WHISPER_INITIAL_PROMPT if use_initial_prompt else None)

    # ============================================================
    # 设备解析：将 "auto" 转换为具体设备
    # ============================================================

    # WhisperX 不接受 "auto"，需要显式指定
    resolved_device = device
    if device == "auto":
        try:
            import torch
            resolved_device = "cuda" if torch.cuda.is_available() else "cpu"
            print(f"[WhisperX] 设备自动检测: {resolved_device}")
        except ImportError:
            # PyTorch 不可用时默认 CPU
            resolved_device = "cpu"
            print(f"[WhisperX] PyTorch 不可用，使用 CPU")

    # 显式解析 compute_type（根据解析后的设备）
    if compute_type is None or compute_type == "":
        # 根据 resolved_device 自动选择
        if resolved_device == "cuda":
            compute_type = "float16"
        else:
            compute_type = "int8"
        print(f"[WhisperX] 计算类型自动选择: {compute_type}")

    # ============================================================
    # 参数验证
    # ============================================================

    audio_path_obj = Path(audio_path)
    if not audio_path_obj.exists():
        raise FileNotFoundError(f"音频文件不存在: {audio_path}")

    if not audio_path_obj.is_file():
        raise ValueError(f"路径不是文件: {audio_path}")

    # 检查文件扩展名
    valid_extensions = {".wav", ".mp3", ".mp4", ".m4a", ".flac", ".ogg", ".webm"}
    if audio_path_obj.suffix.lower() not in valid_extensions:
        raise ValueError(f"不支持的音频格式: {audio_path_obj.suffix}")

    # 阶段 10B-5-Q5-R2：Diarization 降级处理
    # 如果没有 HF token，自动禁用 diarization 而不是失败
    if diarization_enabled and not hf_token:
        print("[WhisperX] ⚠️ HF token not found, diarization will be skipped")
        print("[WhisperX] ⚠️ Falling back to normal transcription without speaker separation")
        diarization_enabled = False  # 自动降级为普通转录
        # 不要抛出错误，让转录继续进行

    # ============================================================
    # 阶段 10B-5-Q：音频预处理
    # ============================================================

    original_audio_path = audio_path
    audio_info = {}

    try:
        # 尝试使用 ffmpeg 预处理音频
        processed_audio_path, audio_info = preprocess_audio_with_ffmpeg(audio_path)
        audio_path = processed_audio_path
        print(f"[WhisperX] 使用预处理后的音频: {audio_path}")
    except (FileNotFoundError, RuntimeError) as e:
        # 预处理失败，使用原始音频
        print(f"[WhisperX] 音频预处理失败，使用原始音频: {e}")
        audio_path = original_audio_path
        # 尝试获取原始音频信息
        audio_info = get_audio_info(original_audio_path)

    # ============================================================
    # 阶段 10B-5-Q：打印配置信息
    # ============================================================

    print(f"[WhisperX] 开始转录...")
    print(f"[WhisperX] 音频: {original_audio_path}")
    print(f"[WhisperX] 模型: {model}")
    print(f"[WhisperX] 语言: {language}")
    print(f"[WhisperX] 设备: {device} (解析为: {resolved_device})")
    print(f"[WhisperX] 计算类型: {compute_type}")
    print(f"[WhisperX] 批处理大小: {batch_size}")
    print(f"[WhisperX] 跳过对齐: {skip_align}")
    print(f"[WhisperX] 说话人分离: {diarization_enabled}")
    if diarization_enabled:
        print(f"[WhisperX] 最少说话人: {DIARIZATION_MIN_SPEAKERS}")
        print(f"[WhisperX] 最多说话人: {DIARIZATION_MAX_SPEAKERS}")
    print(f"[WhisperX] 音频信息: 时长={audio_info.get('duration', 0):.1f}s, 采样率={audio_info.get('sample_rate', 0)}, 声道={audio_info.get('channels', 0)}")

    # ============================================================
    # 动态导入 WhisperX
    # ============================================================

    try:
        import whisperx
        print(f"[WhisperX] whisperx 版本: {whisperx.__version__ if hasattr(whisperx, '__version__') else 'unknown'}")
    except ImportError as e:
        raise ImportError(
            f"WhisperX 未安装: {e}\n"
            f"请运行: pip install whisperx>=3.1.0"
        )

    # ============================================================
    # 加载音频
    # ============================================================

    try:
        stage_start = time.time()
        print(f"[WhisperX] 加载音频...")
        audio = whisperx.load_audio(audio_path)
        stage_times["audio_load"] = time.time() - stage_start
        print(f"[WhisperX] 音频加载成功，shape: {audio.shape}, 耗时: {stage_times['audio_load']:.2f}s")
    except Exception as e:
        raise RuntimeError(f"音频加载失败: {e}")

    # ============================================================
    # 加载 WhisperX 模型并转录
    # ============================================================

    try:
        stage_start = time.time()
        print(f"[WhisperX] 加载模型...")
        whisper_model = whisperx.load_model(
            model,
            resolved_device,  # 使用解析后的设备
            compute_type=compute_type,
            language=language
        )
        model_load_time = time.time() - stage_start
        print(f"[WhisperX] 模型加载成功，耗时: {model_load_time:.2f}s")

        stage_start = time.time()
        print(f"[WhisperX] 开始转录...")
        # 阶段 10B-5-Q5：initial_prompt 兼容性处理
        if initial_prompt and use_initial_prompt:
            print(f"[WhisperX] 尝试使用 initial_prompt (长度: {len(initial_prompt)} 字符)")
        else:
            print(f"[WhisperX] 未使用 initial_prompt (默认)")

        # 构建基础转录参数
        transcribe_params = {
            "audio": audio,
            "batch_size": batch_size,
            "language": language
        }

        # 阶段 10B-5-Q5：只在启用且有initial_prompt时才添加该参数
        if use_initial_prompt and initial_prompt:
            transcribe_params["initial_prompt"] = initial_prompt

        try:
            result = whisper_model.transcribe(**transcribe_params)
        except TypeError as e:
            if "initial_prompt" in str(e) and use_initial_prompt:
                print(f"[WhisperX] ⚠️ initial_prompt 不兼容，自动重试不使用 initial_prompt: {e}")
                # 移除 initial_prompt 参数后重试
                transcribe_params.pop("initial_prompt", None)
                result = whisper_model.transcribe(**transcribe_params)
            else:
                raise

        stage_times["transcribe"] = time.time() - stage_start
        print(f"[WhisperX] 转录完成，片段数: {len(result.get('segments', []))}, 耗时: {stage_times['transcribe']:.2f}s")

        # 保存检测到的语言
        detected_language = result.get("language", language)

        # 释放模型内存
        del whisper_model

    except Exception as e:
        raise RuntimeError(f"WhisperX 转录失败: {e}")

    # ============================================================
    # 词级对齐
    # ============================================================

    alignment_status = "skipped"  # 默认值
    alignment_error = None

    if not skip_align:
        try:
            stage_start = time.time()
            print(f"[WhisperX] 开始词级对齐...")
            model_a, metadata = whisperx.load_align_model(
                language_code=detected_language,
                device=resolved_device  # 使用解析后的设备
            )

            result = whisperx.align(
                result["segments"],
                model_a,
                metadata,
                audio,
                resolved_device,  # 使用解析后的设备
            )
            stage_times["align"] = time.time() - stage_start
            alignment_status = "success"
            print(f"[WhisperX] 对齐完成，耗时: {stage_times['align']:.2f}s")

            # 释放对齐模型内存
            del model_a

        except Exception as e:
            stage_times["align"] = time.time() - stage_start
            alignment_status = "failed"
            alignment_error = str(e)
            print(f"[WhisperX] 对齐失败: {e}")
            print(f"[WhisperX] 继续使用原始转录结果...")
    else:
        print(f"[WhisperX] 跳过词级对齐")
        stage_times["align"] = 0

    # ============================================================
    # 说话人分离
    # ============================================================

    # 阶段 10B-5-Q5-R2：Diarization 降级处理
    diarization_error = None
    diarization_success = False

    if diarization_enabled:
        try:
            stage_start = time.time()
            print(f"[WhisperX] 开始说话人分离...")
            print(f"[WhisperX] 模型: {PYANNOTE_DIARIZE_MODEL}")

            # 导入 pyannote
            try:
                from whisperx.diarize import DiarizationPipeline, assign_word_speakers
            except ImportError as e:
                raise ImportError(
                    f"pyannote.audio 未安装: {e}\n"
                    f"请运行: pip install pyannote.audio>=3.1.0"
                )

            # 创建说话人分离管道
            # DiarizationPipeline 参数：model_name, token, device, cache_dir
            diarize_model = DiarizationPipeline(
                model_name=PYANNOTE_DIARIZE_MODEL,
                token=hf_token,
                device=resolved_device  # 使用解析后的设备
            )

            # 执行说话人分离
            # 阶段 10B-5-Q：使用配置的说话人数量范围
            diarize_segments = diarize_model(
                audio,
                min_speakers=DIARIZATION_MIN_SPEAKERS,
                max_speakers=DIARIZATION_MAX_SPEAKERS
            )

            # 将说话人标签分配给词
            # 参数：diarize_df, transcript_result, speaker_embeddings=None, fill_nearest=False
            result = assign_word_speakers(
                diarize_segments,
                result
            )

            stage_times["diarization"] = time.time() - stage_start
            print(f"[WhisperX] 说话人分离完成，耗时: {stage_times['diarization']:.2f}s")
            diarization_success = True

            # 释放说话人分离模型内存
            del diarize_model

        except ImportError as e:
            # 阶段 10B-5-Q5-R2：pyannote 未安装，降级为普通转录
            stage_times["diarization"] = time.time() - stage_start
            diarization_error = f"pyannote.audio 未安装: {str(e)}"
            print(f"[WhisperX] ⚠️ 说话人分离失败，降级为普通转录: {diarization_error}")
            diarization_enabled = False  # 降级为普通转录
            diarization_success = False

        except Exception as e:
            # 阶段 10B-5-Q5-R2：其他 diarization 错误，也降级为普通转录
            stage_times["diarization"] = time.time() - stage_start
            diarization_error = f"说话人分离失败: {str(e)}"
            print(f"[WhisperX] ⚠️ 说话人分离失败，降级为普通转录: {diarization_error}")
            diarization_enabled = False  # 降级为普通转录
            diarization_success = False

    # 如果 diarization 完全失败，确保继续转录
    if not diarization_success and diarization_enabled:
        print(f"[WhisperX] ℹ️ 说话人分离未成功，将继续进行普通转录")
        diarization_enabled = False

    # ============================================================
    # 构建结果
    # ============================================================

    segments = result.get("segments", [])

    # 构建对话轮次（阶段 10B-5-Q3：传入 language 参数）
    raw_turns = build_turns(segments, diarization_enabled, detected_language or "zh")

    # 阶段 10B-5-Q2：标准化文本（提升可读性）
    turns = normalize_turns_text(raw_turns)

    # 阶段 10B-5-Q5-R4：优先使用 raw segments 构建主 transcript
    # 质量诊断日志：对比三路文本来源
    raw_segment_text = "\n".join(
        clean_replacement_chars((s.get("text") or "").strip())
        for s in segments
        if (s.get("text") or "").strip()
    )

    turns_text = "\n".join(
        clean_replacement_chars((t.get("text") or "").strip())
        for t in turns
        if (t.get("text") or "").strip()
    )

    # 决定最终 transcript 来源
    transcript_source = "empty"

    # 优先级 1: raw segments（Whisper 原始输出，质量最高）
    if raw_segment_text.strip():
        full_text = raw_segment_text.strip()
        transcript_source = "raw_segments"
    # 优先级 2: normalized turns（只在没有 raw segments 时使用）
    elif turns_text.strip():
        full_text = turns_text.strip()
        transcript_source = "normalized_turns"
    else:
        full_text = ""
        transcript_source = "empty"

    # 阶段 10B-5-Q5-R4：质量诊断日志
    print(f"[WhisperX] 10B-5-Q5-R4 质量诊断:")
    print(f"[WhisperX]   transcriptSource: {transcript_source}")
    print(f"[WhisperX]   rawSegmentTextLength: {len(raw_segment_text)} preview: {raw_segment_text[:200]}")
    print(f"[WhisperX]   turnsTextLength: {len(turns_text)} preview: {turns_text[:200]}")
    print(f"[WhisperX]   finalTranscriptLength: {len(full_text)} preview: {full_text[:200]}")

    # 阶段 10B-5-Q2：保留原始文本用于调试（仅用于展示，不用于 summary）
    raw_text = "\n".join(
        f"[{turn['speaker']}] {turn['text']}"
        for turn in raw_turns
    )

    # 阶段 10B-5-Q2：保留原始文本用于调试
    raw_text = "\n".join(
        f"[{turn['speaker']}] {turn['text']}"
        for turn in raw_turns
    )

    processing_time = time.time() - start_time

    # 阶段 10B-5-Q3：阶段耗时日志
    print(f"[WhisperX] 阶段耗时统计:")
    print(f"[WhisperX]   - 音频加载: {stage_times.get('audio_load', 0):.2f}s")
    print(f"[WhisperX]   - 模型加载: {stage_times.get('model_load', 0):.2f}s")
    print(f"[WhisperX]   - 转录: {stage_times.get('transcribe', 0):.2f}s")
    print(f"[WhisperX]   - 对齐: {stage_times.get('align', 0):.2f}s")
    print(f"[WhisperX]   - 说话人分离: {stage_times.get('diarization', 0):.2f}s")
    print(f"[WhisperX]   - 总耗时: {processing_time:.2f}s")
    print(f"[WhisperX]   - 音频时长: {audio_info.get('duration', 0):.1f}s")
    if audio_info.get('duration', 0) > 0:
        rtf = processing_time / audio_info.get('duration', 1)
        print(f"[WhisperX]   - RTF (实时率): {rtf:.2f}x")
    print(f"[WhisperX]   - 模型: {model}")
    print(f"[WhisperX]   - 设备: {resolved_device}")
    print(f"[WhisperX]   - 计算类型: {compute_type}")
    print(f"[WhisperX]   - 批处理大小: {batch_size}")

    # 阶段 10B-5-Q2：详细质量诊断日志
    print(f"[WhisperX] 质量诊断:")

    # 统计说话人分布
    speaker_stats: Dict[str, int] = {}
    turn_lengths = []
    for turn in turns:
        speaker = turn.get("speaker", "UNKNOWN")
        speaker_stats[speaker] = speaker_stats.get(speaker, 0) + 1
        turn_lengths.append(len(turn.get("text", "")))

    # 计算 turn 长度统计
    avg_turn_length = sum(turn_lengths) / len(turn_lengths) if turn_lengths else 0
    max_turn_length = max(turn_lengths) if turn_lengths else 0

    # 统计 words 数量
    total_words = sum(len(seg.get("words", [])) for seg in segments)

    print(f"[WhisperX]   - segments数量: {len(segments)}")
    print(f"[WhisperX]   - words数量: {total_words}")
    print(f"[WhisperX]   - turns数量: {len(turns)}")
    print(f"[WhisperX]   - raw transcript长度: {len(raw_text)} 字符")
    print(f"[WhisperX]   - normalized transcript长度: {len(full_text)} 字符")
    print(f"[WhisperX]   - 检测语言: {detected_language}")
    print(f"[WhisperX]   - 说话人数量: {len(speaker_stats)}")
    print(f"[WhisperX]   - 说话人分布: {speaker_stats}")
    print(f"[WhisperX]   - 平均 turn 长度: {avg_turn_length:.1f} 字符")
    print(f"[WhisperX]   - 最大 turn 长度: {max_turn_length} 字符")
    print(f"[WhisperX]   - 对齐状态: {alignment_status}")
    if alignment_error:
        print(f"[WhisperX]   - 对齐错误: {alignment_error}")

    # 阶段 10B-5-Q5：新增质量对比日志
    print(f"[WhisperX] 质量对比:")

    # raw vs normalized transcript 对比
    raw_preview = raw_text[:120] if raw_text else ""
    normalized_preview = full_text[:120] if full_text else ""
    print(f"[WhisperX]   - raw transcript preview (前120字): {raw_preview}")
    print(f"[WhisperX]   - normalized transcript preview (前120字): {normalized_preview}")

    # transcript vs turns 长度对比
    segments_text_length = sum(len(seg.get("text", "")) for seg in segments)
    turns_text_length = sum(len(turn.get("text", "")) for turn in turns)
    length_diff = abs(segments_text_length - turns_text_length)
    print(f"[WhisperX]   - segments text 总长度: {segments_text_length} 字符")
    print(f"[WhisperX]   - turns text 总长度: {turns_text_length} 字符")
    print(f"[WhisperX]   - 长度差异: {length_diff} 字符 ({length_diff / segments_text_length * 100:.1f}% )")

    if length_diff > segments_text_length * 0.1:  # 如果差异超过10%
        print(f"[WhisperX]   - ⚠️  警告：segments 和 turns 文本长度差异过大，可能存在丢词或重复词")

    return {
        "text": full_text,  # 标准化后的文本
        "rawText": raw_text,  # 原始文本（10B-5-Q2 新增）
        "language": detected_language,
        "provider": "whisperx",
        "model": model,
        "segments": segments,
        "turns": turns,
        "rawTurns": raw_turns,  # 原始 turns（10B-5-Q2 新增）
        "diarizationEnabled": diarization_enabled,
        "diarizationProvider": "pyannote" if diarization_enabled else None,
        "diarizationModel": PYANNOTE_DIARIZE_MODEL if diarization_enabled else None,
        "diarizationError": diarization_error,  # 阶段 10B-5-Q5-R2：新增 diarization 错误信息
        "alignmentStatus": alignment_status,
        "alignmentError": alignment_error,
        "raw": {
            "processingTimeSeconds": round(processing_time, 2),
            "audioPath": str(audio_path_obj),
            "languageDetected": detected_language,
            "segmentsCount": len(segments),
            "wordsCount": total_words,  # 10B-5-Q2 新增
            "turnsCount": len(turns),
            "speakerStats": speaker_stats,
            "audioDuration": audio_info.get("duration", 0),
            "audioSampleRate": audio_info.get("sample_rate", 0),
            "audioChannels": audio_info.get("channels", 0),
            "avgTurnLength": round(avg_turn_length, 1),  # 10B-5-Q2 新增
            "maxTurnLength": max_turn_length,  # 10B-5-Q2 新增
            "turnsBuiltFrom": "words" if total_words > 0 else "segments",  # 10B-5-Q2 新增
        }
    }


# ============================================================
# 测试函数
# ============================================================

def main():
    """测试 WhisperX 服务"""
    if len(sys.argv) < 2:
        print("用法: python whisperx_service.py <audio_path>")
        sys.exit(1)

    audio_path = sys.argv[1]

    try:
        result = transcribe_with_whisperx(audio_path)

        print("\n" + "="*50)
        print("转录结果:")
        print("="*50)
        print(f"文本:\n{result['text']}\n")
        print(f"语言: {result['language']}")
        print(f"提供商: {result['provider']}")
        print(f"模型: {result['model']}")
        print(f"轮次数: {len(result['turns'])}")
        print(f"说话人分离: {'启用' if result['diarizationEnabled'] else '禁用'}")
        print("="*50)

    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
