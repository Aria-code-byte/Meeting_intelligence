"""
Transcript Recorder Templates - 转录文本整理模板

专门用于生成"带时间索引的纯净实录"。
角色：专业录音整理员
目标：只纠错，不改为书面语，输出带时间戳的段落
"""

from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class TimeBlock:
    """时间块"""
    start_ms: int  # 起始时间（毫秒）
    end_ms: int  # 结束时间（毫秒）
    text: str  # 原始文本

    @property
    def duration_seconds(self) -> float:
        """时长（秒）"""
        return (self.end_ms - self.start_ms) / 1000.0

    def format_time_range(self) -> str:
        """格式化时间范围为 [MM:SS - MM:SS]"""
        def ms_to_mmss(ms: int) -> str:
            seconds = ms // 1000
            mm = seconds // 60
            ss = seconds % 60
            return f"{mm:02d}:{ss:02d}"

        return f"[{ms_to_mmss(self.start_ms)} - {ms_to_mmss(self.end_ms)}]"


def build_recorder_system_prompt() -> str:
    """
    构建录音整理员系统提示词

    Returns:
        系统提示词字符串
    """
    return """### 角色：专业录音整理员

### 任务：
你是一位专业的录音整理员。你的任务是将语音转文字的原始转录整理成可读的实录文档。

### 核心原则：
1. **只纠错，不改为书面语** - 保持说话人的口语风格和语气
2. **修正同音错别字**（必须严格对照下表修正）
3. **删除冗余语气词**（如：就是、那个、呃、是吧）
4. **保留说话人原意** - 不要添加或删减实质性内容

### 常见同音错别字对照表（必须严格修正）：
| ASR识别错误 | 正确写法 | 语境 |
|------------|----------|------|
| 蓝哥舞 | 蓝哥我 | 主语 |
| 18线骗案 | 18线偏远 | 地点 |
| 偏案/偏偏 | 偏远 | 地点 |
| 带/代/待 | 贷 | 贷款相关 |
| 车带 | 车贷 | 汽车贷款 |
| 房带 | 房贷 | 住房贷款 |
| 消费带 | 消费贷 | 消费贷款 |
| 唱吃 | 偿债 | 债务 |
| 平穷/频钦 | 贫穷 | 经济状况 |
| 花杯/花费 | 花呗 | 支付产品 |
| 签 | 向 | 方向/对象 |
| 是吧（句末） | （删除） | 冗余词 |
| 舞 | 我 | 第一人称 |

### 输出格式：
直接输出整理后的文本，不要添加任何解释、前缀或后缀。

### 重要提醒：
- 保持口语化，不要改成书面语
- 只删除冗余语气词，保留说话人的表达习惯
- 严格修正同音错别字
- 添加标准标点符号，确保语义清晰"""


def build_recorder_user_prompt(transcript_text: str) -> str:
    """
    构建录音整理员用户提示词

    Args:
        transcript_text: 原始转录文本

    Returns:
        用户提示词字符串
    """
    return f"""请整理以下转录文本：

## 原始转录
{transcript_text}

## 处理要求
1. 严格按照同音错别字对照表修正（如：蓝哥舞→蓝哥我、骗案→偏远、车带→车贷）
2. 删除冗余语气词（就是、那个、然后、呃、是吧等）
3. 保持口语化风格，不要改成书面语
4. 添加标准标点符号
5. 保持说话人的原意和语气

## 输出格式
直接输出整理后的文本，不要添加任何解释。"""


# 便捷函数
def get_recorder_prompts(transcript_text: str) -> Dict[str, str]:
    """
    获取完整的录音整理提示词

    Args:
        transcript_text: 原始转录文本

    Returns:
        包含 system_prompt 和 user_prompt 的字典
    """
    return {
        "system_prompt": build_recorder_system_prompt(),
        "user_prompt": build_recorder_user_prompt(transcript_text)
    }


def format_time_blocks(blocks: List[TimeBlock], refined_texts: List[str]) -> str:
    """
    格式化时间块为带时间戳的实录文档

    Args:
        blocks: 时间块列表
        refined_texts: 对应的整理后文本列表

    Returns:
        格式化后的实录文档
    """
    if len(blocks) != len(refined_texts):
        raise ValueError(f"块数量({len(blocks)})与文本数量({len(refined_texts)})不匹配")

    lines = []
    for block, refined_text in zip(blocks, refined_texts):
        time_range = block.format_time_range()
        lines.append(f"{time_range} {refined_text}")

    return "\n\n".join(lines)


def ms_to_mmss(ms: int) -> str:
    """
    将毫秒转换为 MM:SS 格式

    Args:
        ms: 毫秒数

    Returns:
        格式化后的时间字符串 (MM:SS)
    """
    seconds = ms // 1000
    mm = seconds // 60
    ss = seconds % 60
    return f"{mm:02d}:{ss:02d}"


if __name__ == "__main__":
    # 测试代码
    print("=== 系统提示词 ===")
    print(build_recorder_system_prompt())
    print("\n=== 时间块格式化测试 ===")
    test_block = TimeBlock(start_ms=0, end_ms=60000, text="测试文本")
    print(f"时间范围: {test_block.format_time_range()}")
    print(f"时长: {test_block.duration_seconds}秒")
