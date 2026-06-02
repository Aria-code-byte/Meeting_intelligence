"""
繁简体统一模块
================
统一繁体字和异体字为简体标准字形

功能：
- 繁体转简体
- 异体字统一
- 地区用词统一

使用示例：
    normalizer = TraditionalSimplifiedNormalizer()
    normalized_text = normalizer.normalize("記憶體")
"""

import logging
from typing import Dict, List

logger = logging.getLogger(__name__)


class TraditionalSimplifiedNormalizer:
    """繁简体统一器"""

    # 常见繁简对应表（会议场景高频词）
    TRADITIONAL_SIMPLIFIED_MAP = {
        # === 技术术语 ===
        "記憶體": "内存",
        "記憶": "记忆",
        "運算": "运算",
        "運行": "运行",
        "網路": "网络",
        "網絡": "网络",
        "程式": "程序",
        "編程": "编程",
        "編寫": "编写",
        "資料": "数据",
        "數據": "数据",
        "電腦": "电脑",
        "計算": "计算",
        "處理器": "处理器",
        "處理": "处理",
        "連接": "连接",
        "連線": "连线",
        "設定": "设置",
        "設置": "设置",
        "配置": "配置",
        "製作": "制作",
        "製造": "制造",
        "影像": "视频",
        "圖像": "图像",
        "圖片": "图片",
        "畫面": "画面",
        "顯示": "显示",
        "顯示器": "显示器",
        "視頻": "视频",
        "視訊": "视频",
        "音訊": "音频",
        "音頻": "音频",
        "傳輸": "传输",
        "傳送": "传输",
        "接收": "接收",
        "輸出": "输出",
        "輸入": "输入",
        "檔案": "文件",
        "檔": "文件",

        # === 标点符号 ===
        "，": ",",
        "。": ".",
        "！": "!",
        "？": "?",
        "：": ":",
        "；": ";",
        "（": "(",
        "）": ")",
        "【": "[",
        "】": "]",
        "「": """,
        "」": """,
        "『": "'",
        "』": "'",

        # === 常见异体字 ===
        "佈局": "布局",
        "佈署": "部署",
        "佈线": "布线",
        "佈置": "布置",
        "拼音": "拼音",
        "注音": "注音",
        "迴路": "回路",
        "组件": "组件",
        "元件": "元件",
        "介面": "界面",
        "接口": "接口",
        "机": "机",
        "機": "机",
        "車": "车",
        "車": "车",
    }

    # 智能车竞赛术语表
    SMARTCAR_TERMS = {
        "智慧型": "智能",
        "智慧車": "智能车",
        "感測器": "传感器",
        "感應器": "传感器",
        "導引": "引导",
        "引導": "引导",
        "賽道": "赛道",
        "賽事": "赛事",
        "競賽": "竞赛",
        "比賽": "比赛",
        "選手": "选手",
        "選項": "选项",
        "評分": "评分",
        "評判": "裁判",
        "評審": "评审",
        "計畫": "计划",
        "計算": "计算",
        "計時": "计时",
        "測試": "测试",
        "檢測": "检测",
        "檢查": "检查",
        "驗證": "验证",
        "確認": "确认",
        "標誌": "标志",
        "標記": "标记",
        "識別": "识别",
        "辨識": "识别",
        "編譯": "编译",
        "編碼": "编码",
        "解碼": "解码",
        "壓縮": "压缩",
        "壓力": "压力",
        "閉環": "闭环",
        "迴圈": "循环",
        "迴路": "回路",
    }

    def __init__(self, include_smartcar_terms: bool = True):
        """
        初始化繁简体统一器

        Args:
            include_smartcar_terms: 是否包含智能车竞赛术语
        """
        self.char_map = self.TRADITIONAL_SIMPLIFIED_MAP.copy()
        if include_smartcar_terms:
            self.char_map.update(self.SMARTCAR_TERMS)

        self.stats = {
            "replacements_count": 0,
            "replacements_by_term": {}
        }

    def normalize(self, text: str) -> str:
        """
        统一繁简体

        Args:
            text: 待统一文本

        Returns:
            统一后的文本
        """
        if not text:
            return text

        # 重置统计
        self.stats = {
            "replacements_count": 0,
            "replacements_by_term": {}
        }

        normalized_text = text

        # 按词长降序替换（避免部分匹配问题）
        sorted_terms = sorted(self.char_map.items(), key=lambda x: len(x[0]), reverse=True)

        for traditional, simplified in sorted_terms:
            if traditional in normalized_text:
                count = normalized_text.count(traditional)
                normalized_text = normalized_text.replace(traditional, simplified)

                # 更新统计
                self.stats["replacements_count"] += count
                self.stats["replacements_by_term"][traditional] = \
                    self.stats["replacements_by_term"].get(traditional, 0) + count

        if self.stats["replacements_count"] > 0:
            logger.info(f"[TraditionalSimplifiedNormalizer] 统一了 {self.stats['replacements_count']} 处繁简")

        return normalized_text

    def normalize_turns(self, turns: List[Dict]) -> List[Dict]:
        """
        统一对话轮次的繁简体

        Args:
            turns: 对话轮次列表

        Returns:
            统一后的对话轮次列表
        """
        normalized_turns = []
        for turn in turns:
            normalized_turn = turn.copy()
            original_text = turn.get("text", "")
            normalized_text = self.normalize(original_text)
            normalized_turn["text"] = normalized_text
            normalized_turns.append(normalized_turn)

        return normalized_turns

    def get_stats(self) -> Dict:
        """获取统计信息"""
        return self.stats.copy()

    def add_custom_mapping(self, traditional: str, simplified: str):
        """
        添加自定义繁简对应

        Args:
            traditional: 繁体/异体形式
            simplified: 简体标准形式
        """
        self.char_map[traditional] = simplified
        logger.info(f"[TraditionalSimplifiedNormalizer] 添加映射: '{traditional}' -> '{simplified}'")
