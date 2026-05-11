"""
发言人 UI 管理模块

提供发言人管理的用户界面功能：
- 查看发言人统计
- 重命名发言人
- 合并发言人
- 按发言人筛选内容
"""
import json
from pathlib import Path
from typing import Dict, List, Optional

try:
    from .types import SpeakerInfo, DiarizationResult
except ImportError:
    from speaker.types import SpeakerInfo, DiarizationResult


class SpeakerManager:
    """
    发言人管理器

    管理发言人的名称、颜色等自定义属性。

    Example:
        >>> manager = SpeakerManager()
        >>> manager.set_display_name("SPEAKER_00", "张三")
        >>> manager.set_color("SPEAKER_00", "#FF5733")
    """

    def __init__(self, storage_path: Optional[Path] = None):
        """
        初始化管理器

        Args:
            storage_path: 配置文件路径（默认: .config/speakers.json）
        """
        if storage_path is None:
            project_root = Path(__file__).parent.parent.parent
            storage_path = project_root / ".config" / "speakers.json"

        self.storage_path = storage_path
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

        self.custom_names: Dict[str, str] = {}
        self.custom_colors: Dict[str, str] = {}
        self.merged_speakers: Dict[str, str] = {}  # key -> target

        self._load()

    def _load(self) -> None:
        """从文件加载配置"""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                self.custom_names = data.get("names", {})
                self.custom_colors = data.get("colors", {})
                self.merged_speakers = data.get("merged", {})

            except Exception as e:
                print(f"警告: 加载发言人配置失败 - {e}")

    def _save(self) -> None:
        """保存配置到文件"""
        data = {
            "names": self.custom_names,
            "colors": self.custom_colors,
            "merged": self.merged_speakers
        }

        with open(self.storage_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def set_display_name(self, speaker_id: str, display_name: str) -> None:
        """
        设置发言人显示名称

        Args:
            speaker_id: 发言人 ID
            display_name: 显示名称
        """
        self.custom_names[speaker_id] = display_name
        self._save()

    def get_display_name(self, speaker_id: str) -> str:
        """
        获取发言人显示名称

        Args:
            speaker_id: 发言人 ID

        Returns:
            显示名称（如果未自定义则返回默认名称）
        """
        if speaker_id in self.custom_names:
            return self.custom_names[speaker_id]

        # 默认名称
        if speaker_id.startswith("SPEAKER_"):
            num = int(speaker_id.split("_")[1])
            return f"发言人 {chr(65 + num)}"  # A, B, C...

        return speaker_id

    def set_color(self, speaker_id: str, color: str) -> None:
        """
        设置发言人颜色

        Args:
            speaker_id: 发言人 ID
            color: 颜色值（如 "#FF5733"）
        """
        self.custom_colors[speaker_id] = color
        self._save()

    def get_color(self, speaker_id: str) -> Optional[str]:
        """获取发言人颜色"""
        return self.custom_colors.get(speaker_id)

    def merge_speakers(self, source_id: str, target_id: str) -> None:
        """
        合并发言人

        Args:
            source_id: 要合并的发言人 ID
            target_id: 目标发言人 ID
        """
        self.merged_speakers[source_id] = target_id
        self._save()

    def get_resolved_speaker(self, speaker_id: str) -> str:
        """
        获取解析后的发言人 ID（处理合并）

        Args:
            speaker_id: 原始发言人 ID

        Returns:
            解析后的发言人 ID（如果被合并则返回目标 ID）
        """
        # 追踪合并链
        visited = set()
        current = speaker_id

        while current in self.merged_speakers:
            if current in visited:
                # 检测到循环，返回原始 ID
                return speaker_id
            visited.add(current)
            current = self.merged_speakers[current]

        return current

    def get_display_name_resolved(self, speaker_id: str) -> str:
        """获取解析后的显示名称"""
        resolved_id = self.get_resolved_speaker(speaker_id)
        return self.get_display_name(resolved_id)

    def list_speakers(self, result: DiarizationResult) -> List[Dict]:
        """
        列出所有发言人及其统计信息

        Args:
            result: 发言人分离结果

        Returns:
            发言人信息列表
        """
        speakers = []

        for speaker_id, info in result.speakers.items():
            resolved_id = self.get_resolved_speaker(speaker_id)
            display_name = self.get_display_name_resolved(speaker_id)
            color = self.get_color(resolved_id)

            # 计算百分比
            total_duration = result.duration
            percentage = (info.total_duration / total_duration * 100) if total_duration > 0 else 0

            speakers.append({
                "id": speaker_id,
                "resolved_id": resolved_id,
                "display_name": display_name,
                "total_duration": info.total_duration,
                "segment_count": info.segment_count,
                "percentage": percentage,
                "color": color,
                "is_merged": speaker_id != resolved_id
            })

        # 按发言时长排序
        speakers.sort(key=lambda x: x["total_duration"], reverse=True)

        return speakers

    def format_speaker_list(self, result: DiarizationResult) -> str:
        """
        格式化发言人列表为文本

        Args:
            result: 发言人分离结果

        Returns:
            格式化的文本
        """
        speakers = self.list_speakers(result)

        lines = [
            "=" * 60,
            "  发言人统计",
            "=" * 60,
            "",
            f"总计 {len(speakers)} 位发言人",
            ""
        ]

        for i, speaker in enumerate(speakers, 1):
            duration_min = speaker["total_duration"] / 60

            lines.append(f"[{i}] {speaker['display_name']} ({speaker['id']})")
            lines.append(f"    发言时长: {duration_min:.1f} 分钟 ({speaker['percentage']:.1f}%)")
            lines.append(f"    发言片段: {speaker['segment_count']} 次")

            if speaker["is_merged"]:
                lines.append(f"    → 已合并到: {speaker['resolved_id']}")

            lines.append("")

        return "\n".join(lines)


def format_transcript_with_speakers(
    utterances: list,
    speaker_manager: Optional[SpeakerManager] = None
) -> str:
    """
    格式化带发言人标签的转录文本

    Args:
        utterances: utterance 列表（需包含 speaker 属性）
        speaker_manager: 发言人管理器（可选）

    Returns:
        格式化的文本
    """
    lines = []

    for u in utterances:
        # 获取时间
        start_min = int(u.start // 60)
        start_sec = int(u.start % 60)
        end_min = int(u.end // 60)
        end_sec = int(u.end % 60)

        time_str = f"{start_min:02d}:{start_sec:02d} - {end_min:02d}:{end_sec:02d}"

        # 获取发言人名称
        speaker = getattr(u, 'speaker', 'UNKNOWN')
        if speaker_manager:
            speaker = speaker_manager.get_display_name_resolved(speaker)

        # 格式化
        lines.append(f"[{time_str}] **{speaker}**: {u.text}")

    return "\n".join(lines)


def render_speaker_menu(speakers: List[Dict]) -> str:
    """
    渲染发言人选择菜单

    Args:
        speakers: 发言人信息列表

    Returns:
        格式化的菜单文本
    """
    lines = ["请选择发言人：\n"]

    for i, speaker in enumerate(speakers, 1):
        lines.append(f"  [{i}] {speaker['display_name']} ({speaker['id']})")

    lines.append("")
    return "\n".join(lines)
