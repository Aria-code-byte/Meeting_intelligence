"""
Enhanced prompt generation module.

优化版本的 Prompt 生成，包含：
1. Few-shot 示例
2. 明确的输出格式约束
3. 角色特定的指令
4. 结构化输出引导
"""

from typing import Dict, Any, Optional

from template.types import UserTemplate, SummaryAngle


# ============================================
# 总结角度的具体指令
# ============================================

ANGLE_INSTRUCTIONS = {
    "towards-conclusions": """**总结角度：偏向结论**

你的总结应该：
- 重点提炼会议的核心结论和最终决策
- 简明扼要，省略详细的讨论过程
- 强调"决定了什么"而非"讨论了什么"
- 直接呈现结果，而非推演过程""",

    "towards-process": """**总结角度：偏向过程**

你的总结应该：
- 详细记录讨论的过程和不同观点
- 保留关键的论证思路和权衡考虑
- 说明"为什么这样决定"以及决策背景
- 记录被否决的方案及其原因""",

    "towards-decisions": """**总结角度：偏向决策**

你的总结应该：
- 突出会议中做出的各项决策
- 说明决策的背景、影响因素和预期效果
- 列出决策的负责人、时间节点和依赖关系
- 区分最终决策、待定决策和需升级的决策""",

    "towards-user-impact": """**总结角度：偏向用户体验**

你的总结应该：
- 关注讨论内容对用户体验的影响
- 强调用户反馈和痛点
- 从用户视角总结会议内容
- 突出对用户的直接影响""",

    "balanced": """**总结角度：平衡型**

你的总结应该：
- 平衡记录过程和结论
- 既要说明讨论了什么，也要说明结论是什么
- 兼顾细节和要点
- 提供足够的上下文和背景"""
}


# ============================================
# Few-shot 示例
# ============================================

FEW_SHOT_EXAMPLE = """
## 示例输出格式

### 产品经理模板示例

## 会议总结
本次会议讨论了用户管理功能的开发计划。团队决定采用 RESTful API 设计，使用 JWT 认证，预计2周内完成基础功能开发。

## 需求要点
- 支持用户注册、登录、密码找回
- 支持角色权限管理（普通用户、管理员）
- 支持用户信息编辑和头像上传
- 需满足等保2.0 安全要求

## 关键决策
- 采用 JWT 作为认证方式，有效期7天
- 密码使用 bcrypt 加密，cost=10
- 暂不支持第三方登录（V2考虑）
- 使用现有用户中心服务，不新建系统

## 行动项
- [张三] 完成API设计文档（本周五前）
- [李四] 搭建数据库表结构和索引（下周一）
- [王五] 编写注册/登录单元测试（下周二）
- [赵六] 准备等保安全审查材料（下周三）
"""


# ============================================
# 主函数
# ============================================

def build_system_prompt_v2(template: UserTemplate) -> str:
    """
    构建系统提示词（优化版）

    Args:
        template: 用户模板

    Returns:
        系统提示词字符串
    """
    lines = []

    # 角色定义
    lines.append(f"你是{template.role}。")
    lines.append("")

    # 总结角度说明
    angle_instruction = ANGLE_INSTRUCTIONS.get(
        template.angle.value,
        ANGLE_INSTRUCTIONS["balanced"]
    )
    lines.append(angle_instruction)
    lines.append("")

    # 重点关注
    if template.focus:
        focus_str = "、".join(template.focus)
        lines.append(f"**重点关注**：{focus_str}")
        lines.append("")

    # 输出原则
    lines.append("**输出原则**：")
    lines.append("- 基于转录内容，不要编造")
    lines.append("- 如果某部分内容不适用，标注「无」而不是省略")
    lines.append("- 使用项目符号（-）列出要点")
    lines.append("- 保持简洁但完整")

    return "\n".join(lines)


def build_user_prompt_v2(
    template: UserTemplate,
    transcript_text: str,
    context: Optional[Dict[str, Any]] = None
) -> str:
    """
    构建用户提示词（优化版）

    Args:
        template: 用户模板
        transcript_text: 转录文本
        context: 额外上下文（可选）

    Returns:
        用户提示词字符串
    """
    lines = []

    # 会议转录内容
    lines.append("# 会议转录内容")
    lines.append("")
    lines.append("```")
    lines.append(transcript_text)
    lines.append("```")
    lines.append("")

    # 输出结构说明
    if template.sections:
        lines.append("# 输出结构")
        lines.append("")
        lines.append("请**严格按照以下结构**输出总结，使用 markdown 二级标题（##）分隔各部分：")
        lines.append("")

        for section in sorted(template.sections, key=lambda s: s.order):
            req_marker = "【必需】" if section.required else "【可选】"
            lines.append(f"## {section.order}. **{section.title}** {req_marker}")
            lines.append(f"{section.prompt}")

            # 添加格式说明
            format_hints = {
                "bullet-points": "格式：使用项目符号列表（-）",
                "paragraph": "格式：使用段落形式",
                "table": "格式：使用表格形式",
                "mixed": "格式：自由混合格式",
            }
            hint = format_hints.get(section.format.value, "")
            if hint:
                lines.append(f"_{{hint}_")

            lines.append("")

    # 补充信息
    if context:
        lines.append("# 补充信息")
        lines.append("")
        if "duration" in context:
            duration = context.get("duration")
            if isinstance(duration, (int, float)):
                duration_str = format_duration(duration)
                lines.append(f"- 会议时长：{duration_str}")
        if "utterance_count" in context:
            lines.append(f"- 语句数量：{context['utterance_count']} 条")
        if "total_words" in context:
            lines.append(f"- 总字数：{context['total_words']} 字")
        lines.append("")

    return "\n".join(lines)


def build_full_prompt_v2(
    template: UserTemplate,
    transcript_text: str,
    context: Optional[Dict[str, Any]] = None,
    include_example: bool = False
) -> Dict[str, str]:
    """
    构建完整的 prompt（system + user）

    Args:
        template: 用户模板
        transcript_text: 转录文本
        context: 额外上下文（可选）
        include_example: 是否包含 Few-shot 示例（默认 False，因为会消耗 tokens）

    Returns:
        包含 system_prompt 和 user_prompt 的字典
    """
    system_prompt = build_system_prompt_v2(template)
    user_prompt = build_user_prompt_v2(template, transcript_text, context)

    # 可选：添加 Few-shot 示例
    if include_example:
        user_prompt = user_prompt + "\n\n" + FEW_SHOT_EXAMPLE

    return {
        "system_prompt": system_prompt,
        "user_prompt": user_prompt
    }


# ============================================
# 辅助函数
# ============================================

def format_duration(seconds: float) -> str:
    """
    格式化时长为人类可读格式

    Args:
        seconds: 时长（秒）

    Returns:
        格式化的时长字符串
    """
    if seconds < 60:
        return f"{int(seconds)}秒"
    elif seconds < 3600:
        minutes = int(seconds / 60)
        secs = int(seconds % 60)
        return f"{minutes}分{secs}秒"
    else:
        hours = int(seconds / 3600)
        minutes = int((seconds % 3600) / 60)
        return f"{hours}小时{minutes}分钟"


def get_angle_description(angle: str) -> str:
    """
    获取总结角度的简短描述

    Args:
        angle: 角度值

    Returns:
        角度描述
    """
    descriptions = {
        "towards-conclusions": "偏向结论型",
        "towards-process": "偏向过程型",
        "towards-decisions": "偏向决策型",
        "towards-user-impact": "偏向用户体验型",
        "balanced": "平衡型"
    }
    return descriptions.get(angle, "自定义")


# ============================================
# 向后兼容的别名（可选）
# ============================================

# 保留原函数名作为兼容层
def create_system_prompt(template: UserTemplate) -> str:
    """向后兼容的函数别名"""
    return build_system_prompt_v2(template)


def create_user_prompt(
    template: UserTemplate,
    transcript_text: str,
    context: Optional[Dict[str, Any]] = None
) -> str:
    """向后兼容的函数别名"""
    return build_user_prompt_v2(template, transcript_text, context)


if __name__ == "__main__":
    # 测试代码
    from template.defaults import get_general_template

    template = get_general_template()

    print("=== 系统提示词 ===")
    print(build_system_prompt_v2(template))
    print("\n=== 用户提示词示例 ===")
    print(build_user_prompt_v2(
        template,
        "今天我们讨论了新功能的开发计划...",
        {"duration": 1800, "utterance_count": 50, "total_words": 1500}
    ))
