# 模板管理临时补丁 - 添加到 backend/main.py

# 在 backend/main.py 中找到 "# ============================================================
# 5. 模板管理模块
# =============================================================" 之后添加以下代码

@app.get("/api/templates")
async def get_templates():
    """
    获取所有模板列表

    Returns:
        templates: 模板列表
        message: 成功信息
    """
    # 返回前端Mock模板列表
    templates = [
        {
            "id": "general_meeting",
            "name": "通用会议纪要",
            "description": "适合大多数会议场景，包含摘要、决策与待办事项",
            "category": "default",
            "sections": ["会议摘要", "关键讨论", "决策结论", "待办事项"],
            "prompt": "请总结本次会议，重点关注会议摘要、关键讨论内容、决策结论和待办事项。",
            "output_format": "markdown",
            "is_builtin": True
        },
        {
            "id": "weekly_meeting",
            "name": "周会总结",
            "description": "适合团队周会，包含本周成果、问题与下周计划",
            "category": "team",
            "sections": ["本周亮点", "遇到的问题", "下周计划"],
            "prompt": "请从团队协作视角总结周会，重点关注本周成果、遇到的问题和解决方案、下周重点工作。",
            "output_format": "markdown",
            "is_builtin": True
        },
        {
            "id": "project_review",
            "name": "项目评审",
            "description": "适合项目阶段评审，包含进展、风险与计划",
            "category": "project",
            "sections": ["项目进展", "关键里程碑", "风险评估", "下一步计划"],
            "prompt": "请从项目管理视角总结项目评审会议，重点关注项目进展、潜在风险和下一步行动计划。",
            "output_format": "markdown",
            "is_builtin": True
        },
        {
            "id": "customer_communication",
            "name": "客户沟通",
            "description": "适合客户会议，包含需求、方案与跟进",
            "category": "sales",
            "sections": ["客户需求", "业务场景", "方案讨论", "下一步行动"],
            "prompt": "请从客户成功视角总结客户沟通会议，重点关注客户需求、产品匹配度和后续跟进事项。",
            "output_format": "markdown",
            "is_builtin": True
        },
        {
            "id": "sales_meeting",
            "name": "销售会议",
            "description": "适合销售团队会议，包含目标、策略与行动",
            "category": "sales",
            "sections": ["销售目标", "市场分析", "销售策略", "行动计划"],
            "prompt": "请从销售管理视角总结销售会议，重点关注销售目标、市场分析和销售策略。",
            "output_format": "markdown",
            "is_builtin": True
        },
        {
            "id": "interview_record",
            "name": "面试记录",
            "description": "适合面试评估，包含背景、能力与评价",
            "category": "hr",
            "sections": ["候选人背景", "能力评估", "综合评价"],
            "prompt": "请从HR视角总结面试，重点关注候选人的专业能力、软技能和综合评价。",
            "output_format": "markdown",
            "is_builtin": True
        },
        {
            "id": "product_requirement",
            "name": "产品需求讨论",
            "description": "从产品经理视角总结需求、用户价值、风险和后续计划",
            "category": "product",
            "sections": ["核心需求", "用户价值", "讨论重点", "技术风险", "待办事项", "最终决策"],
            "prompt": "请从产品经理视角总结本次会议，重点关注需求分析、用户价值、可行性、技术风险和后续行动计划。",
            "output_format": "markdown",
            "is_builtin": True
        },
        {
            "id": "project_retrospective",
            "name": "项目复盘",
            "description": "适合项目结束复盘，包含成果、问题与改进",
            "category": "project",
            "sections": ["项目成果", "成功经验", "遇到的问题", "改进建议"],
            "prompt": "请从项目复盘视角总结会议，重点关注项目成果、经验教训和改进建议。",
            "output_format": "markdown",
            "is_builtin": True
        }
    ]

    return {
        "success": True,
        "templates": templates,
        "message": "获取成功"
    }

@app.get("/api/templates/{template_id}")
async def get_template_detail(template_id: str):
    """
    获取单个模板详情

    Args:
        template_id: 模板 ID

    Returns:
        template: 模板详情
    """
    # 先获取所有模板
    all_templates_result = await get_templates()
    all_templates = all_templates_result["templates"]

    # 查找指定模板
    template = next((t for t in all_templates if t["id"] == template_id), None)

    if not template:
        return {
            "success": False,
            "message": "模板不存在"
        }

    return {
        "success": True,
        "template": template,
        "message": "获取成功"
    }
