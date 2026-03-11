"""
Transcript Refiner Templates - 转录文本精修模板

专门用于修正 ASR 转录中的同音错别字、语气词和断句问题。
包含 Few-shot 示例以引导 LLM 正确处理常见问题。
"""

from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class RefinerExample:
    """Few-shot 示例"""
    original: str
    refined: str
    description: str

    def to_markdown(self) -> str:
        """转换为 Markdown 格式"""
        return f"""**原始**: {self.original}
**修正**: {self.refined}
*说明: {self.description}*"""


# Few-shot 示例库
REFINER_EXAMPLES: List[RefinerExample] = [
    RefinerExample(
        original="蓝哥舞从一个东北的18线骗案的小镇",
        refined="蓝哥我从一个东北的18线偏远小镇",
        description="修正同音错别字：舞→我，骗案→偏远"
    ),
    RefinerExample(
        original="因为家里边穷了然后我当时在带款买车卖房",
        refined="因为家里穷了，所以我当时在贷款买车卖房",
        description="修正同音错别字：带→贷，删除冗余语气词"
    ),
    RefinerExample(
        original="然后当时车带然后签我的亲戚朋友包括建设银行当时有一个消费带",
        refined="当时车贷，然后向亲戚朋友借款，包括建设银行有一个消费贷",
        description="修正同音错别字：带→贷，签→向，添加标点"
    ),
    RefinerExample(
        original="我欠了41.4万然后呢每个月车带房带京东信用卡花杯",
        refined="我欠了**41.4万**，每个月车贷、房贷、京东信用卡花呗",
        description="修正同音错别字，加粗核心数字"
    ),
    RefinerExample(
        original="起这么夸张的标题的但听完今天的课程之后你就会发现",
        refined="起这么夸张的标题，但听完今天的课程之后，你就会发现",
        description="添加标准标点，保持第一人称叙述风格"
    ),
    RefinerExample(
        original="就大家都知道嘛就是今天的课程的内容是支撑着",
        refined="大家都知道嘛，今天的课程内容是支撑着",
        description="删除冗余语气词，保持口语化"
    ),
    RefinerExample(
        original="来自这个平穷的是吧下岗职工在家庭的孩子",
        refined="来自这个贫穷的下岗职工家庭的孩子",
        description="修正错别字，删除冗余词，是吧→（删除）"
    ),
]


def build_few_shot_prompt() -> str:
    """
    构建 Few-shot 示例提示词

    Returns:
        Few-shot 示例的 Markdown 格式字符串
    """
    examples = []

    for i, example in enumerate(REFINER_EXAMPLES, 1):
        examples.append(f"### 示例 {i}")
        examples.append(example.to_markdown())
        examples.append("")

    return "\n".join(examples)


def build_refiner_system_prompt() -> str:
    """
    构建精修系统提示词

    Returns:
        系统提示词字符串
    """
    return """### 角色：专业速记校对员

### 任务：
1. **修正同音错别字**（必须严格对照下表修正）
2. **删除语气词**和无意义的重复（如：就是、那个、然后、呃、是吧）
3. **保持第一人称叙述**，但将语言转化为书面口语（保留亲切感，去除冗余）
4. **识别并加粗核心数字**（如金额、年份、时间、百分比）
5. **添加标准标点符号**，确保语义分段清晰

### 常见同音错别字对照表（必须严格修正）：
| ASR识别错误 | 正确写法 | 语境 |
|------------|----------|------|
| 带/代/待 | 贷 | 贷款、车贷、房贷、消费贷 |
| 偏案/偏偏 | 偏远 | 地点描述 |
| 平穷/频钦 | 贫穷 | 经济状况 |
| 唱吃/偿驰 | 偿债 | 债务相关 |
| 骗案 | 偏远 | 地点描述 |
| 花杯/花费 | 花呗 | 支付宝产品 |
| 车带 | 车贷 | 汽车贷款 |
| 房带 | 房贷 | 住房贷款 |
| 消费带 | 消费贷 | 消费贷款 |
| 签 | 向 | 方向/对象 |
| 舞 | 我 | 第一人称 |
| 是吧（句末） | （删除） | 冗余语气词 |

### 语义分段规则：
- 按照完整语义单元分段，不要在句子中间断开
- 使用中文标准标点：逗号、句号、问号、感叹号
- 逗号用于句内停顿，句号用于完整句子结束
- 问号和感叹号用于疑问和强调语气

### 处理原则：
- **保留说话人的原意和语气**
- **优先修正上述表格中的错别字**
- **数字格式：**金额**、**年份**、**时间**、**百分比**
- **保持叙述连贯性和流畅性**

### 输出格式：
直接输出修正后的完整文本，不要添加任何解释、前缀或后缀。"""


def build_refiner_user_prompt(transcript_text: str) -> str:
    """
    构建精修用户提示词

    Args:
        transcript_text: 原始转录文本

    Returns:
        用户提示词字符串
    """
    return f"""请优化以下转录文本：

## 原始转录
{transcript_text}

## 处理要求
1. 严格按照同音错别字对照表修正
2. 删除冗余语气词（就是、那个、然后、呃、是吧等）
3. 加粗核心数字（金额、年份、时间）
4. 添加标准标点，确保语义分段清晰
5. 保持第一人称叙述风格

## 输出格式
直接输出修正后的文本，不要添加任何解释。"""


# 便捷函数
def get_refiner_prompts(transcript_text: str, include_examples: bool = True) -> Dict[str, str]:
    """
    获取完整的精修提示词

    Args:
        transcript_text: 原始转录文本
        include_examples: 是否包含 Few-shot 示例

    Returns:
        包含 system_prompt 和 user_prompt 的字典
    """
    system_prompt = build_refiner_system_prompt()
    user_prompt = build_refiner_user_prompt(transcript_text)

    if include_examples:
        user_prompt = f"{build_few_shot_prompt()}\n\n{user_prompt}"

    return {
        "system_prompt": system_prompt,
        "user_prompt": user_prompt
    }


if __name__ == "__main__":
    # 测试代码
    print("=== 系统提示词 ===")
    print(build_refiner_system_prompt())
    print("\n=== Few-shot 示例 ===")
    print(build_few_shot_prompt())
