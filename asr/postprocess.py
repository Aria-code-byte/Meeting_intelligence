"""
ASR 后处理校正模块

处理 Whisper ASR 的常见错误，提高转写质量：
1. 同音字/错别字校正
2. 专有名词识别和大小写修正
3. 标点符号优化
4. 口语填充词清理
5. 数字/单位格式化
"""

import re
from pathlib import Path
from typing import List, Dict, Optional

from asr.types import Utterance


# ============================================
# 常见错别字和口语词映射表
# ============================================

# 常见口语填充词（可以删除）
FILLER_WORDS = [
    "那个", "然后那个", "嗯", "啊", "呃",
    "就是", "就是那个", "对吧", "的话",
    "嗯嗯", "啊啊", "呃呃",
]

# 常见同音字/错别字校正
COMMON_CORRECTIONS = {
    # 数字/单位
    "一块": "1元",
    "两块": "2元",
    "十块": "10元",

    # 常见错别字
    "咱们": "我们",
    "咋们": "我们",
    "人家": "他人",

    # 技术词汇（常见错误）
    "微服务": "微服务",
    "前后端": "前后端",
    "前端": "前端",
    "后端": "后端",
    "接口": "接口",
    "数据库": "数据库",

    # 保留原有正确的词
}

# 专有名词默认字典（可被配置覆盖）
DEFAULT_PROPER_NOUNS = {
    # 公司/产品
    "github": "GitHub",
    "gitlab": "GitLab",
    "docker": "Docker",
    "kubernetes": "Kubernetes",
    "k8s": "K8s",
    "aws": "AWS",
    "azure": "Azure",
    "gcp": "GCP",

    # 技术栈
    "react": "React",
    "vue": "Vue",
    "angular": "Angular",
    "typescript": "TypeScript",
    "javascript": "JavaScript",
    "python": "Python",
    "java": "Java",
    "golang": "Go",
    "rust": "Rust",

    # 框架/库
    "django": "Django",
    "flask": "Flask",
    "fastapi": "FastAPI",
    "spring": "Spring",
    "express": "Express",
    "vite": "Vite",
    "webpack": "Webpack",

    # 工具
    "git": "Git",
    "nginx": "Nginx",
    "redis": "Redis",
    "mysql": "MySQL",
    "postgresql": "PostgreSQL",
    "mongodb": "MongoDB",
    "postgresql": "PostgreSQL",

    # 通讯工具
    "slack": "Slack",
    "teams": "Microsoft Teams",
    "zoom": "Zoom",
    "tencent meeting": "腾讯会议",
    "dingtalk": "钉钉",
    "feishu": "飞书",
    "lark": "Lark",
}

# 数字/单位正则模式
NUMBER_PATTERNS = [
    (r'(\d+)块钱', r'\1元'),
    (r'(\d+)块', r'\1元'),
    (r'(\d+)k\b', r'\1K'),  # 10k -> 10K
    (r'(\d+)K\b', r'\1K'),
    (r'(\d+)M\b', r'\1M'),
    (r'(\d+)G\b', r'\1G'),
]

# 中文数字转阿拉伯数字（可选）
CHINESE_NUMBERS = {
    "一": "1", "二": "2", "三": "3", "四": "4", "五": "5",
    "六": "6", "七": "7", "八": "8", "九": "9", "十": "10",
    "零": "0", "两": "2",
}


# ============================================
# 后处理器类
# ============================================

class TranscriptPostProcessor:
    """
    转录后处理器

    应用一系列校正规则来提高 ASR 输出质量。
    """

    def __init__(
        self,
        custom_corrections: Optional[Dict[str, str]] = None,
        custom_nouns: Optional[Dict[str, str]] = None,
        remove_filler_words: bool = True,
        normalize_numbers: bool = True
    ):
        """
        初始化后处理器

        Args:
            custom_corrections: 自定义错别字映射
            custom_nouns: 自定义专有名词映射
            remove_filler_words: 是否删除口语填充词
            normalize_numbers: 是否规范化数字格式
        """
        # 合并自定义配置
        self.corrections = {**COMMON_CORRECTIONS, **(custom_corrections or {})}
        self.nouns = {**DEFAULT_PROPER_NOUNS, **(custom_nouns or {})}
        self.remove_filler_words = remove_filler_words
        self.normalize_numbers = normalize_numbers

        # 预编译正则表达式以提高性能
        self._number_patterns = [
            (re.compile(pattern, re.IGNORECASE), replacement)
            for pattern, replacement in NUMBER_PATTERNS
        ]

        # 预编译专有名词匹配模式（不区分大小写）
        self._noun_patterns = [
            (re.compile(re.escape(wrong), re.IGNORECASE), right)
            for wrong, right in self.nouns.items()
        ]

    def correct_utterance(self, utterance: Utterance) -> Utterance:
        """
        校正单条语句

        Args:
            utterance: 原始语句

        Returns:
            校正后的语句，如果文本为空则返回 None
        """
        text = utterance.text

        # 1. 删除口语填充词
        if self.remove_filler_words:
            text = self._remove_filler_words(text)

        # 2. 应用常见错别字校正
        text = self._apply_corrections(text)

        # 3. 专有名词大小写修正
        text = self._correct_proper_nouns(text)

        # 4. 数字/单位格式化
        if self.normalize_numbers:
            text = self._normalize_numbers(text)

        # 5. 清理多余空格和空白
        text = self._clean_whitespace(text)

        # 6. 检查文本是否为空
        if not text:
            return None

        # 返回新对象（保持原始时间戳）
        return Utterance(
            start=utterance.start,
            end=utterance.end,
            text=text
        )

    def correct_transcript(
        self,
        utterances: List[Utterance]
    ) -> List[Utterance]:
        """
        校正完整转录

        Args:
            utterances: 原始识别结果列表

        Returns:
            校正后的识别结果列表（过滤掉空文本）
        """
        result = []
        for u in utterances:
            corrected = self.correct_utterance(u)
            if corrected is not None:  # 跳过被过滤掉的语句
                result.append(corrected)
        return result

    def _remove_filler_words(self, text: str) -> str:
        """删除口语填充词"""
        for filler in FILLER_WORDS:
            # 使用单词边界避免误删
            pattern = r'\b' + re.escape(filler) + r'\b'
            text = re.sub(pattern, '', text)
        return text

    def _apply_corrections(self, text: str) -> str:
        """应用常见错别字校正"""
        for wrong, right in self.corrections.items():
            if right:  # 如果替换为空则删除
                text = text.replace(wrong, right)
            else:
                text = text.replace(wrong, "")
        return text

    def _correct_proper_nouns(self, text: str) -> str:
        """修正专有名词大小写"""
        for pattern, correct in self._noun_patterns:
            text = pattern.sub(correct, text)
        return text

    def _normalize_numbers(self, text: str) -> str:
        """规范化数字/单位格式"""
        for pattern, replacement in self._number_patterns:
            text = pattern.sub(replacement, text)
        return text

    def _clean_whitespace(self, text: str) -> str:
        """清理多余空白"""
        # 多个空格压缩为一个
        text = re.sub(r' +', ' ', text)
        # 多个换行压缩为一个
        text = re.sub(r'\n+', '\n', text)
        # 删除首尾空白
        text = text.strip()
        return text


# ============================================
# 配置加载
# ============================================

def load_proper_nouns_config(path: Optional[str] = None) -> Dict[str, str]:
    """
    从 YAML 文件加载专有名词配置

    Args:
        path: 配置文件路径，默认为 data/proper_nouns.yaml

    Returns:
        专有名词字典
    """
    if path is None:
        path = Path(__file__).parent.parent / "data" / "proper_nouns.yaml"

    config_path = Path(path)
    if not config_path.exists():
        return {}

    try:
        import yaml
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}
    except ImportError:
        # 如果没有安装 yaml，返回空字典
        return {}
    except Exception:
        return {}

    # 合并所有类别
    nouns = {}
    if isinstance(config, dict):
        for category in config.values():
            if isinstance(category, dict):
                nouns.update(category)

    return nouns


def load_corrections_config(path: Optional[str] = None) -> Dict[str, str]:
    """
    从 YAML 文件加载错别字校正配置

    Args:
        path: 配置文件路径

    Returns:
        错别字映射字典
    """
    if path is None:
        path = Path(__file__).parent.parent / "data" / "corrections.yaml"

    config_path = Path(path)
    if not config_path.exists():
        return {}

    try:
        import yaml
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    except Exception:
        return {}


# ============================================
# 默认处理器（单例）
# ============================================

_default_processor: Optional[TranscriptPostProcessor] = None


def get_processor() -> TranscriptPostProcessor:
    """
    获取默认后处理器（单例）

    处理器会自动加载配置文件（如果存在）。
    """
    global _default_processor

    if _default_processor is None:
        # 尝试加载自定义配置
        custom_nouns = load_proper_nouns_config()
        custom_corrections = load_corrections_config()

        _default_processor = TranscriptPostProcessor(
            custom_nouns=custom_nouns if custom_nouns else None,
            custom_corrections=custom_corrections if custom_corrections else None
        )

    return _default_processor


def postprocess_transcript(
    utterances: List[Utterance],
    processor: Optional[TranscriptPostProcessor] = None
) -> List[Utterance]:
    """
    后处理转录结果（便捷函数）

    Args:
        utterances: 原始识别结果
        processor: 自定义处理器（可选，默认使用全局单例）

    Returns:
        校正后的识别结果
    """
    if processor is None:
        processor = get_processor()

    return processor.correct_transcript(utterances)


# ============================================
# 测试/验证函数
# ============================================

def demonstrate_corrections():
    """演示校正效果"""
    test_cases = [
        "那个我们用docker部署到k8s上",
        "然后那个github上的代码需要更新",
        "大概需要十块钱左右",
        "react和vue都可以用",
        "就是这个问题我们已经讨论过了",
    ]

    processor = TranscriptPostProcessor()

    print("ASR 后处理演示:")
    print("=" * 60)

    for original in test_cases:
        corrected = processor.correct_utterance(
            Utterance(start=0.0, end=5.0, text=original)
        ).text

        print(f"原文: {original}")
        print(f"校正: {corrected}")
        print()


if __name__ == "__main__":
    demonstrate_corrections()
