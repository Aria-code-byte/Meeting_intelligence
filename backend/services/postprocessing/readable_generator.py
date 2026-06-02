"""
可读转录文本生成器
===================
生成带时间戳和角色标签的可读转录文本

功能：
- 生成带时间戳的转录文本
- 格式化为会议纪要样式
- 支持多种输出格式

使用示例：
    generator = ReadableTranscriptGenerator()
    readable_md = generator.generate_markdown(turns)
"""

import re
from typing import List, Dict, Optional
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


class ReadableTranscriptGenerator:
    """可读转录文本生成器"""

    def __init__(self):
        """初始化生成器"""
        self.stats = {
            "total_turns": 0,
            "total_duration": 0,
            "speaker_stats": {}
        }

    def _format_timestamp(self, seconds: float) -> str:
        """
        格式化时间戳为 HH:MM:SS

        Args:
            seconds: 秒数

        Returns:
            格式化的时间戳
        """
        if seconds is None:
            return "00:00:00"

        try:
            total_seconds = int(seconds)
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            secs = total_seconds % 60

            if hours > 0:
                return f"{hours:02d}:{minutes:02d}:{secs:02d}"
            else:
                return f"{minutes:02d}:{secs:02d}"
        except (TypeError, ValueError):
            return "00:00:00"

    def _format_duration(self, start: float, end: float) -> str:
        """
        格式化时长

        Args:
            start: 开始时间（秒）
            end: 结束时间（秒）

        Returns:
            格式化的时长
        """
        try:
            duration = int(end - start)
            if duration < 60:
                return f"{duration}秒"
            else:
                minutes = duration // 60
                secs = duration % 60
                return f"{minutes}分{secs}秒"
        except (TypeError, ValueError):
            return "0秒"

    def generate_markdown(
        self,
        turns: List[Dict],
        title: str = "会议转录",
        include_timestamp: bool = True,
        include_duration: bool = False,
        include_speaker_id: bool = False
    ) -> str:
        """
        生成 Markdown 格式的可读转录文本

        Args:
            turns: 对话轮次列表
            title: 标题
            include_timestamp: 是否包含时间戳
            include_duration: 是否包含时长
            include_speaker_id: 是否包含原始说话人 ID

        Returns:
            Markdown 格式的转录文本
        """
        if not turns:
            return "# 会议转录\n\n（无内容）"

        # 重置统计
        self.stats = {
            "total_turns": len(turns),
            "total_duration": 0,
            "speaker_stats": {}
        }

        lines = [f"# {title}\n"]

        # 添加元信息
        if turns:
            first_turn = turns[0]
            last_turn = turns[-1]
            total_duration = last_turn.get("end", 0) - first_turn.get("start", 0)
            self.stats["total_duration"] = total_duration

            lines.append("## 会议信息\n")
            lines.append(f"- **开始时间**: {self._format_timestamp(first_turn.get('start', 0))}")
            lines.append(f"- **结束时间**: {self._format_timestamp(last_turn.get('end', 0))}")
            lines.append(f"- **总时长**: {self._format_duration(first_turn.get('start', 0), last_turn.get('end', 0))}")
            lines.append(f"- **发言轮次**: {len(turns)}")
            lines.append("\n---\n")

        # 添加转录内容
        lines.append("## 完整文字稿\n")

        for i, turn in enumerate(turns):
            speaker = turn.get("speaker", "UNKNOWN")
            role = turn.get("role", "参会者")
            text = turn.get("text", "").strip()
            start = turn.get("start", 0)
            end = turn.get("end", 0)

            if not text:
                continue

            # 统计说话人信息
            if role not in self.stats["speaker_stats"]:
                self.stats["speaker_stats"][role] = {"count": 0, "words": 0}
            self.stats["speaker_stats"][role]["count"] += 1
            self.stats["speaker_stats"][role]["words"] += len(text)

            # 构建段落标题
            header_parts = []

            if include_timestamp:
                start_ts = self._format_timestamp(start)
                end_ts = self._format_timestamp(end)
                header_parts.append(f"[{start_ts} - {end_ts}]")

            if include_duration:
                duration = self._format_duration(start, end)
                header_parts.append(f"({duration})")

            # 显示角色（如果包含 speaker_id，则格式为 "角色 (SPEAKER_00)"）
            if include_speaker_id:
                header_parts.append(f"**{role}** ({speaker}):")
            else:
                header_parts.append(f"**{role}**:")

            # 组合段落
            paragraph_header = " ".join(header_parts)
            paragraph_text = f"{paragraph_header} {text}"

            lines.append(paragraph_text)
            lines.append("")  # 空行分隔

        return "\n".join(lines)

    def generate_srt(self, turns: List[Dict]) -> str:
        """
        生成 SRT 字幕格式

        Args:
            turns: 对话轮次列表

        Returns:
            SRT 格式文本
        """
        if not turns:
            return ""

        lines = []

        for i, turn in enumerate(turns, 1):
            speaker = turn.get("speaker", "UNKNOWN")
            role = turn.get("role", "参会者")
            text = turn.get("text", "").strip()
            start = turn.get("start", 0)
            end = turn.get("end", 0)

            if not text:
                continue

            # SRT 时间戳格式: 00:00:00,000 --> 00:00:00,000
            start_srt = self._srt_timestamp(start)
            end_srt = self._srt_timestamp(end)

            lines.append(str(i))  # 序号
            lines.append(f"{start_srt} --> {end_srt}")  # 时间戳
            lines.append(f"[{role}] {text}")  # 文本
            lines.append("")  # 空行

        return "\n".join(lines)

    def _srt_timestamp(self, seconds: float) -> str:
        """
        格式化 SRT 时间戳

        Args:
            seconds: 秒数

        Returns:
            SRT 格式时间戳 (HH:MM:SS,mmm)
        """
        try:
            total_seconds = int(seconds)
            milliseconds = int((seconds - total_seconds) * 1000)

            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            secs = total_seconds % 60

            return f"{hours:02d}:{minutes:02d}:{secs:02d},{milliseconds:03d}"
        except (TypeError, ValueError):
            return "00:00:00,000"

    def generate_plain_text(self, turns: List[Dict]) -> str:
        """
        生成纯文本格式（不带时间戳）

        Args:
            turns: 对话轮次列表

        Returns:
            纯文本转录
        """
        if not turns:
            return ""

        lines = []

        for turn in turns:
            role = turn.get("role", "参会者")
            text = turn.get("text", "").strip()

            if not text:
                continue

            lines.append(f"[{role}] {text}")

        return "\n\n".join(lines)

    def get_stats(self) -> Dict:
        """
        获取统计信息

        Returns:
            统计信息字典
        """
        return self.stats.copy()

    def generate_summary_stats(self) -> str:
        """
        生成统计摘要

        Returns:
            Markdown 格式的统计摘要
        """
        if not self.stats["total_turns"]:
            return "（无统计数据）"

        lines = ["## 发言统计\n"]

        # 总体统计
        lines.append(f"- **总轮次**: {self.stats['total_turns']}")
        lines.append(f"- **总时长**: {self._format_duration(0, self.stats['total_duration'])}")

        # 按角色统计
        lines.append("\n### 按角色统计\n")
        for role, stats in self.stats["speaker_stats"].items():
            count = stats["count"]
            words = stats["words"]
            lines.append(f"- **{role}**: {count} 次发言, 约 {words} 字")

        return "\n".join(lines)
