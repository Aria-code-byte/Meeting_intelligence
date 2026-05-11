"""
发言人分离引擎 (Speaker Diarization)

使用 pyannote.audio 进行发言人识别和分离。
"""
import sys
import warnings
from pathlib import Path
from typing import List, Optional, Union

# 抑制 pyannote 的警告
warnings.filterwarnings("ignore", category=UserWarning)

try:
    from .types import SpeakerSegment, DiarizationResult, SpeakerInfo
except ImportError:
    from speaker.types import SpeakerSegment, DiarizationResult, SpeakerInfo


class SpeakerDiarization:
    """
    发言人分离引擎

    使用 pyannote.audio 进行语音活动检测和发言人聚类。

    Example:
        >>> diarization = SpeakerDiarization()
        >>> result = diarization.process("meeting.wav")
        >>> for segment in result.segments:
        ...     print(f"[{segment.start:.1f}-{segment.end:.1f}] {segment.speaker}")
    """

    def __init__(self, model_name: str = "pyannote/speaker-diarization-3.1"):
        """
        初始化发言人分离引擎

        Args:
            model_name: pyannote 模型名称
                       - "pyannote/speaker-diarization-3.1": 最准确（推荐）
                       - "pyannote/speaker-diarization": 旧版本

        Note:
            首次使用需要从 HuggingFace 下载模型。
            需要接受 pyannote 的模型使用协议。
        """
        self.model_name = model_name
        self.pipeline = None
        self._load_pipeline()

    def _load_pipeline(self) -> None:
        """加载 pyannote pipeline"""
        try:
            from pyannote.audio import Pipeline
            self.pipeline = Pipeline.from_pretrained(
                self.model_name,
                use_auth_token=False  # 如果需要 token，从配置读取
            )

            # 尝试使用 GPU（如果可用）
            import torch
            if torch.cuda.is_available():
                self.pipeline.to(torch.device("cuda"))
                print("✓ 使用 GPU 加速发言人分离")
            else:
                print("✓ 使用 CPU 进行发言人分离")

        except ImportError:
            raise RuntimeError(
                "pyannote.audio 未安装。\n"
                "请运行: pip install pyannote.audio\n"
                "注意: 首次使用需要从 HuggingFace 下载模型"
            )
        except Exception as e:
            raise RuntimeError(f"加载 pyannote pipeline 失败: {e}")

    def process(
        self,
        audio_path: str,
        min_speakers: int = 1,
        max_speakers: int = 10
    ) -> DiarizationResult:
        """
        处理音频文件，进行发言人分离

        Args:
            audio_path: 音频文件路径
            min_speakers: 最小发言人数量
            max_speakers: 最大发言人数量

        Returns:
            DiarizationResult: 分离结果

        Raises:
            FileNotFoundError: 音频文件不存在
            RuntimeError: 处理失败
        """
        audio_file = Path(audio_path)
        if not audio_file.exists():
            raise FileNotFoundError(f"音频文件不存在: {audio_path}")

        if self.pipeline is None:
            raise RuntimeError("pyannote pipeline 未加载")

        print(f"正在分析音频文件: {audio_file.name}")
        print(f"预计发言人数量: {min_speakers}-{max_speakers}")

        # 执行分离
        try:
            diarization = self.pipeline(
                audio_path,
                min_speakers=min_speakers,
                max_speakers=max_speakers
            )
        except Exception as e:
            raise RuntimeError(f"发言人分离失败: {e}")

        # 转换结果
        result = DiarizationResult(
            audio_path=str(audio_path.absolute()),
            model=self.model_name
        )

        # pyannote 返回的是迭代器，格式为 (turn, _, speaker)
        # turn 是 Segment 对象，包含 start 和 end
        for turn, _, speaker in diarization.itertracks(yield_label=True):
            segment = SpeakerSegment(
                start=turn.start,
                end=turn.end,
                speaker=speaker,
                confidence=1.0  # pyannote 不直接提供置信度
            )
            result.add_segment(segment)

        result.sort_segments()

        print(f"✓ 识别到 {len(result.speakers)} 位发言人")
        print(f"✓ 共 {len(result.segments)} 个发言片段")

        return result

    def align_with_transcript(
        self,
        diarization_result: DiarizationResult,
        utterances: list
    ) -> list:
        """
        将发言人信息与转录结果对齐

        Args:
            diarization_result: 发言人分离结果
            utterances: 转录的 utterance 列表

        Returns:
            带发言人标签的 utterance 列表
        """
        aligned_utterances = []

        for utterance in utterances:
            # 获取 utterance 时间段的中点
            mid_time = (utterance.start + utterance.end) / 2

            # 查找该时间点的发言人
            segments_at_time = diarization_result.get_segments_at_time(mid_time)

            if segments_at_time:
                # 使用置信度最高的片段
                speaker = segments_at_time[0].speaker
            else:
                # 如果没有找到，使用最近的片段
                speaker = self._find_nearest_speaker(diarization_result, mid_time)

            # 添加发言人标签
            if hasattr(utterance, '__dict__'):
                utterance.speaker = speaker
            else:
                # 对于 Utterance dataclass，创建新对象
                from dataclasses import replace
                utterance = replace(utterance, speaker=speaker)

            aligned_utterances.append(utterance)

        return aligned_utterances

    def _find_nearest_speaker(
        self,
        diarization_result: DiarizationResult,
        time: float
    ) -> str:
        """查找离给定时间最近的发言人"""
        if not diarization_result.segments:
            return "UNKNOWN"

        # 找到最近的片段
        nearest_segment = min(
            diarization_result.segments,
            key=lambda s: min(abs(s.start - time), abs(s.end - time))
        )

        return nearest_segment.speaker


class MockSpeakerDiarization:
    """
    模拟发言人分离（用于测试）

    基于简单的规则分配发言人标签。
    """

    def __init__(self, num_speakers: int = 2):
        """
        初始化模拟器

        Args:
            num_speakers: 模拟的发言人数量
        """
        self.num_speakers = num_speakers
        self.current_speaker = 0

    def process(self, audio_path: str, **kwargs) -> DiarizationResult:
        """
        模拟处理（仅基于时间分配发言人）

        Args:
            audio_path: 音频文件路径

        Returns:
            DiarizationResult: 模拟的分离结果
        """
        import librosa

        # 获取音频时长
        duration = librosa.get_duration(filename=audio_path)

        result = DiarizationResult(
            audio_path=str(Path(audio_path).absolute()),
            duration=duration,
            model="mock"
        )

        # 每 30 秒切换一次发言人
        segment_duration = 30.0
        current_time = 0.0

        while current_time < duration:
            end_time = min(current_time + segment_duration, duration)

            segment = SpeakerSegment(
                start=current_time,
                end=end_time,
                speaker=f"SPEAKER_{self.current_speaker:02d}",
                confidence=0.8
            )
            result.add_segment(segment)

            current_time = end_time
            self.current_speaker = (self.current_speaker + 1) % self.num_speakers

        return result

    def align_with_transcript(
        self,
        diarization_result: DiarizationResult,
        utterances: list
    ) -> list:
        """对齐转录结果"""
        return SpeakerDiarization.align_with_transcript(
            self, diarization_result, utterances
        )


def create_diarization_engine(use_mock: bool = False) -> Union[SpeakerDiarization, MockSpeakerDiarization]:
    """
    创建发言人分离引擎

    Args:
        use_mock: 是否使用模拟引擎（用于测试）

    Returns:
        发言人分离引擎实例
    """
    if use_mock:
        print("⚠ 使用模拟发言人分离引擎")
        return MockSpeakerDiarization()

    try:
        return SpeakerDiarization()
    except Exception as e:
        print(f"⚠ 无法加载真实引擎: {e}")
        print("使用模拟引擎代替")
        return MockSpeakerDiarization()
