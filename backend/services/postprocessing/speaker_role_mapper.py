"""
发言人角色映射模块
===================
将 WhisperX 的 SPEAKER_00/01 映射为实际角色（主持人/主讲人等）

功能：
- 基于上下文规则自动识别角色
- 支持自定义映射规则
- 生成带时间戳的可读转录文本

使用示例：
    mapper = SpeakerRoleMapper()
    mapped_turns = mapper.map_roles(turns)
    readable_text = mapper.format_readable(mapped_turns)
"""

import re
from typing import Dict, List, Optional, Tuple
import logging
from datetime import timedelta

logger = logging.getLogger(__name__)


class SpeakerRoleMapper:
    """发言人角色映射器"""

    # 默认角色识别规则
    DEFAULT_RULES = {
        "主持人": {
            "keywords": ["能听到吗", "我们差不多开始", "欢迎各位", "宣讲会", "大家好",
                        "首先欢迎", "接下来我们", "开始吧", "差不多开始"],
            "position_hint": "first",  # 优先在开头识别
            "min_duration": 0
        },
        "主讲人": {
            "keywords": ["各位老师", "各位同学", "大家下午好", "介绍一下", "比赛规则",
                        "赛事介绍", "智能车", "挑战赛", "文杰杯", "技术细节"],
            "position_hint": "any",
            "min_duration": 30  # 主讲人通常发言较长
        },
        "嘉宾": {
            "keywords": ["梁医学长", "学长", "接下来由", "介绍"],
            "position_hint": "any",
            "min_duration": 10
        },
        "提问者": {
            "keywords": ["请问", "问题", "想问", "怎么", "为什么", "?", "？"],
            "position_hint": "any",
            "min_duration": 0
        }
    }

    def __init__(self, custom_rules: Optional[Dict] = None):
        """
        初始化角色映射器

        Args:
            custom_rules: 自定义角色识别规则
        """
        self.rules = custom_rules or self.DEFAULT_RULES
        self.speaker_role_map: Dict[str, str] = {}
        self.role_counter: Dict[str, int] = {}

    def _reset_counters(self):
        """重置角色计数器"""
        self.speaker_role_map = {}
        self.role_counter = {role: 0 for role in self.rules}

    def _detect_role_from_text(self, text: str, position_hint: str = "any") -> Optional[str]:
        """
        从文本中检测角色

        Args:
            text: 发言文本
            position_hint: 位置提示 (first/any)

        Returns:
            检测到的角色，如果未检测到返回 None
        """
        for role, rule in self.rules.items():
            # 检查位置提示
            if rule["position_hint"] == "first" and position_hint != "first":
                continue

            # 检查关键词
            for keyword in rule["keywords"]:
                if keyword in text:
                    return role

        return None

    def _assign_role_to_speaker(self, speaker_id: str, role: str):
        """
        为说话人分配角色

        Args:
            speaker_id: 说话人 ID (如 SPEAKER_00)
            role: 角色名称
        """
        # 如果该说话人已有角色，不覆盖（除非是更具体的角色）
        if speaker_id in self.speaker_role_map:
            existing_role = self.speaker_role_map[speaker_id]
            # 角色优先级：主持人 > 主讲人 > 嘉宾 > 提问者
            role_priority = {"主持人": 4, "主讲人": 3, "嘉宾": 2, "提问者": 1}
            if role_priority.get(role, 0) <= role_priority.get(existing_role, 0):
                return

        self.speaker_role_map[speaker_id] = role
        self.role_counter[role] = self.role_counter.get(role, 0) + 1
        logger.info(f"[SpeakerRoleMapper] {speaker_id} -> {role}")

    def map_roles(self, turns: List[Dict]) -> List[Dict]:
        """
        为对话轮次映射角色

        Args:
            turns: 对话轮次列表，每个轮次包含 speaker, start, end, text

        Returns:
            添加了 role 字段的对话轮次列表
        """
        self._reset_counters()
        result_turns = []

        # 第一遍：检测角色
        for i, turn in enumerate(turns):
            speaker = turn.get("speaker", "UNKNOWN")
            text = turn.get("text", "")
            start = turn.get("start", 0)
            end = turn.get("end", 0)
            duration = end - start

            # 确定位置提示
            position_hint = "first" if i < 3 else "any"

            # 检测角色
            detected_role = self._detect_role_from_text(text, position_hint)

            # 检查发言时长是否符合角色预期
            if detected_role:
                min_duration = self.rules[detected_role]["min_duration"]
                if duration >= min_duration:
                    self._assign_role_to_speaker(speaker, detected_role)

        # 第二遍：处理未识别的说话人
        for speaker in self.speaker_role_map:
            if self.speaker_role_map[speaker] == "UNKNOWN":
                # 根据发言量和出现顺序分配默认角色
                if self.role_counter.get("主讲人", 0) == 0:
                    self.speaker_role_map[speaker] = "主讲人"
                elif self.role_counter.get("嘉宾", 0) == 0:
                    self.speaker_role_map[speaker] = "嘉宾"
                else:
                    self.speaker_role_map[speaker] = "参会者"

        # 第三遍：为每个 turn 添加角色信息
        for turn in turns:
            speaker = turn.get("speaker", "UNKNOWN")
            role = self.speaker_role_map.get(speaker, "参会者")

            result_turn = turn.copy()
            result_turn["role"] = role
            result_turns.append(result_turn)

        logger.info(f"[SpeakerRoleMapper] 角色映射完成: {self.role_counter}")
        return result_turns

    def format_readable(self, turns: List[Dict], include_timestamp: bool = True) -> str:
        """
        格式化为可读的转录文本

        Args:
            turns: 对话轮次列表
            include_timestamp: 是否包含时间戳

        Returns:
            格式化的转录文本
        """
        lines = []

        for turn in turns:
            speaker = turn.get("speaker", "UNKNOWN")
            role = turn.get("role", "参会者")
            text = turn.get("text", "").strip()
            start = turn.get("start", 0)
            end = turn.get("end", 0)

            if not text:
                continue

            # 格式化时间戳
            if include_timestamp:
                start_ts = self._format_timestamp(start)
                end_ts = self._format_timestamp(end)
                timestamp = f"[{start_ts} - {end_ts}] "
            else:
                timestamp = ""

            # 格式化行
            line = f"{timestamp}{role}：{text}"
            lines.append(line)

        return "\n\n".join(lines)

    def _format_timestamp(self, seconds: float) -> str:
        """
        格式化时间戳为 HH:MM:SS

        Args:
            seconds: 秒数

        Returns:
            格式化的时间戳
        """
        td = timedelta(seconds=int(seconds))
        hours, remainder = divmod(td.seconds, 3600)
        minutes, secs = divmod(remainder, 60)

        # 如果超过1小时，显示小时
        if td.days > 0 or hours > 0:
            return f"{td.days * 24 + hours:02d}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes:02d}:{secs:02d}"

    def get_role_mapping(self) -> Dict[str, str]:
        """
        获取说话人到角色的映射

        Returns:
            映射字典 {speaker_id: role}
        """
        return self.speaker_role_map.copy()

    def add_custom_rule(self, role: str, keywords: List[str],
                       position_hint: str = "any", min_duration: int = 0):
        """
        添加自定义角色识别规则

        Args:
            role: 角色名称
            keywords: 关键词列表
            position_hint: 位置提示 (first/any)
            min_duration: 最小发言时长（秒）
        """
        self.rules[role] = {
            "keywords": keywords,
            "position_hint": position_hint,
            "min_duration": min_duration
        }
        logger.info(f"[SpeakerRoleMapper] 添加自定义规则: {role}")

    def merge_speakers_by_role(self, turns: List[Dict]) -> List[Dict]:
        """
        按角色合并相邻的对话轮次

        Args:
            turns: 对话轮次列表

        Returns:
            合并后的对话轮次列表
        """
        if not turns:
            return turns

        merged_turns = []
        current_turn = None

        for turn in turns:
            role = turn.get("role", "参会者")
            speaker = turn.get("speaker", "UNKNOWN")
            text = turn.get("text", "")
            start = turn.get("start", 0)
            end = turn.get("end", 0)

            if current_turn is None:
                current_turn = turn.copy()
                continue

            # 检查是否可以合并（同一角色且同一说话人）
            if (current_turn.get("role") == role and
                current_turn.get("speaker") == speaker and
                end - current_turn.get("end", 0) < 3.0):  # 间隔小于3秒
                # 合并文本
                current_turn["text"] += " " + text
                current_turn["end"] = end
            else:
                # 不能合并，保存当前 turn
                merged_turns.append(current_turn)
                current_turn = turn.copy()

        # 添加最后一个 turn
        if current_turn:
            merged_turns.append(current_turn)

        logger.info(f"[SpeakerRoleMapper] 合并 {len(turns)} -> {len(merged_turns)} 个轮次")
        return merged_turns
