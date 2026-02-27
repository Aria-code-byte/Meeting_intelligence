"""
End-to-end pipeline.

从音频/视频到总结的完整流程。
"""

from typing import Optional, Callable
from pathlib import Path

from asr.transcribe import transcribe as asr_transcribe
from transcript.build import build_transcript
from summarizer.generate import generate_summary
from summarizer.types import SummaryResult
from summarizer.llm import MockLLMProvider


def audio_to_summary(
    audio_path: str,
    template_name: str = "general",
    llm_provider=None,
    progress_callback: Optional[Callable] = None
) -> SummaryResult:
    """
    从音频文件生成总结（完整流程）

    Args:
        audio_path: 音频文件路径
        template_name: 模板名称
        llm_provider: LLM 提供商（可选，默认使用 Mock）
        progress_callback: 进度回调函数 (stage, progress)

    Returns:
        SummaryResult 实例

    Raises:
        FileNotFoundError: 如果音频文件不存在
        RuntimeError: 如果处理失败
    """
    def report(stage: str, progress: int):
        if progress_callback:
            progress_callback(stage, progress)

    try:
        # 阶段 0: 音频格式转换 (如果需要) (0-5%)
        audio_path_obj = Path(audio_path)
        if audio_path_obj.suffix.lower() not in ['.wav']:
            report("convert_audio", 0)
            from audio.preprocess import convert_to_wav
            processed = convert_to_wav(audio_path)
            audio_path = processed.path
            report("convert_audio", 5)

        # 阶段 1: ASR 转写 (5-35%)
        report("asr_transcribe", 5)
        asr_result = asr_transcribe(audio_path, auto_build_transcript=True)
        report("asr_transcribe", 35)

        # 阶段 2: 获取 transcript (35-45%)
        report("load_transcript", 35)
        transcript_path = asr_result.transcript_path
        report("load_transcript", 45)

        # 阶段 3: 生成总结 (45-100%)
        report("generate_summary", 45)
        summary = generate_summary(
            transcript=transcript_path,
            template=template_name,
            llm_provider=llm_provider,
            save=True
        )
        report("generate_summary", 100)

        return summary

    except Exception as e:
        report("error", 0)
        raise RuntimeError(f"处理失败: {e}") from e


def video_to_summary(
    video_path: str,
    template_name: str = "general",
    llm_provider=None,
    progress_callback: Optional[Callable] = None
) -> SummaryResult:
    """
    从视频文件生成总结（完整流程）

    Args:
        video_path: 视频文件路径
        template_name: 模板名称
        llm_provider: LLM 提供商（可选，默认使用 Mock）
        progress_callback: 进度回调函数

    Returns:
        SummaryResult 实例

    Raises:
        FileNotFoundError: 如果视频文件不存在
        RuntimeError: 如果处理失败
    """
    def report(stage: str, progress: int):
        if progress_callback:
            progress_callback(stage, progress)

    try:
        # 阶段 1: 上传视频并提取音频 (0-15%)
        report("upload_video", 0)
        from input.upload_video import upload_video
        input_result = upload_video(video_path)

        # 获取提取的音频路径
        audio_path = input_result.audio_path
        report("upload_video", 15)

        # 阶段 2-4: 使用音频生成总结 (15-100%)
        summary = audio_to_summary(
            audio_path=audio_path,
            template_name=template_name,
            llm_provider=llm_provider,
            progress_callback=lambda stage, prog: report(stage, 15 + prog * 0.85)
        )

        return summary

    except Exception as e:
        report("error", 0)
        raise RuntimeError(f"处理失败: {e}") from e


def quick_summary(
    input_path: str,
    template_name: str = "general",
    use_mock: bool = True
) -> SummaryResult:
    """
    快速生成总结（使用 Mock LLM）

    适合演示和测试。

    Args:
        input_path: 音频或视频文件路径
        template_name: 模板名称
        use_mock: 是否使用 Mock LLM（默认 True）

    Returns:
        SummaryResult 实例
    """
    # 确定文件类型
    path = Path(input_path)
    suffix = path.suffix.lower()

    # 根据文件类型选择流程
    audio_extensions = ['.mp3', '.wav', '.m4a']
    video_extensions = ['.mp4', '.mkv', '.mov']

    # 使用 Mock provider
    provider = MockLLMProvider() if use_mock else None

    if suffix in audio_extensions:
        return audio_to_summary(input_path, template_name, provider)
    elif suffix in video_extensions:
        return video_to_summary(input_path, template_name, provider)
    else:
        raise ValueError(
            f"不支持的文件格式: {suffix}. "
            f"支持的格式: 音频 {audio_extensions}, 视频 {video_extensions}"
        )
