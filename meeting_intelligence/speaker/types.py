"""
发言人识别数据类型
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime


@dataclass
class SpeakerSegment:
    """
    单个发言人片段

    表示一段时间内某个发言人的语音片段。

    Attributes:
        start: 开始时间（秒）
        end: 结束时间（秒）
        speaker: 发言人 ID（如 "SPEAKER_00"）
        confidence: 置信度（0-1）
    """
    start: float
    end: float
    speaker: str
    confidence: float = 0.0

    @property
    def duration(self) -> float:
        """片段时长（秒）"""
        return self.end - self.start

    def overlaps_with(self, other: "SpeakerSegment") -> bool:
        """检查是否与另一个片段重叠"""
        return not (self.end <= other.start or self.start >= other.end)

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "start": self.start,
            "end": self.end,
            "speaker": self.speaker,
            "confidence": self.confidence,
        }


@dataclass
class SpeakerInfo:
    """
    发言人信息

    Attributes:
        speaker_id: 发言人 ID（如 "SPEAKER_00"）
        display_name: 显示名称（用户可自定义，如 "张三"）
        total_duration: 总发言时长（秒）
        segment_count: 发言片段数
        first_appearance: 首次出现时间（秒）
        color: UI 显示颜色（可选）
    """
    speaker_id: str
    display_name: Optional[str] = None
    total_duration: float = 0.0
    segment_count: int = 0
    first_appearance: float = 0.0
    color: Optional[str] = None

    def __post_init__(self):
        """初始化显示名称"""
        if self.display_name is None:
            # 从 ID 提取友好的名称
            if self.speaker_id.startswith("SPEAKER_"):
                num = int(self.speaker_id.split("_")[1])
                self.display_name = f"发言人 {chr(65 + num)}"  # A, B, C...
            else:
                self.display_name = self.speaker_id

    @property
    def avg_segment_duration(self) -> float:
        """平均片段时长"""
        if self.segment_count == 0:
            return 0.0
        return self.total_duration / self.segment_count

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "speaker_id": self.speaker_id,
            "display_name": self.display_name,
            "total_duration": self.total_duration,
            "segment_count": self.segment_count,
            "first_appearance": self.first_appearance,
            "avg_segment_duration": self.avg_segment_duration,
            "color": self.color,
        }


@dataclass
class DiarizationResult:
    """
    发言人分离结果

    Attributes:
        segments: 发言人片段列表（按时间排序）
        speakers: 发言人信息字典
        audio_path: 源音频文件路径
        duration: 音频总时长（秒）
        model: 使用的模型名称
        timestamp: 处理时间戳
    """
    segments: List[SpeakerSegment] = field(default_factory=list)
    speakers: Dict[str, SpeakerInfo] = field(default_factory=dict)
    audio_path: str = ""
    duration: float = 0.0
    model: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def add_segment(self, segment: SpeakerSegment) -> None:
        """添加片段并更新统计信息"""
        self.segments.append(segment)

        # 更新或创建发言人信息
        if segment.speaker not in self.speakers:
            self.speakers[segment.speaker] = SpeakerInfo(
                speaker_id=segment.speaker,
                first_appearance=segment.start
            )

        info = self.speakers[segment.speaker]
        info.total_duration += segment.duration
        info.segment_count += 1

    def get_speaker_segments(self, speaker_id: str) -> List[SpeakerSegment]:
        """获取指定发言人的所有片段"""
        return [s for s in self.segments if s.speaker == speaker_id]

    def get_segments_at_time(self, time: float) -> List[SpeakerSegment]:
        """获取指定时间点的发言片段"""
        return [s for s in self.segments if s.start <= time < s.end]

    def get_dominant_speaker(self) -> Optional[str]:
        """获取发言时长最长的发言人"""
        if not self.speakers:
            return None
        return max(self.speakers.items(), key=lambda x: x[1].total_duration)[0]

    def sort_segments(self) -> None:
        """按时间排序片段"""
        self.segments.sort(key=lambda s: s.start)

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "segments": [s.to_dict() for s in self.segments],
            "speakers": {
                k: v.to_dict() for k, v in self.speakers.items()
            },
            "audio_path": self.audio_path,
            "duration": self.duration,
            "model": self.model,
            "timestamp": self.timestamp,
            "dominant_speaker": self.get_dominant_speaker(),
        }
