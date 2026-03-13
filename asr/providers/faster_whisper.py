"""
Faster-Whisper ASR Provider.

使用 CTK 实现的 Whisper，比原生 openai-whisper 快 4-5 倍，内存占用减少 50%+。
准确度完全相同，因为使用的是同一个模型文件。

安装: pip install faster-whisper
"""

from typing import List, Optional
from pathlib import Path

from asr.providers.base import BaseASRProvider
from asr.types import Utterance


class FasterWhisperProvider(BaseASRProvider):
    """
    Faster-Whisper ASR 提供商

    使用 faster-whisper (CTK 实现)，相比原生 openai-whisper：
    - 速度提升 4-5 倍
    - 内存占用减少 50%+
    - 准确度完全相同（同一模型文件）

    支持的模型大小: tiny, base, small, medium, large-v1, large-v2, large-v3
    """

    def __init__(
        self,
        model_size: str = "base",
        device: str = "auto",
        compute_type: str = "default",
        num_workers: int = 1,
    ):
        """
        初始化 Faster-Whisper 提供商

        Args:
            model_size: 模型大小（tiny, base, small, medium, large-v1, large-v2, large-v3）
            device: 计算设备（auto, cpu, cuda）
            compute_type: 计算精度（default, int8, float16, float32）
                        - default: 自动选择最佳精度
                        - int8: 最快，轻微精度损失
                        - float16: GPU 推荐，速度快
                        - float32: 最精确，CPU 推荐
            num_workers: 并行处理数量（默认 1）
        """
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self.num_workers = num_workers
        self._model = None
        self._available = self._check_available()

    @property
    def name(self) -> str:
        """提供商名称"""
        device_suffix = f"-{self.device}" if self.device != "auto" else ""
        return f"faster-whisper-{self.model_size}{device_suffix}"

    def _check_available(self) -> bool:
        """
        检查 faster-whisper 是否可用

        Returns:
            True 如果 faster-whisper 已安装
        """
        try:
            from faster_whisper import WhisperModel
            return True
        except ImportError:
            return False

    def _load_model(self):
        """
        延迟加载模型

        只在第一次转写时加载，避免初始化开销
        """
        if self._model is not None:
            return

        if not self._available:
            raise RuntimeError(
                "faster-whisper 未安装。请运行: pip install faster-whisper"
            )

        from faster_whisper import WhisperModel

        # 根据设备自动选择计算类型
        if self.compute_type == "default":
            import torch
            if self.device == "cuda" or (self.device == "auto" and torch.cuda.is_available()):
                self.compute_type = "float16"  # GPU 使用 float16
            else:
                self.compute_type = "int8"  # CPU 使用 int8 加速

        # 加载模型
        self._model = WhisperModel(
            self.model_size,
            device=self.device,
            compute_type=self.compute_type,
            num_workers=self.num_workers,
        )

    def transcribe(
        self,
        audio_path: str,
        language: str = "auto",
        vad_filter: bool = True,
        beam_size: int = 5,
    ) -> List[Utterance]:
        """
        使用 Faster-Whisper 转写音频

        Args:
            audio_path: 音频文件路径（支持 WAV, MP3, M4A 等格式）
            language: 语言代码（"auto" 自动检测，"zh" 中文，"en" 英文）
            vad_filter: 是否使用 VAD (语音活动检测) 过滤静音片段
            beam_size: 束搜索大小（越大越精确，但更慢）

        Returns:
            识别结果列表

        Raises:
            FileNotFoundError: 音频文件不存在
            RuntimeError: faster-whisper 不可用或转写失败
        """
        # 验证音频文件
        self._validate_audio_file(audio_path)

        # 延迟加载模型
        self._load_model()

        # 语言参数处理
        if language == "auto":
            language_param = None
        else:
            language_param = language

        try:
            # 执行转写
            segments, info = self._model.transcribe(
                audio_path,
                language=language_param,
                vad_filter=vad_filter,
                beam_size=beam_size,
                word_timestamps=False,  # 不需要词级时间戳
            )

            # 转换为 Utterance 格式
            utterances = []
            for segment in segments:
                text = segment.text.strip()
                # 跳过空文本
                if text:
                    utterances.append(Utterance(
                        start=segment.start,
                        end=segment.end,
                        text=text
                    ))

            return utterances

        except Exception as e:
            raise RuntimeError(f"Faster-Whisper 转写失败: {e}")

    def get_language_info(self, audio_path: str) -> dict:
        """
        检测音频语言（不执行完整转写）

        Args:
            audio_path: 音频文件路径

        Returns:
            包含语言信息的字典: {"language": "zh", "probability": 0.98}
        """
        self._load_model()

        self._validate_audio_file(audio_path)

        _, info = self._model.transcribe(
            audio_path,
            language=None,
            vad_filter=False,
            beam_size=1,
        )

        return {
            "language": info.language,
            "language_probability": info.language_probability,
            "duration": info.duration,
        }
