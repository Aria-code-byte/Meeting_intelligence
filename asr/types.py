"""
Shared types for the ASR module.

This module defines the common data structures used across all ASR operations.
"""

from dataclasses import dataclass
from typing import Optional, List
from pathlib import Path


@dataclass
class Utterance:
    """
    单条语音识别结果

    表示一段连续的语音及其对应文本。

    Attributes:
        start: 开始时间（秒）
        end: 结束时间（秒）
        text: 识别文本内容
    """
    start: float
    end: float
    text: str

    def __post_init__(self):
        """验证时间戳"""
        if self.start < 0:
            raise ValueError(f"开始时间不能为负数: {self.start}")
        if self.end <= self.start:
            raise ValueError(f"结束时间必须大于开始时间: start={self.start}, end={self.end}")
        if not self.text:
            raise ValueError("文本内容不能为空")

    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "start": self.start,
            "end": self.end,
            "text": self.text
        }


@dataclass
class TranscriptionResult:
    """
    语音识别结果接口

    所有 ASR 操作都返回此结构。

    Attributes:
        utterances: 识别结果列表（按时间顺序）
        audio_path: 源音频文件路径
        duration: 音频总时长（秒）
        output_path: 结果 JSON 文件路径
        asr_provider: ASR 提供商名称
        timestamp: 识别时间戳
        transcript_path: 原始会议文档路径（可选，始终指向 raw ASR transcript）
        enhanced_transcript_path: 增强版文档路径（可选，预留用于 future PRs）
    """
    utterances: List[Utterance]
    audio_path: str
    duration: float
    output_path: str
    asr_provider: str
    timestamp: str
    transcript_path: Optional[str] = None
    # transcript_path 始终指向原始 ASR 转录文件
    # enhanced_transcript_path 预留给未来的增强版输出
    enhanced_transcript_path: Optional[str] = None

    def __post_init__(self):
        """验证结果"""
        # 验证文件存在
        audio_file = Path(self.audio_path)
        if not audio_file.exists():
            raise FileNotFoundError(f"音频文件不存在: {self.audio_path}")

        output_file = Path(self.output_path)
        if not output_file.exists():
            raise FileNotFoundError(f"输出文件不存在: {self.output_path}")

        # 验证 transcript_path（如果提供）
        if self.transcript_path is not None:
            transcript_file = Path(self.transcript_path)
            if not transcript_file.exists():
                raise FileNotFoundError(f"文档文件不存在: {self.transcript_path}")

        # 验证时长
        if self.duration <= 0:
            raise ValueError(f"音频时长必须大于 0: {self.duration}")

        # 验证时间戳单调性（添加小容差处理浮点精度）
        prev_end = -1
        epsilon = 0.001  # 1ms 容差
        for utterance in self.utterances:
            if utterance.start < prev_end - epsilon:
                raise ValueError(f"时间戳不单调: utterance.start={utterance.start}, prev_end={prev_end}")
            if utterance.end > self.duration:
                raise ValueError(f"utterance 时间超出音频时长: end={utterance.end}, duration={self.duration}")
            prev_end = utterance.end

    def to_dict(self) -> dict:
        """转换为字典格式"""
        result = {
            "utterances": [u.to_dict() for u in self.utterances],
            "audio_path": self.audio_path,
            "duration": self.duration,
            "output_path": self.output_path,
            "asr_provider": self.asr_provider,
            "timestamp": self.timestamp
        }
        if self.transcript_path is not None:
            result["transcript_path"] = self.transcript_path
        if self.enhanced_transcript_path is not None:
            result["enhanced_transcript_path"] = self.enhanced_transcript_path
        return result

    def get_full_text(self) -> str:
        """获取完整文本（所有 utterances 拼接）"""
        return "".join(u.text for u in self.utterances)
