"""
Default template library.

提供预定义的默认模板，覆盖常见角色和使用场景。
"""

from template.types import UserTemplate, TemplateSection, SummaryAngle, OutputFormat


def get_product_manager_template() -> UserTemplate:
    """产品经理默认模板"""
    return UserTemplate(
        name="product-manager",
        role="Product Manager",
        angle=SummaryAngle.TOWARDS_CONCLUSIONS,
        focus=["requirements", "features", "decisions", "action-items", "risks"],
        description="适合产品经理的模板，关注需求、功能、决策和行动项",
        sections=[
            TemplateSection(
                id="summary",
                title="会议总结",
                prompt="请用2-3句话总结这次会议的核心内容",
                required=True,
                format=OutputFormat.PARAGRAPH,
                order=1
            ),
            TemplateSection(
                id="requirements",
                title="需求要点",
                prompt="提取会议中讨论的产品需求，包括新需求、需求变更和需求澄清",
                required=True,
                format=OutputFormat.BULLET_POINTS,
                order=2
            ),
            TemplateSection(
                id="decisions",
                title="关键决策",
                prompt="列出会议中做出的重要决策，包括决策背景和结论",
                required=True,
                format=OutputFormat.BULLET_POINTS,
                order=3
            ),
            TemplateSection(
                id="action-items",
                title="行动项",
                prompt="列出需要跟进的行动项，包括负责人和预期完成时间",
                required=True,
                format=OutputFormat.BULLET_POINTS,
                order=4
            ),
            TemplateSection(
                id="risks",
                title="风险与问题",
                prompt="识别会议中提到的风险、隐患或待解决问题",
                required=False,
                format=OutputFormat.BULLET_POINTS,
                order=5
            )
        ],
        is_default=True
    )


def get_developer_template() -> UserTemplate:
    """开发者默认模板"""
    return UserTemplate(
        name="developer",
        role="Developer",
        angle=SummaryAngle.TOWARDS_PROCESS,
        focus=["technical-decisions", "implementation", "architecture", "bugs"],
        description="适合开发者的模板，关注技术细节、实现方案和架构决策",
        sections=[
            TemplateSection(
                id="summary",
                title="技术概述",
                prompt="简要概括会议讨论的技术主题",
                required=True,
                format=OutputFormat.PARAGRAPH,
                order=1
            ),
            TemplateSection(
                id="technical-discussion",
                title="技术讨论",
                prompt="详细记录技术讨论内容，包括不同观点和技术权衡",
                required=True,
                format=OutputFormat.BULLET_POINTS,
                order=2
            ),
            TemplateSection(
                id="implementation",
                title="实现方案",
                prompt="总结确定的技术实现方案和关键步骤",
                required=True,
                format=OutputFormat.BULLET_POINTS,
                order=3
            ),
            TemplateSection(
                id="architecture",
                title="架构决策",
                prompt="记录影响系统架构的重要决策",
                required=False,
                format=OutputFormat.BULLET_POINTS,
                order=4
            ),
            TemplateSection(
                id="bugs",
                title="Bug 与问题",
                prompt="列出讨论到的 bug 或技术问题",
                required=False,
                format=OutputFormat.BULLET_POINTS,
                order=5
            )
        ],
        is_default=True
    )


def get_designer_template() -> UserTemplate:
    """设计师默认模板"""
    return UserTemplate(
        name="designer",
        role="Designer",
        angle=SummaryAngle.TOWARDS_USER_IMPACT,
        focus=["ux", "user-feedback", "design-decisions", "visuals"],
        description="适合设计师的模板，关注用户体验、设计决策和视觉相关",
        sections=[
            TemplateSection(
                id="summary",
                title="设计概要",
                prompt="概括会议讨论的设计主题和目标",
                required=True,
                format=OutputFormat.PARAGRAPH,
                order=1
            ),
            TemplateSection(
                id="user-feedback",
                title="用户反馈",
                prompt="提取讨论到的用户反馈和用户痛点",
                required=True,
                format=OutputFormat.BULLET_POINTS,
                order=2
            ),
            TemplateSection(
                id="design-decisions",
                title="设计决策",
                prompt="记录做出的设计决策，包括方案选择和理由",
                required=True,
                format=OutputFormat.BULLET_POINTS,
                order=3
            ),
            TemplateSection(
                id="ux-considerations",
                title="用户体验考虑",
                prompt="列出讨论到的 UX 相关考虑和改进点",
                required=True,
                format=OutputFormat.BULLET_POINTS,
                order=4
            ),
            TemplateSection(
                id="visuals",
                title="视觉相关",
                prompt="记录视觉设计相关的内容，如颜色、布局、动效等",
                required=False,
                format=OutputFormat.BULLET_POINTS,
                order=5
            )
        ],
        is_default=True
    )


def get_executive_template() -> UserTemplate:
    """高管默认模板"""
    return UserTemplate(
        name="executive",
        role="Executive",
        angle=SummaryAngle.TOWARDS_DECISIONS,
        focus=["strategy", "resources", "timeline", "decisions", "roi"],
        description="适合高管的模板，关注战略方向、资源投入和关键决策",
        sections=[
            TemplateSection(
                id="executive-summary",
                title="执行摘要",
                prompt="用简洁的语言总结会议的核心内容和结论（3-5句话）",
                required=True,
                format=OutputFormat.PARAGRAPH,
                order=1
            ),
            TemplateSection(
                id="key-decisions",
                title="关键决策",
                prompt="列出需要高层关注的决策，包括决策影响和后续行动",
                required=True,
                format=OutputFormat.BULLET_POINTS,
                order=2
            ),
            TemplateSection(
                id="strategy",
                title="战略影响",
                prompt="分析会议内容对公司/产品战略的影响",
                required=True,
                format=OutputFormat.PARAGRAPH,
                order=3
            ),
            TemplateSection(
                id="resources",
                title="资源需求",
                prompt="总结提出的人力、时间或预算需求",
                required=True,
                format=OutputFormat.BULLET_POINTS,
                order=4
            ),
            TemplateSection(
                id="timeline",
                title="时间规划",
                prompt="列出关键里程碑和时间节点",
                required=True,
                format=OutputFormat.BULLET_POINTS,
                order=5
            ),
            TemplateSection(
                id="roi",
                title="预期收益",
                prompt="说明讨论到的预期收益或 ROI",
                required=False,
                format=OutputFormat.PARAGRAPH,
                order=6
            )
        ],
        is_default=True
    )


def get_general_template() -> UserTemplate:
    """通用默认模板"""
    return UserTemplate(
        name="general",
        role="General",
        angle=SummaryAngle.BALANCED,
        focus=["summary", "key-points", "action-items"],
        description="通用模板，适合大多数场景",
        sections=[
            TemplateSection(
                id="summary",
                title="会议总结",
                prompt="请简要总结这次会议的主要内容",
                required=True,
                format=OutputFormat.PARAGRAPH,
                order=1
            ),
            TemplateSection(
                id="key-points",
                title="关键要点",
                prompt="列出会议讨论的关键要点",
                required=True,
                format=OutputFormat.BULLET_POINTS,
                order=2
            ),
            TemplateSection(
                id="action-items",
                title="行动项",
                prompt="列出需要跟进的行动项",
                required=True,
                format=OutputFormat.BULLET_POINTS,
                order=3
            )
        ],
        is_default=True
    )


# 默认模板注册表
# 注意：此字典需要在所有模板函数定义之后，因此移到文件末尾
DEFAULT_TEMPLATES = {
    "product-manager": get_product_manager_template,
    "developer": get_developer_template,
    "designer": get_designer_template,
    "executive": get_executive_template,
    "general": get_general_template,
}


def get_default_template(name: str) -> UserTemplate:
    """
    获取指定的默认模板

    Args:
        name: 模板名称

    Returns:
        UserTemplate 实例

    Raises:
        ValueError: 如果模板不存在
    """
    if name not in DEFAULT_TEMPLATES:
        available = ", ".join(DEFAULT_TEMPLATES.keys())
        raise ValueError(
            f"默认模板不存在: {name}. "
            f"可用模板: {available}"
        )

    return DEFAULT_TEMPLATES[name]()


def list_default_templates() -> list:
    """
    列出所有默认模板的名称

    Returns:
        模板名称列表
    """
    return list(DEFAULT_TEMPLATES.keys())


def get_all_default_templates() -> list:
    """
    获取所有默认模板实例

    Returns:
        UserTemplate 实例列表
    """
    return [template_func() for template_func in DEFAULT_TEMPLATES.values()]


# ============================================================
# 自律课会议专属模板
# ============================================================

def get_course_general_template() -> UserTemplate:
    """通用模板 - 适合一般受众"""
    return UserTemplate(
        name="course-general",
        role="课程内容总结专家",
        angle=SummaryAngle.BALANCED,
        focus=["course-content", "teaching-method", "key-concepts", "student-feedback"],
        description="通用模板，提供课程的整体概览",
        sections=[
            TemplateSection(
                id="overview",
                title="课程概述",
                prompt="简要介绍这是什么课程，主讲人是谁，课程的目标是什么",
                required=True,
                format=OutputFormat.PARAGRAPH,
                order=1
            ),
            TemplateSection(
                id="core-concepts",
                title="核心观点",
                prompt="总结课程传达的核心观点和理念，如执行力的定义、目标设定的重要性等",
                required=True,
                format=OutputFormat.BULLET_POINTS,
                order=2
            ),
            TemplateSection(
                id="course-structure",
                title="课程结构",
                prompt="列出课程包含的主要模块和章节",
                required=True,
                format=OutputFormat.BULLET_POINTS,
                order=3
            ),
            TemplateSection(
                id="teaching-features",
                title="教学特色",
                prompt="总结课程的独特教学方法，如案例分析、互动环节、小组学习等",
                required=True,
                format=OutputFormat.BULLET_POINTS,
                order=4
            ),
            TemplateSection(
                id="student-cases",
                title="学员案例",
                prompt="提取会议中提到的学员成功案例和反馈",
                required=False,
                format=OutputFormat.BULLET_POINTS,
                order=5
            )
        ],
        is_default=False
    )


def get_course_student_template() -> UserTemplate:
    """大学学生模板 - 适合潜在学员"""
    return UserTemplate(
        name="course-student",
        role="大学生学习顾问",
        angle=SummaryAngle.TOWARDS_USER_IMPACT,
        focus=["benefits", "problem-solved", "course-content", "enrollment-info"],
        description="适合大学生了解课程价值和报名信息",
        sections=[
            TemplateSection(
                id="pain-points",
                title="你是否面临这些问题",
                prompt="列出课程针对的学生痛点，如拖延、缺乏自律、目标难以执行等",
                required=True,
                format=OutputFormat.BULLET_POINTS,
                order=1
            ),
            TemplateSection(
                id="what-you-will-learn",
                title="你将学到什么",
                prompt="详细列出课程会教授的具体技能和方法",
                required=True,
                format=OutputFormat.BULLET_POINTS,
                order=2
            ),
            TemplateSection(
                id="benefits",
                title="课程能带给你什么",
                prompt="说明完成课程后学生能获得的改变和收益",
                required=True,
                format=OutputFormat.BULLET_POINTS,
                order=3
            ),
            TemplateSection(
                id="success-cases",
                title="学长学姐的成果",
                prompt="提取会议中提到的学员成功案例，如保研、考研上岸、进大厂等",
                required=True,
                format=OutputFormat.BULLET_POINTS,
                order=4
            ),
            TemplateSection(
                id="course-format",
                title="上课形式",
                prompt="说明课程的教学方式、时间安排、小组学习等",
                required=True,
                format=OutputFormat.PARAGRAPH,
                order=5
            ),
            TemplateSection(
                id="enrollment",
                title="报名信息",
                prompt="提供课程价格、报名截止时间、开课时间、报名方式等关键信息",
                required=True,
                format=OutputFormat.BULLET_POINTS,
                order=6
            ),
            TemplateSection(
                id="is-it-for-you",
                title="这门课适合你吗",
                prompt="说明哪些人适合这门课，哪些人可能不适合",
                required=True,
                format=OutputFormat.BULLET_POINTS,
                order=7
            )
        ],
        is_default=False
    )


def get_course_teacher_template() -> UserTemplate:
    """课程讲师模板 - 适合教学人员"""
    return UserTemplate(
        name="course-teacher",
        role="教育教学专家",
        angle=SummaryAngle.TOWARDS_PROCESS,
        focus=["pedagogy", "course-design", "student-engagement", "learning-outcomes"],
        description="适合教学人员了解课程设计理念和方法",
        sections=[
            TemplateSection(
                id="teaching-philosophy",
                title="教学理念",
                prompt="总结主讲人的教学理念，如执行力可培养、从底层逻辑改变等",
                required=True,
                format=OutputFormat.PARAGRAPH,
                order=1
            ),
            TemplateSection(
                id="course-design",
                title="课程设计架构",
                prompt="分析课程的整体设计逻辑，模块划分、章节安排的考虑",
                required=True,
                format=OutputFormat.BULLET_POINTS,
                order=2
            ),
            TemplateSection(
                id="teaching-methods",
                title="教学方法",
                prompt="总结主讲人使用的教学方法，如案例教学、互动测试、经验分享、比喻讲解等",
                required=True,
                format=OutputFormat.BULLET_POINTS,
                order=3
            ),
            TemplateSection(
                id="engagement-strategies",
                title="学员参与策略",
                prompt="分析如何保持学员参与度，如自律小组、每周复盘、打卡机制等",
                required=True,
                format=OutputFormat.BULLET_POINTS,
                order=4
            ),
            TemplateSection(
                id="content-highlights",
                title="内容亮点",
                prompt="提取课程中最有价值的知识点和独特见解",
                required=True,
                format=OutputFormat.BULLET_POINTS,
                order=5
            ),
            TemplateSection(
                id="assessment-feedback",
                title="效果评估与反馈",
                prompt="总结如何评估学习效果，以及收集到的学员反馈",
                required=False,
                format=OutputFormat.PARAGRAPH,
                order=6
            )
        ],
        is_default=False
    )


def get_course_investor_template() -> UserTemplate:
    """投资者模板 - 适合投资分析"""
    return UserTemplate(
        name="course-investor",
        role="商业分析师",
        angle=SummaryAngle.TOWARDS_DECISIONS,
        focus=["market-demand", "business-model", "pricing", "growth-potential", "risks"],
        description="适合投资者了解课程的商业价值和市场前景",
        sections=[
            TemplateSection(
                id="market-opportunity",
                title="市场机会",
                prompt="分析目标市场规模、需求痛点、市场空白",
                required=True,
                format=OutputFormat.BULLET_POINTS,
                order=1
            ),
            TemplateSection(
                id="product-value",
                title="产品价值主张",
                prompt="总结课程的核心差异化价值和竞争优势",
                required=True,
                format=OutputFormat.BULLET_POINTS,
                order=2
            ),
            TemplateSection(
                id="business-model",
                title="商业模式",
                prompt="分析课程的盈利模式、定价策略、交付方式",
                required=True,
                format=OutputFormat.BULLET_POINTS,
                order=3
            ),
            TemplateSection(
                id="pricing",
                title="定价分析",
                prompt="说明课程价格、对比竞品、价值感知",
                required=True,
                format=OutputFormat.PARAGRAPH,
                order=4
            ),
            TemplateSection(
                id="conversion-factors",
                title="转化因素",
                prompt="分析影响用户购买决策的关键因素，如主讲人背书、学员案例、限时优惠等",
                required=True,
                format=OutputFormat.BULLET_POINTS,
                order=5
            ),
            TemplateSection(
                id="social-proof",
                title="社会证明",
                prompt="总结提供的学员成功案例、好评反馈等信任要素",
                required=True,
                format=OutputFormat.BULLET_POINTS,
                order=6
            ),
            TemplateSection(
                id="growth-potential",
                title="增长潜力",
                prompt="分析产品的可扩展性、复购潜力、新客户获取能力",
                required=True,
                format=OutputFormat.BULLET_POINTS,
                order=7
            ),
            TemplateSection(
                id="risks",
                title="风险因素",
                prompt="识别潜在的风险，如市场竞争、学员满意度、口碑维护等",
                required=True,
                format=OutputFormat.BULLET_POINTS,
                order=8
            ),
            TemplateSection(
                id="key-metrics",
                title="关键指标",
                prompt="列出需要跟踪的关键业务指标",
                required=False,
                format=OutputFormat.BULLET_POINTS,
                order=9
            )
        ],
        is_default=False
    )


# ============================================================
# 重新定义 DEFAULT_TEMPLATES（包含所有模板）
# ============================================================
DEFAULT_TEMPLATES = {
    "product-manager": get_product_manager_template,
    "developer": get_developer_template,
    "designer": get_designer_template,
    "executive": get_executive_template,
    "general": get_general_template,
    # 自律课专属模板
    "course-general": get_course_general_template,
    "course-student": get_course_student_template,
    "course-teacher": get_course_teacher_template,
    "course-investor": get_course_investor_template,
}
