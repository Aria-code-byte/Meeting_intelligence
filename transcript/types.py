"""
Transcript module types.

定义原始会议文档的类型结构。
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path
import json


class TranscriptDocument:
    """
    原始会议文档

    包含完整的会议文字记录，按时间顺序组织，带时间戳和元数据。
    这不是摘要，而是会议本身的完整记录。
    """

    def __init__(
        self,
        utterances: List[Dict[str, Any]],
        audio_path: str,
        duration: float,
        asr_provider: str,
        created_at: Optional[str] = None,
        document_path: Optional[str] = None,
        source_transcript_path: Optional[str] = None
    ):
        """
        初始化原始会议文档

        Args:
            utterances: 语音片段列表，每个包含 {start, end, text}
            audio_path: 源音频文件路径
            duration: 音频总时长（秒）
            asr_provider: ASR 服务提供商（如 "whisper-local-base"）
            created_at: 文档创建时间（ISO 8601 格式，可选）
            document_path: 文档保存路径（可选）
            source_transcript_path: 源 ASR 转录文件路径（可选，用于追溯原始工件）

        Raises:
            ValueError: 如果必填字段缺失或无效
            FileNotFoundError: 如果音频文件不存在
        """
        # 验证音频文件存在
        if not Path(audio_path).exists():
            raise FileNotFoundError(f"音频文件不存在: {audio_path}")

        # 验证时长
        if duration <= 0:
            raise ValueError(f"音频时长必须大于 0，当前值: {duration}")

        # 验证并设置语音片段
        self.utterances = self._validate_utterances(utterances)

        self.audio_path = audio_path
        self.duration = duration
        self.asr_provider = asr_provider
        self.created_at = created_at or datetime.now().isoformat()
        self.document_path = document_path
        self.source_transcript_path = source_transcript_path

        # 元数据
        self.utterance_count = len(self.utterances)

    def _validate_utterances(self, utterances: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        验证语音片段列表

        Args:
            utterances: 语音片段列表

        Returns:
            验证后的语音片段列表

        Raises:
            ValueError: 如果语音片段格式无效或时间戳不单调
        """
        if not isinstance(utterances, list):
            raise ValueError("utterances 必须是列表")

        validated = []
        last_end = -1.0

        for i, u in enumerate(utterances):
            if not isinstance(u, dict):
                raise ValueError(f"utterance[{i}] 必须是字典")

            # 检查必需字段
            required_fields = ["start", "end", "text"]
            for field in required_fields:
                if field not in u:
                    raise ValueError(f"utterance[{i}] 缺少字段: {field}")

            # 验证时间戳
            start = float(u["start"])
            end = float(u["end"])
            text = str(u["text"])

            if start < 0:
                raise ValueError(f"utterance[{i}] start 时间不能为负数")

            if end <= start:
                raise ValueError(f"utterance[{i}] end 时间必须大于 start 时间")

            # 检查时间戳单调性（添加容差处理浮点精度）
            epsilon = 0.001  # 1ms 容差
            if start < last_end - epsilon:
                raise ValueError(
                    f"utterance[{i}] 时间戳不单调: start={start}, "
                    f"previous end={last_end}"
                )

            last_end = end

            validated.append({
                "start": start,
                "end": end,
                "text": text
            })

        return validated

    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典格式

        Returns:
            包含完整文档数据的字典
        """
        metadata = {
            "audio_path": self.audio_path,
            "duration": self.duration,
            "asr_provider": self.asr_provider,
            "created_at": self.created_at,
            "utterance_count": self.utterance_count
        }
        if self.source_transcript_path is not None:
            metadata["source_transcript_path"] = self.source_transcript_path
        return {
            "metadata": metadata,
            "utterances": self.utterances
        }

    def save(self, path: Optional[str] = None) -> str:
        """
        保存文档到磁盘

        Args:
            path: 保存路径（可选，默认使用 data/transcripts/）

        Returns:
            保存的文件路径
        """
        if path is None:
            # 生成默认文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            path = f"data/transcripts/transcript_{timestamp}.json"

        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)

        self.document_path = str(output_path)
        return str(output_path)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TranscriptDocument":
        """
        从字典创建文档

        Args:
            data: 包含文档数据的字典

        Returns:
            TranscriptDocument 实例

        Raises:
            ValueError: 如果数据格式无效
        """
        if "metadata" not in data:
            raise ValueError("文档数据缺少 metadata")

        if "utterances" not in data:
            raise ValueError("文档数据缺少 utterances")

        meta = data["metadata"]

        return cls(
            utterances=data["utterances"],
            audio_path=meta["audio_path"],
            duration=meta["duration"],
            asr_provider=meta["asr_provider"],
            created_at=meta.get("created_at"),
            source_transcript_path=meta.get("source_transcript_path")
        )

    def get_full_text(self) -> str:
        """
        获取完整文字内容（不含时间戳）

        Returns:
            所有 utterance 的文字拼接
        """
        return " ".join(u["text"] for u in self.utterances)

    def get_utterances_after(self, timestamp: float) -> List[Dict[str, Any]]:
        """
        获取指定时间之后的语音片段

        Args:
            timestamp: 时间戳（秒）

        Returns:
            该时间之后的 utterance 列表
        """
        return [u for u in self.utterances if u["start"] >= timestamp]

    def get_utterances_before(self, timestamp: float) -> List[Dict[str, Any]]:
        """
        获取指定时间之前的语音片段

        Args:
            timestamp: 时间戳（秒）

        Returns:
            该时间之前的 utterance 列表
        """
        return [u for u in self.utterances if u["end"] <= timestamp]

    def get_utterances_between(self, start: float, end: float) -> List[Dict[str, Any]]:
        """
        获取指定时间范围内的语音片段

        Args:
            start: 开始时间（秒）
            end: 结束时间（秒）

        Returns:
            时间范围内的 utterance 列表
        """
        return [
            u for u in self.utterances
            if u["start"] >= start and u["end"] <= end
        ]

    def __repr__(self) -> str:
        return (
            f"TranscriptDocument("
            f"utterances={self.utterance_count}, "
            f"duration={self.duration:.1f}s, "
            f"provider={self.asr_provider})"
        )
