"""
Jinni Meeting Elf - v8 Stable Version
基于干净的版本，逐步添加最小化样式
稳定优先，不激进修改
"""

import streamlit as st
import time
from datetime import datetime

# ============================================================
# 页面配置
# ============================================================

st.set_page_config(
    page_title="Jinni | AI Meeting Intelligence",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ============================================================
# 最小化 CSS - 只添加必要的布局样式
# ============================================================

st.markdown("""
<style>
    /* 隐藏默认菜单 */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    stAppHeader { display: none; }
</style>
""", unsafe_allow_html=True)

# ============================================================
# 状态管理
# ============================================================

def init_state():
    """初始化 session state"""
    if 'current_step' not in st.session_state:
        st.session_state.current_step = 1
    if 'uploaded_file' not in st.session_state:
        st.session_state.uploaded_file = None
    if 'file_meta' not in st.session_state:
        st.session_state.file_meta = None
    if 'selected_template' not in st.session_state:
        st.session_state.selected_template = None

init_state()

# ============================================================
# 辅助函数
# ============================================================

def format_size(size_bytes):
    """格式化文件大小"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"

# ============================================================
# 步骤 1: 上传文件
# ============================================================

def render_step_upload():
    st.header("📁 上传会议文件")
    st.markdown("**步骤 1/5**")
    st.markdown("---")

    st.markdown("### 支持的格式")
    st.markdown("- MP3, WAV, MP4, M4A, WEBM")
    st.markdown("- 最大文件大小: 3GB")
    st.markdown("")

    # 文件上传
    uploaded_file = st.file_uploader(
        "选择会议文件",
        type=["mp3", "wav", "mp4", "m4a", "webm"],
        label_visibility="visible"
    )

    if uploaded_file:
        st.success(f"✅ 已选择文件: **{uploaded_file.name}** ({format_size(uploaded_file.size)})")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("✨ 开始处理", type="primary", use_container_width=True):
                st.session_state.uploaded_file = uploaded_file
                st.session_state.file_meta = {
                    "name": uploaded_file.name,
                    "size": uploaded_file.size
                }
                st.session_state.current_step = 2
                st.rerun()

        with col2:
            if st.button("重新选择", use_container_width=True):
                st.rerun()

# ============================================================
# 步骤 2: 提取内容
# ============================================================

def render_step_extract():
    st.header("⚙️ 提取会议内容")
    st.markdown("**步骤 2/5**")
    st.markdown("---")

    if st.session_state.uploaded_file:
        st.info(f"📄 正在处理: {st.session_state.uploaded_file.name}")

        with st.spinner("🎙️ AI 正在转录语音..."):
            time.sleep(2)  # 模拟处理

        st.success("✅ 转录完成！")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("➡️ 继续选择模板", type="primary", use_container_width=True):
                st.session_state.current_step = 3
                st.rerun()

        with col2:
            if st.button("⬅️ 返回上传", use_container_width=True):
                st.session_state.current_step = 1
                st.rerun()

# ============================================================
# 步骤 3: 选择模板
# ============================================================

def render_step_template():
    st.header("📋 选择总结模板")
    st.markdown("**步骤 3/5**")
    st.markdown("---")

    st.markdown("### 选择一个模板来定制化你的会议总结")

    templates = {
        "通用会议纪要": """
**主要议题**
• 讨论的主题和背景

**讨论要点**
• 关键观点和意见
• 重要决策和结论

**行动项**
• 待办事项
• 负责人和截止时间
        """,

        "产品需求讨论": """
**核心需求**
• 用户痛点
• 功能目标

**用户价值**
• 预期收益
• 业务影响

**技术要点**
• 实现方式
• 技术挑战
        """,

        "项目评审": """
**项目进展**
• 已完成的工作
• 关键里程碑

**风险评估**
• 潜在问题
• 缓解措施

**下一步计划**
• 优先级排序
• 时间安排
        """,

        "周会总结": """
**本周亮点**
• 重要成果
• 关键指标

**遇到的问题**
• 障碍和挑战
• 解决方案

**下周计划**
• 重点工作
• 资源需求
        """,

        "客户沟通": """
**客户需求**
• 业务场景
• 具体要求

**方案讨论**
• 产品匹配度
• 定制化需求

**下一步行动**
• 跟进事项
• 时间节点
        """,

        "面试记录": """
**候选人背景**
• 教育经历
• 工作经验

**能力评估**
• 专业技能
• 软技能

**综合评价**
• 优势
• 待提升点
• 推荐等级
        """
    }

    # 模板选择
    selected = st.radio(
        "选择模板",
        list(templates.keys()),
        label_visibility="collapsed"
    )

    # 显示模板预览
    with st.expander(f"👀 查看模板结构: {selected}", expanded=False):
        st.markdown(templates[selected])

    col1, col2 = st.columns(2)

    with col1:
        if st.button("✨ 生成总结", type="primary", use_container_width=True):
            st.session_state.selected_template = selected
            st.session_state.current_step = 4
            st.rerun()

    with col2:
        if st.button("⬅️ 返回上一步", use_container_width=True):
            st.session_state.current_step = 2
            st.rerun()

# ============================================================
# 步骤 4: 生成总结
# ============================================================

def render_step_generate():
    st.header("🤖 生成会议总结")
    st.markdown("**步骤 4/5**")
    st.markdown("---")

    if st.session_state.selected_template:
        st.info(f"📋 使用模板: **{st.session_state.selected_template}**")

        with st.spinner("✨ AI 正在生成定制化总结..."):
            time.sleep(2)  # 模拟生成

        st.success("✅ 总结生成完成！")

        if st.button("➡️ 查看结果", type="primary", use_container_width=True):
            st.session_state.current_step = 5
            st.rerun()

# ============================================================
# 步骤 5: 查看结果
# ============================================================

def render_step_result():
    st.header("✅ 会议总结")
    st.markdown("**步骤 5/5**")
    st.markdown("---")

    # Tab 切换
    tab1, tab2 = st.tabs(["🪄 AI 总结", "📝 完整文字稿"])

    with tab1:
        st.markdown(f"""
### 📋 {st.session_state.selected_template or '会议总结'}

**会议时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}

---

#### 主要议题
• 这是 AI 生成的定制化会议总结
• 基于你选择的模板: **{st.session_state.selected_template}**
• AI 已自动提取关键信息

#### 讨论要点
• 观点 1: 自动识别的重要内容
• 观点 2: 基于业务视角的关键决策
• 观点 3: AI 提取的核心洞察

#### 行动项
- [ ] 待办事项 1
- [ ] 待办事项 2
- [ ] 待办事项 3

---

*由 Jinni AI 自动生成*
        """)

        col1, col2 = st.columns(2)
        with col1:
            st.button("📋 复制总结", use_container_width=True)
        with col2:
            st.button("📥 下载总结", use_container_width=True)

    with tab2:
        st.markdown("""
### 📝 完整文字稿

[00:00] **发言人1**: 大家好，今天我们讨论...

[00:15] **发言人2**: 我觉得这个很重要...

[00:45] **发言人1**: 让我们总结一下...

[01:20] **发言人2**: 同意，下一步...

---

*完整文字稿由 AI 转录生成*
        """)

        col1, col2 = st.columns(2)
        with col1:
            st.button("📋 复制文字稿", use_container_width=True)
        with col2:
            st.button("📥 下载文字稿", use_container_width=True)

    st.markdown("")

    # 底部按钮
    col1, col2, col3 = st.columns([1, 1, 2])

    with col1:
        if st.button("⬅️ 返回模板", use_container_width=True):
            st.session_state.current_step = 3
            st.rerun()

    with col2:
        if st.button("🆕 新会议", use_container_width=True):
            # 清除状态
            for key in ['current_step', 'uploaded_file', 'file_meta', 'selected_template']:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()

# ============================================================
# 主程序
# ============================================================

def main():
    # 显示当前步骤
    step = st.session_state.current_step

    # 渲染对应步骤
    if step == 1:
        render_step_upload()
    elif step == 2:
        render_step_extract()
    elif step == 3:
        render_step_template()
    elif step == 4:
        render_step_generate()
    elif step == 5:
        render_step_result()

if __name__ == "__main__":
    main()
