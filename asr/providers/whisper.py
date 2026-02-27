"""
Whisper ASR provider.

Supports both local Whisper (via openai-whisper) and Whisper API.
"""

from typing import List
import subprocess

from asr.providers.base import BaseASRProvider
from asr.types import Utterance


class WhisperProvider(BaseASRProvider):
    """
    Whisper ASR 提供商

    支持：
    - 本地 Whisper（通过 openai-whisper 或 faster-whisper）
    - Whisper API（通过 OpenAI API）

    默认使用本地 Whisper，如果未安装则回退到 API。
    """

    def __init__(
        self,
        model_size: str = "base",
        use_api: bool = False,
        api_key: str = None
    ):
        """
        初始化 Whisper 提供商

        Args:
            model_size: 模型大小（tiny, base, small, medium, large）
            use_api: 是否使用 API（默认 False，使用本地）
            api_key: OpenAI API key（仅 use_api=True 时需要）
        """
        self.model_size = model_size
        self.use_api = use_api
        self.api_key = api_key
        self._local_available = self._check_local_whisper()

    @property
    def name(self) -> str:
        """提供商名称"""
        if self.use_api:
            return "whisper-api"
        return f"whisper-local-{self.model_size}"

    def _check_local_whisper(self) -> bool:
        """
        检查本地 Whisper 是否可用

        Returns:
            True 如果本地 Whisper 已安装
        """
        try:
            import whisper
            return True
        except ImportError:
            return False

    def transcribe(
        self,
        audio_path: str,
        language: str = "auto"
    ) -> List[Utterance]:
        """
        使用 Whisper 转写音频

        Args:
            audio_path: 音频文件路径（WAV 格式）
            language: 语言代码（"auto", "zh", "en"）

        Returns:
            识别结果列表

        Raises:
            FileNotFoundError: 音频文件不存在
            RuntimeError: Whisper 不可用或转写失败
        """
        # 验证音频文件
        self._validate_audio_file(audio_path)

        # 选择转写方式
        if self.use_api:
            return self._transcribe_with_api(audio_path, language)
        else:
            return self._transcribe_local(audio_path, language)

    def _transcribe_local(
        self,
        audio_path: str,
        language: str
    ) -> List[Utterance]:
        """
        使用本地 Whisper 转写

        Args:
            audio_path: 音频文件路径
            language: 语言代码

        Returns:
            识别结果列表
        """
        if not self._local_available:
            raise RuntimeError(
                "本地 Whisper 未安装。请安装: pip install openai-whisper"
            )

        try:
            import whisper

            # 加载模型
            model = whisper.load_model(self.model_size)

            # 语言参数处理
            language_arg = None if language == "auto" else language

            # 转写
            result = model.transcribe(
                audio_path,
                language=language_arg,
                word_timestamps=False  # 不需要词级时间戳
            )

            # 转换为 Utterance 格式
            utterances = []
            for segment in result.get("segments", []):
                text = segment["text"].strip()
                # 跳过空文本
                if text:
                    utterances.append(Utterance(
                        start=segment["start"],
                        end=segment["end"],
                        text=text
                    ))

            return utterances

        except Exception as e:
            raise RuntimeError(f"Whisper 转写失败: {e}")

    def _transcribe_with_api(
        self,
        audio_path: str,
        language: str
    ) -> List[Utterance]:
        """
        使用 Whisper API 转写

        TODO: 实现 OpenAI Whisper API 调用

        Args:
            audio_path: 音频文件路径
            language: 语言代码

        Returns:
            识别结果列表
        """
        raise NotImplementedError(
            "Whisper API 尚未实现。请使用本地 Whisper 或安装: pip install openai"
        )
