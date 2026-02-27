"""
ASR transcription module.

Provides speech-to-text conversion with timestamp support.
"""

import json
from pathlib import Path
from typing import Optional, List
from datetime import datetime

from asr.types import TranscriptionResult, Utterance
from asr.providers.whisper import WhisperProvider


# 数据存储目录
TRANSCRIPTS_DIR = Path(__file__).parent.parent / "data" / "transcripts"


def _ensure_transcripts_dir() -> Path:
    """确保转录结果目录存在"""
    TRANSCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
    return TRANSCRIPTS_DIR


def _generate_output_filename() -> str:
    """
    生成输出文件名（基于时间戳）

    Returns:
        输出文件名（.json 格式）
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"transcript_{timestamp}.json"


def _save_result(
    utterances: List[Utterance],
    audio_path: str,
    duration: float,
    asr_provider: str
) -> str:
    """
    保存转录结果到 JSON 文件

    Args:
        utterances: 识别结果列表
        audio_path: 源音频文件路径
        duration: 音频时长
        asr_provider: ASR 提供商名称

    Returns:
        输出文件路径
    """
    output_dir = _ensure_transcripts_dir()
    filename = _generate_output_filename()
    output_path = output_dir / filename

    # 构建结果数据
    data = {
        "utterances": [u.to_dict() for u in utterances],
        "audio_path": audio_path,
        "duration": duration,
        "asr_provider": asr_provider,
        "timestamp": datetime.now().isoformat()
    }

    # 保存到文件
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return str(output_path.absolute())


def _load_result(output_path: str) -> dict:
    """
    从 JSON 文件加载转录结果

    Args:
        output_path: JSON 文件路径

    Returns:
        转录结果数据
    """
    with open(output_path, "r", encoding="utf-8") as f:
        return json.load(f)


def transcribe(
    audio_path: str,
    provider: Optional[str] = None,
    language: str = "auto",
    model_size: str = "base",
    auto_build_transcript: bool = False,
    enable_postprocess: bool = True
) -> TranscriptionResult:
    """
    转写音频文件

    Args:
        audio_path: 音频文件路径（WAV, 16kHz, mono）
        provider: ASR 提供商名称（None 表示使用默认 Whisper）
        language: 语言代码（"auto" 自动检测，"zh" 中文，"en" 英文）
        model_size: Whisper 模型大小（tiny, base, small, medium, large）
        auto_build_transcript: 是否自动构建原始会议文档（默认 False）
        enable_postprocess: 是否启用后处理校正（默认 True）

    Returns:
        TranscriptionResult: 包含识别结果和元数据

    Raises:
        FileNotFoundError: 音频文件不存在
        ValueError: 音频格式不支持
        RuntimeError: ASR 服务不可用或转写失败

    Example:
        >>> result = transcribe("/path/to/audio.wav")
        >>> print(f"识别到 {len(result.utterances)} 条语句")
        >>> for u in result.utterances:
        ...     print(f"[{u.start:.1f}-{u.end:.1f}] {u.text}")
    """
    # 获取音频时长
    from audio.extract_audio import _get_audio_duration
    duration = _get_audio_duration(audio_path)

    # 选择提供商
    if provider is None or provider == "whisper":
        asr_provider = WhisperProvider(model_size=model_size)
    else:
        raise ValueError(f"不支持的 ASR 提供商: {provider}")

    # 执行转写
    utterances = asr_provider.transcribe(audio_path, language)

    # 后处理校正（如果启用）
    if enable_postprocess:
        try:
            from asr.postprocess import postprocess_transcript
            utterances = postprocess_transcript(utterances)
        except ImportError:
            # 如果后处理模块不可用，继续使用原始结果
            pass

    # 保存结果
    output_path = _save_result(
        utterances=utterances,
        audio_path=audio_path,
        duration=duration,
        asr_provider=asr_provider.name
    )

    # 构建结果
    result = TranscriptionResult(
        utterances=utterances,
        audio_path=audio_path,
        duration=duration,
        output_path=output_path,
        asr_provider=asr_provider.name,
        timestamp=datetime.now().isoformat()
    )

    # 自动构建原始会议文档
    if auto_build_transcript:
        from transcript.build import build_transcript
        transcript_doc = build_transcript(result, save=True)
        result.transcript_path = transcript_doc.document_path

    return result


def load_transcript(json_path: str) -> TranscriptionResult:
    """
    从 JSON 文件加载转录结果

    Args:
        json_path: JSON 文件路径

    Returns:
        TranscriptionResult: 转录结果

    Raises:
        FileNotFoundError: JSON 文件不存在
    """
    data = _load_result(json_path)

    # 重建 Utterance 对象
    utterances = [
        Utterance(
            start=u["start"],
            end=u["end"],
            text=u["text"]
        )
        for u in data["utterances"]
    ]

    return TranscriptionResult(
        utterances=utterances,
        audio_path=data["audio_path"],
        duration=data["duration"],
        output_path=json_path,
        asr_provider=data["asr_provider"],
        timestamp=data["timestamp"]
    )


def export_text(result: TranscriptionResult, output_path: str) -> None:
    """
    导出转录结果为纯文本

    Args:
        result: 转录结果
        output_path: 输出文件路径
    """
    with open(output_path, "w", encoding="utf-8") as f:
        for utterance in result.utterances:
            f.write(f"[{utterance.start:.1f}-{utterance.end:.1f}] {utterance.text}\n")


def get_provider(name: str = "whisper") -> object:
    """
    获取 ASR 提供商实例

    Args:
        name: 提供商名称

    Returns:
        ASR 提供商实例
    """
    if name == "whisper":
        return WhisperProvider()
    else:
        raise ValueError(f"不支持的提供商: {name}")
