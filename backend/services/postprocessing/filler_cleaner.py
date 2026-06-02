"""
口癖清理模块
================
清理口语中的无意义重复词和填充词

功能：
- 清理"然后""这个""就是"等口癖
- 压缩重复短语
- 保留有意义的重复强调

使用示例：
    cleaner = FillerWordCleaner()
    cleaned_text = cleaner.clean("然后然后我们就开始")
"""

import re
from typing import List, Set, Dict
import logging

logger = logging.getLogger(__name__)


class FillerWordCleaner:
    """口癖词清理器"""

    # 常见中文口癖词（按清理强度分类）
    FILLER_WORDS = {
        # 强度 1：无意义的填充词（直接删除）
        "strong": [
            "嗯嗯", "啊啊", "呃呃", "那个那个", "就是就是",
            "对对", "是是", "嗯", "啊", "呃", "哦",
        ],
        # 强度 2：可选择性清理的连接词（保留第一个）
        "medium": [
            "然后然后", "然后 然后", "然后  然后",
            "这个这个", "这个 这个",
            "就是就是", "就是 就是",
            "那那个", "那 那",
        ],
        # 强度 3：需要谨慎清理的词（根据上下文判断）
        "weak": [
            "然后", "这个", "就是", "那个", "的话",
            "的话的话", "嗯", "啊",
        ]
    }

    def __init__(self, clean_strength: str = "medium"):
        """
        初始化口癖清理器

        Args:
            clean_strength: 清理强度 (strong/medium/weak)
        """
        self.clean_strength = clean_strength
        self.stats = {
            "filler_removed": 0,
            "repetition_compressed": 0
        }

    def _remove_strong_fillers(self, text: str) -> str:
        """删除无意义的填充词"""
        count = 0
        for filler in self.FILLER_WORDS["strong"]:
            # 只删除独立的词，不删除词的一部分
            pattern = r'\b' + re.escape(filler) + r'\b'
            matches = len(re.findall(pattern, text))
            if matches > 0:
                text = re.sub(pattern, '', text)
                count += matches

        if count > 0:
            logger.info(f"[FillerWordCleaner] 删除了 {count} 个强填充词")
            self.stats["filler_removed"] += count

        return text

    def _compress_medium_fillers(self, text: str) -> str:
        """压缩中等强度的重复词（保留第一个）"""
        count = 0

        # 处理重复的连接词
        replacements = {
            "然后然后": "然后",
            "这个这个": "这个",
            "就是就是": "就是",
            "那个那个": "那个",
            "嗯嗯": "嗯",
            "啊啊": "啊",
        }

        for wrong, right in replacements.items():
            if wrong in text:
                text = text.replace(wrong, right)
                count += 1

        if count > 0:
            logger.info(f"[FillerWordCleaner] 压缩了 {count} 个重复词")
            self.stats["repetition_compressed"] += count

        return text

    def _clean_weak_fillers_selective(self, text: str) -> str:
        """选择性清理弱口癖词（基于上下文）"""
        # 只删除连续重复3次以上的情况
        # 例如："然后然后然后" -> "然后"
        count = 0

        # 检测 2-4 字短语的连续重复（3次以上）
        pattern = r'([一-龥]{2,4}?)(\1{2,})'

        def replace_repeated(match):
            nonlocal count
            repeated_phrase = match.group(1)
            count += 1
            return repeated_phrase  # 只保留一次

        text = re.sub(pattern, replace_repeated, text)

        if count > 0:
            logger.info(f"[FillerWordCleaner] 清理了 {count} 个过度重复")

        return text

    def clean(self, text: str) -> str:
        """
        清理口癖词

        Args:
            text: 待清理的文本

        Returns:
            清理后的文本
        """
        if not text:
            return text

        # 重置统计
        self.stats = {
            "filler_removed": 0,
            "repetition_compressed": 0
        }

        # 根据清理强度选择清理策略
        if self.clean_strength == "strong":
            text = self._remove_strong_fillers(text)
            text = self._compress_medium_fillers(text)
            text = self._clean_weak_fillers_selective(text)
        elif self.clean_strength == "medium":
            text = self._compress_medium_fillers(text)
            text = self._clean_weak_fillers_selective(text)
        else:  # weak
            text = self._clean_weak_fillers_selective(text)

        # 清理多余的空格
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()

        return text

    def clean_turns(self, turns: List[Dict]) -> List[Dict]:
        """
        清理对话轮次中的口癖词

        Args:
            turns: 对话轮次列表

        Returns:
            清理后的对话轮次列表
        """
        cleaned_turns = []
        for turn in turns:
            cleaned_turn = turn.copy()
            original_text = turn.get("text", "")
            cleaned_text = self.clean(original_text)
            cleaned_turn["text"] = cleaned_text
            cleaned_turns.append(cleaned_turn)

        return cleaned_turns

    def get_stats(self) -> Dict:
        """获取清理统计信息"""
        return self.stats.copy()
