"""
WhisperX Transcription Service
============================
WhisperX + pyannote.audio 说话人分离转录服务

功能：
- 使用 WhisperX 进行高精度语音识别
- 支持词级时间戳对齐
- 使用 pyannote.audio 进行说话人分离
- 生成结构化的对话轮次（turns）

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
"""

import os
import sys
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import time

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

# Diarization 配置
DIARIZATION_ENABLED = _get_env("DIARIZATION_ENABLED", True)
PYANNOTE_DIARIZE_MODEL = _get_env("PYANNOTE_DIARIZE_MODEL", "pyannote/speaker-diarization-community-1")
HF_TOKEN = _get_env("HF_TOKEN") or _get_env("HUGGINGFACE_TOKEN")
DIARIZATION_MERGE_GAP = _get_env("DIARIZATION_MERGE_GAP", 1.0)


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

    # 检查是否可以合并到上一个轮次
    if turns:
        last_turn = turns[-1]
        gap = start - last_turn["end"]

        # 同一说话人且间隔较小，合并
        if (last_turn["speaker"] == speaker and
            gap <= DIARIZATION_MERGE_GAP):
            last_turn["end"] = end
            last_turn["text"] += " " + text
            return

    # 添加新轮次
    turns.append({
        "speaker": speaker,
        "start": round(start, 2),
        "end": round(end, 2),
        "text": text
    })


def build_turns(
    segments: List[Dict[str, Any]],
    diarization_enabled: bool = True
) -> List[Dict[str, Any]]:
    """
    从片段构建对话轮次

    Args:
        segments: WhisperX 片段列表
        diarization_enabled: 是否启用了说话人分离

    Returns:
        对话轮次列表
    """
    turns: List[Dict[str, Any]] = []

    if not segments:
        return turns

    for segment in segments:
        start = segment.get("start", 0)
        end = segment.get("end", 0)
        text = segment.get("text", "")
        words = segment.get("words", [])

        if not text.strip():
            continue

        if diarization_enabled and words:
            # 有说话人信息
            speaker = speaker_for_segment(words)
            if speaker:
                add_turn(turns, speaker, start, end, text)
            else:
                # 没有说话人信息，使用 "UNKNOWN"
                add_turn(turns, "UNKNOWN", start, end, text)
        else:
            # 没有说话人分离，使用 "SPEAKER"
            add_turn(turns, "SPEAKER", start, end, text)

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
    hf_token: Optional[str] = None
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

    if diarization_enabled and not hf_token:
        raise ValueError(
            "说话人分离需要 Hugging Face token。"
            "请设置 HF_TOKEN 或 HUGGINGFACE_TOKEN 环境变量，"
            "或通过 hf_token 参数传入。"
            "\n获取 token: https://huggingface.co/settings/tokens"
        )

    print(f"[WhisperX] 开始转录...")
    print(f"[WhisperX] 音频: {audio_path}")
    print(f"[WhisperX] 模型: {model}")
    print(f"[WhisperX] 语言: {language}")
    print(f"[WhisperX] 设备: {device}")
    print(f"[WhisperX] 批处理大小: {batch_size}")
    print(f"[WhisperX] 跳过对齐: {skip_align}")
    print(f"[WhisperX] 说话人分离: {diarization_enabled}")

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
        print(f"[WhisperX] 加载音频...")
        audio = whisperx.load_audio(audio_path)
        print(f"[WhisperX] 音频加载成功，shape: {audio.shape}")
    except Exception as e:
        raise RuntimeError(f"音频加载失败: {e}")

    # ============================================================
    # 加载 WhisperX 模型并转录
    # ============================================================

    try:
        print(f"[WhisperX] 加载模型...")
        whisper_model = whisperx.load_model(
            model,
            device,
            compute_type=compute_type,
            language=language
        )
        print(f"[WhisperX] 模型加载成功")

        print(f"[WhisperX] 开始转录...")
        result = whisper_model.transcribe(
            audio,
            batch_size=batch_size,
            language=language
        )
        print(f"[WhisperX] 转录完成，片段数: {len(result.get('segments', []))}")

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
            print(f"[WhisperX] 开始词级对齐...")
            model_a, metadata = whisperx.load_align_model(
                language_code=detected_language,
                device=device
            )

            result = whisperx.align(
                result["segments"],
                model_a,
                metadata,
                audio,
                device,
            )
            alignment_status = "success"
            print(f"[WhisperX] 对齐完成")

            # 释放对齐模型内存
            del model_a

        except Exception as e:
            alignment_status = "failed"
            alignment_error = str(e)
            print(f"[WhisperX] 对齐失败: {e}")
            print(f"[WhisperX] 继续使用原始转录结果...")
    else:
        print(f"[WhisperX] 跳过词级对齐")

    # ============================================================
    # 说话人分离
    # ============================================================

    if diarization_enabled:
        try:
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
            diarize_model = DiarizationPipeline(
                use_auth_token=hf_token,
                model=PYANNOTE_DIARIZE_MODEL,
                device=device
            )

            # 执行说话人分离
            diarize_segments = diarize_model(
                audio,
                min_speakers=None,
                max_speakers=None
            )

            # 将说话人标签分配给词
            result = assign_word_speakers(
                diarize_segments,
                result,
                fill_missing_words=True
            )

            print(f"[WhisperX] 说话人分离完成")

            # 释放说话人分离模型内存
            del diarize_model

        except ImportError:
            raise
        except Exception as e:
            raise RuntimeError(f"说话人分离失败: {e}")

    # ============================================================
    # 构建结果
    # ============================================================

    segments = result.get("segments", [])

    # 构建对话轮次
    turns = build_turns(segments, diarization_enabled)

    # 构建完整文本
    full_text = "\n".join(
        f"[{turn['speaker']}] {turn['text']}"
        for turn in turns
    )

    processing_time = time.time() - start_time

    print(f"[WhisperX] 处理完成，耗时: {processing_time:.2f}s")
    print(f"[WhisperX] 轮次数: {len(turns)}")

    return {
        "text": full_text,
        "language": detected_language,
        "provider": "whisperx",
        "model": model,
        "segments": segments,
        "turns": turns,
        "diarizationEnabled": diarization_enabled,
        "diarizationProvider": "pyannote" if diarization_enabled else None,
        "diarizationModel": PYANNOTE_DIARIZE_MODEL if diarization_enabled else None,
        "alignmentStatus": alignment_status,
        "alignmentError": alignment_error,
        "raw": {
            "processingTimeSeconds": round(processing_time, 2),
            "audioPath": str(audio_path_obj),
            "languageDetected": detected_language,
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
