"""
热词纠错模块
================
针对 WhisperX 中文专有词错识别的后处理纠错

功能：
- 基于上下文的热词替换
- 避免误替换（只在相邻上下文命中时替换）
- 支持领域特定词表

使用示例：
    corrector = HotwordCorrector()
    corrected_text = corrector.correct("文杰杯宣讲会")
"""

import re
from typing import Dict, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class HotwordCorrector:
    """热词纠错器"""

    # 默认热词表（智能车/竞赛领域 - 扩展版）
    DEFAULT_HOTWORDS: Dict[str, Tuple[str, List[str]]] = {
        # === 文杰杯相关 ===
        "圈鸟会": ("宣讲会", ["比赛", "赛事", "参加", "欢迎"]),
        "圈脚费": ("宣讲会", ["比赛", "赛事", "参加", "欢迎"]),
        "文洁": ("文杰", ["杯", "比赛", "宣讲", "智能车"]),
        "文节": ("文杰", ["杯", "比赛", "宣讲", "智能车"]),
        "文节卑": ("文杰杯", ["智能车", "比赛", "宣讲会"]),
        "运节杯": ("文杰杯", ["智能车", "比赛", "宣讲会"]),
        "子能车": ("智能车", ["比赛", "赛事", "文杰杯"]),
        "条": ("挑战赛", ["文杰", "杯", "智能车", "竞赛"]),

        # === 技术术语 ===
        "飞沿走地": ("飞檐走壁", ["圆筒", "水平面", "电磁", "导线", "赛道"]),
        "飞燕走地": ("飞檐走壁", ["圆筒", "水平面", "电磁", "导线", "赛道"]),
        "飞验走弊": ("飞檐走壁", ["圆筒", "水平面", "电磁", "导线", "赛道"]),
        "飞烟走彼": ("飞檐走壁", ["圆筒", "水平面", "电磁", "导线", "赛道"]),
        "组飞": ("逐飞", ["开源", "库", "学习", "套件", "淘宝", "供应商", "助手"]),
        "组飞助手": ("逐飞助手", ["开源", "库", "学习", "套件"]),
        "组飞开源库": ("逐飞开源库", ["学习", "套件", "供应商"]),
        "除非": ("逐飞", ["开源", "库", "学习", "套件", "淘宝", "供应商", "助手"]),
        "除非助手": ("逐飞助手", ["开源", "库", "学习"]),
        "单品机": ("单片机", ["开发", "嵌入式", "编程", "硬件", "STM32"]),
        "科墓": ("科目", ["考试", "题目", "一", "二", "三", "四"]),
        "科墓一": ("科目一", ["考试", "题目"]),
        "科墓二": ("科目二", ["考试", "题目"]),
        "电磁银脑线": ("电磁引导线", ["赛道", "传感器", "导航", "磁"]),
        "圆统面": ("圆筒面", ["赛道", "坡道", "交接"]),
        "悄悄板面": ("跷跷板面", ["赛道", "坡道", "交接"]),
        "推压吸附": ("负压吸附", ["风扇", "吸附", "壁面", "悬停"]),
        "随压吸附": ("负压吸附", ["风扇", "吸附", "壁面", "悬停"]),

        # === 平台/公司 ===
        "马鸣平台": ("码云平台", ["代码", "托管", "开源", "仓库"]),
        "滑维": ("华为", ["云", "平台", "AI", "计算"]),
        "汉街": ("焊接", ["工艺", "质量", "焊点", "连接"]),

        # === 通用术语 ===
        "通常链路": ("通用链路", ["开源", "代码", "架构", "设计"]),
        "风航链路": ("通用链路", ["开源", "代码", "架构", "设计"]),
        "通房建书": ("通用链路", ["开源", "代码", "架构", "设计"]),
        "艳过流痕": ("焰过流痕", ["焊接", "工艺", "质量"]),
        "指上谈兵": ("纸上谈兵", ["理论", "实践", "空谈"]),
        "PVT": ("PPT", ["演示", "幻灯", "讲义"]),
        "视频交叉": ("十字交叉", ["赛道", "路口", "交叉"]),

        # === 常见错误 ===
        "解评": ("截屏或扫码", ["二维码", "扫码", "加群"]),
        "截评": ("截屏或扫码", ["二维码", "扫码", "加群"])
    }

    def __init__(self, hotwords: Optional[Dict[str, Tuple[str, List[str]]]] = None):
        """
        初始化热词纠错器

        Args:
            hotwords: 自定义热词表，格式为 {错误词: (正确词, [上下文关键词])}
                     如果为 None，使用默认热词表
        """
        self.hotwords = hotwords or self.DEFAULT_HOTWORDS
        self.correction_stats = {
            "total_corrections": 0,
            "corrections_by_word": {}
        }

    def correct(self, text: str, window_size: int = 20) -> str:
        """
        对文本进行热词纠错

        Args:
            text: 待纠错的文本
            window_size: 上下文窗口大小（字符数）

        Returns:
            纠错后的文本
        """
        if not text:
            return text

        corrected_text = text
        corrections_made = []

        for wrong_word, (correct_word, context_keywords) in self.hotwords.items():
            # 查找所有错误词出现的位置
            for match in re.finditer(re.escape(wrong_word), corrected_text):
                start, end = match.span()

                # 提取上下文
                context_start = max(0, start - window_size)
                context_end = min(len(corrected_text), end + window_size)
                context = corrected_text[context_start:context_end]

                # 检查上下文是否包含关键词
                has_context = any(keyword in context for keyword in context_keywords)

                # 只在上下文匹配时替换
                if has_context:
                    corrected_text = corrected_text[:start] + correct_word + corrected_text[end:]
                    corrections_made.append({
                        "wrong": wrong_word,
                        "correct": correct_word,
                        "position": start
                    })
                    # 更新统计
                    self.correction_stats["total_corrections"] += 1
                    self.correction_stats["corrections_by_word"][wrong_word] = \
                        self.correction_stats["corrections_by_word"].get(wrong_word, 0) + 1

        if corrections_made:
            logger.info(f"[HotwordCorrector] 纠正了 {len(corrections_made)} 处热词错误")
            for correction in corrections_made:
                logger.info(f"  '{correction['wrong']}' -> '{correction['correct']}' (位置: {correction['position']})")

        return corrected_text

    def correct_turns(self, turns: List[Dict]) -> List[Dict]:
        """
        对对话轮次进行热词纠错

        Args:
            turns: 对话轮次列表，每个轮次包含 speaker, start, end, text

        Returns:
            纠错后的对话轮次列表
        """
        corrected_turns = []
        for turn in turns:
            corrected_turn = turn.copy()
            original_text = turn.get("text", "")
            corrected_text = self.correct(original_text)
            corrected_turn["text"] = corrected_text
            corrected_turns.append(corrected_turn)

        return corrected_turns

    def add_hotword(self, wrong: str, correct: str, context: List[str]):
        """
        添加自定义热词

        Args:
            wrong: 错误词
            correct: 正确词
            context: 上下文关键词列表
        """
        self.hotwords[wrong] = (correct, context)
        logger.info(f"[HotwordCorrector] 添加热词: '{wrong}' -> '{correct}' (上下文: {context})")

    def remove_hotword(self, wrong: str):
        """
        移除热词

        Args:
            wrong: 要移除的错误词
        """
        if wrong in self.hotwords:
            del self.hotwords[wrong]
            logger.info(f"[HotwordCorrector] 移除热词: '{wrong}'")

    def get_stats(self) -> Dict:
        """
        获取纠错统计信息

        Returns:
            统计信息字典
        """
        return self.correction_stats.copy()

    def reset_stats(self):
        """重置统计信息"""
        self.correction_stats = {
            "total_corrections": 0,
            "corrections_by_word": {}
        }


def create_domain_hotword_dict(domain: str = "smartcar") -> Dict[str, Tuple[str, List[str]]]:
    """
    创建领域特定的热词字典

    Args:
        domain: 领域名称，支持 "smartcar"（智能车）、"general"（通用）

    Returns:
        热词字典
    """
    if domain == "smartcar":
        return HotwordCorrector.DEFAULT_HOTWORDS.copy()
    elif domain == "general":
        return {
            "嗯嗯": ("嗯", []),
            "啊啊": ("啊", []),
            "那个那个": ("那个", []),
        }
    else:
        return {}
