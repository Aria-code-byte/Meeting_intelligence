"""
Jinni Meeting Elf - 双页面导航版本
====================================
功能页面：
1. 智能会议处理 - 上传、提取、总结
2. 个人会议库 - 历史记录预览与查看
3. 模板工厂 - 自定义总结模板

启动方式：
    streamlit run app.py --server.port 8501
"""

import asyncio
import json
import time
from datetime import datetime

import requests
import streamlit as st
from streamlit_option_menu import option_menu

# ============================================================
# 页面配置
# ============================================================

st.set_page_config(
    page_title="Jinni Meeting Elf | AI 会议助理",
    page_icon="🧞",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ============================================================
# CSS 样式系统
# ============================================================

st.markdown("""
<style>
/* ============================================================
   克莱因蓝极简主义主题 (Klein Blue Minimalist)
   ============================================================ */

/* 1. 全局清理：移除 Streamlit 顶部 Header 的残留白色方块与 Padding */
.stAppHeader {
    background-color: transparent !important;
    border: none !important;
    height: 0px !important;
    padding: 0 !important;
}

/* 隐藏所有默认 Header 元素 */
.stAppHeader [data-testid="stLogo"],
.stAppHeader button {
    display: none !important;
}

/* 内容区域边距调整 */
.block-container {
    padding-top: 1.5rem !important;
    padding-bottom: 1.5rem !important;
    max-width: 1400px !important;
}

/* 全局背景 - 极浅灰 */
.stApp {
    background-color: #F8F9FA;
    color: #212529;
}

/* 隐藏 Streamlit 默认菜单 */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* ============================================================
   深度视觉清理 - 移除所有不需要的边框和背景
   ============================================================ */

/* 移除所有容器的边框和背景，实现"无框"设计 */
[data-testid="stVerticalBlock"] > div > div[data-testid="stVerticalBlock"],
[data-testid="stVerticalBlock"] > div > div[data-testid="stVerticalBlock"] > div {
    background-color: transparent !important;
    border: none !important;
    box-shadow: none !important;
}

/* 移除 columns 容器的默认样式 */
[data-testid="column"] {
    background-color: transparent !important;
    border: none !important;
}

/* 顶部导航栏 - 白色极简卡片 + Logo 容器 */
.nav-container {
    position: sticky;
    top: 0;
    z-index: 999;
    background: #FFFFFF;
    border-radius: 16px;
    box-shadow: 0 4px 6px rgba(0, 47, 167, 0.05);
    padding: 8px 30px !important;
    margin-bottom: 2rem;
    display: flex !important;
    align-items: center !important;
    justify-content: space-between !important;
}

/* Logo 容器样式 */
.logo-container {
    display: flex;
    align-items: center;
    margin-right: auto;
}

.logo-img {
    width: 38px;
    height: 38px;
    margin-right: 12px;
}

.logo-text {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    font-size: 1.3rem;
    font-weight: 800;
    color: #002FA7;
    letter-spacing: -0.5px;
}

/* 导航选项容器 - 右对齐 */
.nav-options {
    display: flex;
    gap: 8px;
    margin-left: auto;
}

/* 导航链接样式 - 克莱因蓝 */
.nav-link {
    color: #6C757D !important;
    font-size: 0.95rem !important;
    font-weight: 500 !important;
    padding: 8px 16px !important;
    border-radius: 10px !important;
    transition: all 0.2s ease !important;
    cursor: pointer;
}

.nav-link:hover {
    background-color: #F1F3FB !important;
    color: #002FA7 !important;
}

.nav-link-selected {
    background-color: #002FA7 !important;
    color: #FFFFFF !important;
}

/* 选项菜单样式覆盖 */
[data-testid="stHorizontalBlock"] {
    background-color: transparent !important;
}

/* 自定义卡片 - 纯白无边框 */
.custom-card {
    background: #FFFFFF;
    border-radius: 16px;
    padding: 24px;
    min-height: 200px;
    transition: all 0.3s ease;
}

.custom-card:hover {
    box-shadow: 0 4px 20px rgba(0, 47, 167, 0.08);
}

/* 会议预览卡片 - 左边框高亮 */
.meeting-card {
    background: #FFFFFF;
    border-left: 4px solid #E9ECEF;
    border-radius: 8px;
    padding: 16px 20px;
    margin-bottom: 12px;
    cursor: pointer;
    transition: all 0.2s ease;
}

.meeting-card:hover {
    border-left-color: #002FA7;
    box-shadow: 0 2px 12px rgba(0, 47, 167, 0.1);
    transform: translateX(4px);
}

/* 进行中的会议 - 克莱因蓝左边框 */
.meeting-card.active {
    border-left-color: #002FA7;
    background: linear-gradient(to right, rgba(0, 47, 167, 0.02), transparent);
}

/* Markdown 内容预览 - 淡灰背景 */
.markdown-preview {
    background: #F8F9FA;
    border: 1px solid #E9ECEF;
    border-radius: 12px;
    padding: 24px;
    max-height: 500px;
    overflow-y: auto;
    color: #212529;
}

/* 标题样式 - 克莱因蓝 */
.main-title {
    font-size: 2rem;
    font-weight: 700;
    color: #002FA7 !important;
    margin-bottom: 0.5rem;
    letter-spacing: -0.5px;
}

/* 按钮样式 - 克莱因蓝 + 增强 hover 效果 */
.stButton > button {
    background-color: #002FA7 !important;
    color: white !important;
    border-radius: 10px !important;
    border: none !important;
    font-weight: 600 !important;
    transition: all 0.2s ease;
    padding: 0.6rem 1.5rem !important;
}

.stButton > button:hover {
    background-color: #001F7A !important;
    border-color: #001F7A !important;
    box-shadow: 0 4px 16px rgba(0, 47, 167, 0.35) !important;
    transform: translateY(-1px);
}

/* 次要按钮 */
.stButton > button[kind="secondary"] {
    background-color: #F8F9FA !important;
    color: #212529 !important;
    border: 1px solid #E9ECEF !important;
}

/* 文件上传区域 - 巨型虚线框，完美居中 */
[data-testid="stFileUploader"] {
    width: 100%;
    margin-top: 20px;
}

[data-testid="stFileUploader"] section {
    background-color: #FFFFFF !important;
    border: 2px dashed #002FA7 !important;
    border-radius: 16px !important;
    padding: 100px 20px !important;
    display: flex !important;
    flex-direction: column !important;
    align-items: center !important;
    justify-content: center !important;
    transition: all 0.2s ease-in-out;
    min-height: 250px !important;
}

[data-testid="stFileUploader"] section:hover {
    background-color: #F1F3FB !important;
    border-style: solid !important;
    box-shadow: 0 4px 20px rgba(0, 47, 167, 0.1);
    transform: translateY(-2px);
}

/* 隐藏原生上传按钮，让整个区域可点击 */
[data-testid="stFileUploader"] button {
    display: none !important;
}

/* 上传区域文字居中 + 克莱因蓝 */
[data-testid="stFileUploader"] section > div {
    display: flex !important;
    flex-direction: column !important;
    align-items: center !important;
    justify-content: center !important;
    text-align: center !important;
}

/* 上传图标 */
[data-testid="stFileUploader"] section > div::before {
    content: "📥";
    font-size: 56px;
    margin-bottom: 16px;
    opacity: 0.9;
    display: block;
}

/* 上传提示文字样式 */
[data-testid="stFileUploader"] label,
[data-testid="stFileUploader"] section span {
    color: #002FA7 !important;
    font-size: 1.1rem !important;
    font-weight: 500 !important;
}

[data-testid="stFileUploader"] section span[data-testid="baseButton-secondaryPlainText"] {
    color: #6C757D !important;
    font-size: 0.95rem !important;
}

/* 状态徽章 */
.status-badge {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 0.8rem;
    font-weight: 600;
}

.status-completed {
    background: rgba(0, 47, 167, 0.1);
    color: #002FA7;
}

.status-processing {
    background: rgba(255, 165, 0, 0.1);
    color: #FF8C00;
}

.status-pending {
    background: #F8F9FA;
    color: #6C757D;
}

/* 下拉框样式 */
.stSelectbox > div > div {
    background-color: #FFFFFF !important;
    border: 1px solid #E9ECEF !important;
    border-radius: 10px !important;
}

/* 输入框样式 */
.stTextInput > div > div > input {
    background-color: #FFFFFF !important;
    border: 1px solid #E9ECEF !important;
    border-radius: 10px !important;
}

/* 文本区域样式 */
.stTextArea > div > div > textarea {
    background-color: #FFFFFF !important;
    border: 1px solid #E9ECEF !important;
    border-radius: 10px !important;
}

/* expander 样式 */
.streamlit-expanderHeader {
    background-color: #F8F9FA !important;
    border-radius: 10px !important;
    border: 1px solid #E9ECEF !important;
}

/* 所有标题颜色 */
h1, h2, h3, h4, h5, h6 {
    color: #002FA7 !important;
}

/* 选项菜单样式优化 */
.nav-link {
    color: #6C757D !important;
}

.nav-link-selected {
    color: #002FA7 !important;
    background-color: rgba(0, 47, 167, 0.08) !important;
}

/* 进度条颜色 */
.stProgress > div > div > div > div {
    background-color: #002FA7 !important;
}

/* 分隔线 */
hr {
    border-color: #E9ECEF !important;
}
</style>
""", unsafe_allow_html=True)

# ============================================================
# 状态管理初始化
# ============================================================

if 'current_page' not in st.session_state:
    st.session_state.current_page = "智能会议处理"

if 'show_template_editor' not in st.session_state:
    st.session_state.show_template_editor = False

if 'selected_meeting_id' not in st.session_state:
    st.session_state.selected_meeting_id = None

if 'editing_template_id' not in st.session_state:
    st.session_state.editing_template_id = None

# ============================================================
# 辅助函数
# ============================================================

def format_file_size(size_bytes):
    """格式化文件大小"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"


def api_get(endpoint):
    """调用 FastAPI 后端 GET 请求"""
    try:
        response = requests.get(f"http://localhost:8000{endpoint}", timeout=30)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        st.error(f"API 请求失败: {e}")
    return None


def api_post(endpoint, **kwargs):
    """调用 FastAPI 后端 POST 请求"""
    try:
        response = requests.post(
            f"http://localhost:8000{endpoint}",
            timeout=600,  # 增加到 10 分钟以支持长音频
            **kwargs
        )
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API 错误: {response.status_code} - {response.text}")
    except Exception as e:
        st.error(f"API 请求失败: {e}")
    return None


def copy_to_clipboard(text, button_text="📋 复制内容"):
    """复制内容到剪贴板 - 克莱因蓝风格"""
    st.components.v1.html(f"""
    <script>
    function copyToClipboard() {{
        navigator.clipboard.writeText({json.dumps(text)}).then(function() {{
            alert('内容已复制到剪贴板！');
        }});
    }}
    </script>
    <button onclick="copyToClipboard()" style="
        padding: 10px 20px;
        background: #002FA7;
        color: white;
        border: none;
        border-radius: 10px;
        cursor: pointer;
        font-size: 14px;
        font-weight: 600;
        transition: all 0.2s ease;
    " onmouseover="this.style.background='#0028C7'; this.style.boxShadow='0 4px 12px rgba(0,47,167,0.3)'"
       onmouseout="this.style.background='#002FA7'; this.style.boxShadow='none'">{button_text}</button>
    """, height=50)


# ============================================================
# 页面：智能会议处理（主页）
# ============================================================

def page_main():
    """主页面 - 智能会议处理 - 漏斗式业务流"""
    st.markdown('<h1 class="main-title">🎙️ 智能会议处理</h1>', unsafe_allow_html=True)

    # 初始化状态
    if 'uploaded_file_info' not in st.session_state:
        st.session_state.uploaded_file_info = None
    if 'transcript_ready' not in st.session_state:
        st.session_state.transcript_ready = False
    if 'processing_meeting_id' not in st.session_state:
        st.session_state.processing_meeting_id = None

    # 左右布局
    col_left, col_right = st.columns([3, 2], gap="large")

    # ========== 左侧：上传区域 ==========
    with col_left:
        st.markdown("##### 📁 会议文件存档")

        # 初始化上传状态
        if 'show_uploader' not in st.session_state:
            st.session_state.show_uploader = True

        # 动态容器：上传框 / 任务卡片
        upload_container = st.container()

        with upload_container:
            # 未上传状态：显示上传框
            if st.session_state.show_uploader:
                uploaded_file = st.file_uploader(
                    "将视频或音频拖入此处开始处理",
                    type=["mp4", "wav", "mp3", "m4a", "webm"],
                    label_visibility="collapsed",
                    help="支持最大 1GB 的音视频文件",
                    key="main_uploader"
                )

                # 文件选择后自动切换到任务卡片
                if uploaded_file:
                    st.session_state.uploaded_file = uploaded_file
                    st.session_state.show_uploader = False
                    st.session_state.default_title = uploaded_file.name.rsplit('.', 1)[0]
                    st.rerun()

            # 已选择文件：显示任务确认卡片
            else:
                uploaded_file = st.session_state.uploaded_file

                # 一体化任务卡片
                st.markdown(f"""
                <div style="background: #FFFFFF; padding: 24px; border-radius: 16px; border-left: 6px solid #002FA7; box-shadow: 0 4px 16px rgba(0,47,167,0.08); transition: all 0.3s ease;">
                    <div style="display: flex; align-items: center; margin-bottom: 20px;">
                        <span style="font-size: 32px; margin-right: 16px;">📄</span>
                        <div style="flex: 1;">
                            <div style="font-weight: 700; color: #212529; font-size: 1.1rem;">{uploaded_file.name}</div>
                            <div style="color: #6C757D; font-size: 0.85rem;">{format_file_size(uploaded_file.size)} · {uploaded_file.type.upper()}</div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # 标题编辑区
                st.markdown("###### 📝 会议标题")
                title = st.text_input(
                    "会议标题",
                    value=st.session_state.default_title,
                    placeholder="例如：2026-03-11 产品周会",
                    label_visibility="collapsed",
                    key="upload_title"
                )

                st.markdown("<div style='font-size: 0.75rem; color: #ADB5BD; margin: -8px 0 12px;'>* 此标题将用于个人会议库检索</div>", unsafe_allow_html=True)

                # 操作按钮组
                col_confirm, col_change = st.columns([2, 1], gap="small")

                with col_confirm:
                    if st.button("✨ 确认并开始解析", type="primary", use_container_width=True, key="confirm_upload"):
                        with st.spinner("🔄 正在上传..."):
                            file_content = uploaded_file.getvalue()
                            files = {"file": (uploaded_file.name, file_content, uploaded_file.type)}
                            result = api_post("/api/upload", files=files, data={"title": title})

                            if result:
                                st.success(f"✅ 上传成功！会议 ID: {result['id']}")
                                st.session_state.processing_meeting_id = result["id"]
                                st.session_state.transcript_ready = False
                                time.sleep(0.5)
                                st.rerun()

                with col_change:
                    if st.button("🔄 更改文件", use_container_width=True, key="change_file"):
                        st.session_state.show_uploader = True
                        st.session_state.uploaded_file = None
                        st.rerun()

    # ========== 右侧：漏斗式任务配置 ==========
    with col_right:
        st.markdown("##### ⚡ 智能任务配置")

        # 状态 0: 未上传
        if not st.session_state.processing_meeting_id:
            st.markdown("""
            <div style="padding: 24px; text-align: center; background: #F1F3FB; border-radius: 12px; border: 2px solid #002FA7;">
                <div style="color: #002FA7; font-weight: 600; font-size: 0.95rem;">请先上传会议文件</div>
            </div>
            """, unsafe_allow_html=True)

        # 状态 1-3: 已上传，显示处理流程
        else:
            meeting = api_get(f"/api/meetings/{st.session_state.processing_meeting_id}")
            if not meeting:
                st.error("无法获取会议信息")
                st.session_state.processing_meeting_id = None
                st.rerun()
                return

            # 显示当前状态徽章
            status_badge = {
                "pending": ("⏳", "待处理", "#6C757D"),
                "processing": ("🔄", "处理中", "#FF8C00"),
                "completed": ("✅", "已完成", "#002FA7"),
                "failed": ("❌", "失败", "#DC3545")
            }.get(meeting["status"], ("📋", "未知", "#6C757D"))

            st.markdown(f"""
            <div style="background: #F8F9FA; padding: 10px 16px; border-radius: 10px; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center;">
                <span style="font-size: 0.85rem; color: #6C757D;">{meeting['title']}</span>
                <div style="display: flex; align-items: center; gap: 8px;">
                    <span>{status_badge[0]}</span>
                    <span style="color: {status_badge[2]}; font-weight: 600; font-size: 0.85rem;">{status_badge[1]}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # ========== 第一步：语音转文字 ==========
            st.markdown("""
            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 12px;">
                <span style="background: #002FA7; color: white; width: 22px; height: 22px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 0.75rem; font-weight: 600;">1</span>
                <span style="font-weight: 600; color: #212529; font-size: 0.9rem;">语音转文字</span>
            </div>
            """, unsafe_allow_html=True)

            # 进度显示
            if meeting["status"] == "processing":
                st.progress(meeting["progress"] / 100)
                progress_text = {
                    (0, 30): "🔄 提取音频流...",
                    (30, 60): "🎙️ Whisper ASR 转录中...",
                    (60, 90): "🤖 LLM 语义增强...",
                    (90, 100): "✨ 即将完成..."
                }
                for (start, end), text in progress_text.items():
                    if start <= meeting["progress"] < end:
                        st.caption(text)
                        break

                # 轮询更新
                import time as time_module
                for _ in range(30):
                    time_module.sleep(2)
                    status = api_get(f"/api/meetings/{meeting['id']}/status")
                    if status and status["status"] == "completed":
                        st.rerun()
                        break
                    elif status and status["status"] == "failed":
                        st.error(f"❌ 处理失败: {status.get('error_message', '未知错误')}")
                        break

            # 提取按钮
            extract_disabled = meeting["status"] in ["processing", "completed"]
            button_type = "secondary" if extract_disabled else "primary"
            if st.button("📝 提取文字稿", use_container_width=True, disabled=extract_disabled, type=button_type, key="extract_btn"):
                result = api_post(f"/api/meetings/{meeting['id']}/transcribe")
                if result:
                    st.rerun()

            # 完成标记
            if meeting["status"] == "completed" or meeting.get("results"):
                st.markdown("""
                <div style="display: flex; align-items: center; gap: 6px; color: #002FA7; font-size: 0.85rem; margin-top: 8px;">
                    <span>✓</span>
                    <span>文字稿已就绪</span>
                </div>
                """, unsafe_allow_html=True)
                st.session_state.transcript_ready = True

            st.markdown("<div style='height: 1px; background: #E9ECEF; margin: 16px 0;'></div>", unsafe_allow_html=True)

            # ========== 第二步：智能总结 ==========
            st.markdown("""
            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 12px;">
                <span style="background: #6C757D; color: white; width: 22px; height: 22px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 0.75rem; font-weight: 600;">2</span>
                <span style="font-weight: 600; color: #212529; font-size: 0.9rem;">智能总结</span>
            </div>
            """, unsafe_allow_html=True)

            # 模板选择
            templates = api_get("/api/templates")
            if templates:
                template_names = [t["name"] for t in templates]
            else:
                template_names = ["通用周报（默认）", "技术评审（默认）"]

            col_sel, col_add = st.columns([5, 1])
            with col_sel:
                selected_template = st.selectbox("选择模板", template_names, label_visibility="collapsed", key="template_select")
            with col_add:
                if st.button("➕", help="新增模板", key="add_template_btn"):
                    st.session_state.show_template_editor = True
                    st.session_state.editing_template_id = None
                    st.rerun()

            # 总结按钮（带条件判断）
            if st.button("🪄 生成智能总结", use_container_width=True, key="summarize_btn"):
                if not st.session_state.transcript_ready and meeting["status"] != "completed":
                    st.toast("⚠️ 请先完成「提取文字稿」", icon="⚠️")
                else:
                    with st.spinner("🤖 AI 正在生成总结..."):
                        template_id = None
                        if templates and selected_template in template_names:
                            template = next((t for t in templates if t["name"] == selected_template), None)
                            if template:
                                template_id = template["id"]

                        if template_id:
                            result = api_post(f"/api/meetings/{meeting['id']}/summarize", params={"template_id": template_id})
                        else:
                            result = {"message": "使用默认模板"}

                        if result:
                            st.success("✅ 总结生成完成！")
                            time.sleep(0.5)
                            st.rerun()

            # 新建会议按钮
            st.markdown("<div style='height: 1px; background: #E9ECEF; margin: 16px 0;'></div>", unsafe_allow_html=True)
            if st.button("🆕 处理新会议", use_container_width=True, key="new_meeting_btn"):
                st.session_state.processing_meeting_id = None
                st.session_state.uploaded_file_info = None
                st.session_state.transcript_ready = False
                st.rerun()

    # ========== 底部：内容预览区 ==========
    if st.session_state.processing_meeting_id:
        meeting = api_get(f"/api/meetings/{st.session_state.processing_meeting_id}")
        if meeting and meeting.get("results"):
            st.markdown("---")
            st.markdown("### 📄 处理结果")

            # 元数据展示
            result = api_get(f"/api/results/{meeting['results'][0]['id']}")
            if result:
                col_m1, col_m2, col_m3 = st.columns(3)
                with col_m1:
                    st.metric("字数", f"{result.get('word_count', 0):,}")
                with col_m2:
                    st.metric("时长", f"{result.get('duration', 0):.1f}秒")
                with col_m3:
                    st.metric("处理时间", f"{result.get('processing_time', 0):.1f}秒")

            # 标签页
            tab_transcript, tab_summary = st.tabs(["📝 文字稿", "🪄 AI 总结"])

            with tab_transcript:
                if result:
                    # 优先显示经过 LLM 处理的分段文字稿（带时间索引）
                    # 如果没有，则显示原始转录作为后备
                    transcript_text = result.get("transcript_enhanced") or result.get("transcript_raw", "暂无内容")

                    # 添加说明标签
                    if result.get("transcript_enhanced"):
                        st.caption("✨ 已通过 LLM 优化，按时间段分段整理")
                    else:
                        st.caption("📝 原始转录（Whisper 直接输出）")

                    st.markdown('<div class="markdown-preview" style="max-height: 400px;">', unsafe_allow_html=True)
                    st.markdown(transcript_text)
                    st.markdown('</div>', unsafe_allow_html=True)

                    # 操作按钮
                    col_copy, col_download = st.columns(2)
                    with col_copy:
                        copy_to_clipboard(transcript_text, "📋 复制")
                    with col_download:
                        st.download_button(
                            "📥 下载",
                            data=transcript_text,
                            file_name=f"{meeting['title']}_文字稿.md",
                            mime="text/markdown",
                            use_container_width=True
                        )

            with tab_summary:
                if result:
                    # 从新 API 获取会议的所有总结（从 Summary 表）
                    summaries = api_get(f"/api/meetings/{meeting['id']}/summaries")

                    if summaries:
                        # 提取模板名称列表用于下拉菜单
                        template_names = [s.get("template_name", "未知模板") for s in summaries]

                        # 下拉菜单选择模板
                        col_title, col_select = st.columns([3, 2])
                        with col_title:
                            st.markdown("#### 📋 模板总结")
                        with col_select:
                            selected_template_name = st.selectbox(
                                "选择模板查看",
                                template_names,
                                label_visibility="collapsed",
                                key="summary_template_select"
                            )

                        # 找到选中的总结内容
                        selected_summary = next(
                            (s for s in summaries if s.get("template_name") == selected_template_name),
                            None
                        )

                        if selected_summary:
                            content = selected_summary.get("content", "")

                            # 显示模板信息
                            st.caption(f"✨ 使用模板: **{selected_template_name}**")
                            if selected_summary.get("created_at"):
                                st.caption(f"🕒 生成时间: {selected_summary['created_at'][:19]}")

                            # 显示内容
                            st.markdown(content)

                            # 操作按钮
                            col_copy, col_download = st.columns(2)
                            with col_copy:
                                copy_to_clipboard(content, "📋 复制")
                            with col_download:
                                st.download_button(
                                    "📥 下载",
                                    data=content,
                                    file_name=f"{meeting['title']}_{selected_template_name}_总结.md",
                                    mime="text/markdown",
                                    use_container_width=True
                                )
                    else:
                        st.info("👆 请先在右侧选择模板并生成总结")


# ============================================================
# 页面：个人会议库
# ============================================================

def page_library():
    """个人会议库页面"""
    st.markdown('<h1 class="main-title">📚 个人会议库</h1>', unsafe_allow_html=True)

    # 获取所有会议
    meetings = api_get("/api/meetings")

    if not meetings:
        st.info("📭 还没有任何会议记录，去「智能会议处理」上传第一个会议吧！")
        return

    # 如果没有选中的会议，显示预览网格
    if not st.session_state.selected_meeting_id:
        # 三列网格布局
        cols = st.columns(3)

        for idx, meeting in enumerate(meetings):
            col = cols[idx % 3]

            with col:
                # 会议预览卡片 - 克莱因蓝左边框
                status_badge = f'<span class="status-badge status-{meeting["status"]}">{meeting["status"]}</span>'
                active_class = "active" if meeting["status"] == "processing" or meeting["status"] == "pending" else ""

                st.markdown(f"""
                <div class="meeting-card {active_class}">
                    <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 8px;">
                        <div style="font-size: 1rem; font-weight: 600; color: #212529;">
                            {meeting["title"]}
                        </div>
                        {status_badge}
                    </div>
                    <div style="color: #6C757D; font-size: 0.85rem; margin-top: 12px;">
                        {meeting.get("one_line_summary", "📝 暂无概括")}
                    </div>
                    <div style="color: #ADB5BD; font-size: 0.75rem; margin-top: 12px; display: flex; align-items: center; gap: 6px;">
                        <span>🕒</span>
                        <span>{meeting["created_at"][:10] if meeting.get("created_at") else ""}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                if st.button("查看详情", key=f"view_{meeting['id']}", use_container_width=True):
                    st.session_state.selected_meeting_id = meeting["id"]
                    st.rerun()

    else:
        # 显示会议详情
        meeting = api_get(f"/api/meetings/{st.session_state.selected_meeting_id}")

        if st.button("🔙 返回列表", use_container_width=False):
            st.session_state.selected_meeting_id = None
            st.rerun()

        st.markdown(f"### 📂 {meeting['title']}")
        st.markdown("---")

        # 左右布局：左侧显示文字稿，右侧显示各种总结
        col_left, col_right = st.columns([1, 1])

        with col_left:
            st.markdown("#### 📝 智能文字稿")

            if meeting.get("results"):
                result = api_get(f"/api/results/{meeting['results'][0]['id']}")
                if result:
                    # 优先显示经过 LLM 处理的分段文字稿
                    transcript_text = result.get("transcript_enhanced") or result.get("transcript_raw", "暂无内容")

                    # 添加说明标签
                    if result.get("transcript_enhanced"):
                        st.caption("✨ LLM 优化分段版")
                    else:
                        st.caption("📝 原始转录")

                    st.markdown('<div class="markdown-preview">', unsafe_allow_html=True)
                    st.markdown(transcript_text[:500] + "...")
                    st.markdown('</div>', unsafe_allow_html=True)

                    col1, col2 = st.columns(2)
                    with col1:
                        copy_to_clipboard(transcript_text)
                    with col2:
                        st.download_button(
                            "📥 下载",
                            data=transcript_text,
                            file_name=f"{meeting['title']}_文字稿.md",
                            mime="text/markdown"
                        )

        with col_right:
            st.markdown("#### 🪄 AI 总结")

            # 从新 API 获取会议的所有总结（从 Summary 表）
            summaries = api_get(f"/api/meetings/{meeting['id']}/summaries")

            if summaries:
                # 提取模板名称列表
                template_names = [s.get("template_name", "未知模板") for s in summaries]

                # 下拉菜单选择已生成的模板总结
                selected_template_name = st.selectbox(
                    "📋 查看已生成的模板总结",
                    template_names,
                    key=f"lib_summary_select_{meeting['id']}"
                )

                # 找到选中的总结内容
                selected_summary = next(
                    (s for s in summaries if s.get("template_name") == selected_template_name),
                    None
                )

                if selected_summary:
                    content = selected_summary.get("content", "")

                    st.caption(f"✨ **{selected_template_name}**")

                    # 显示预览
                    st.markdown(content[:500] + ("..." if len(content) > 500 else ""))

            st.markdown("---")

            # 重新选择模板生成总结
            templates = api_get("/api/templates")
            if templates:
                template_names = [t["name"] for t in templates]
            else:
                template_names = ["通用周报", "技术评审"]

            new_template = st.selectbox("📋 选择新模板重新生成", template_names, key=f"lib_new_template_{meeting['id']}")

            if st.button("🔄 重新生成总结", use_container_width=True, key=f"lib_regenerate_{meeting['id']}"):
                # 获取选中的模板 ID
                template = next((t for t in templates if t["name"] == new_template), None)
                if template:
                    result = api_post(f"/api/meetings/{meeting['id']}/summarize", params={"template_id": template["id"]})
                    if result:
                        st.success("✅ 总结生成完成！")
                        st.rerun()


# ============================================================
# 页面：模板编辑器
# ============================================================

def page_template_editor():
    """模板编辑页面"""
    st.markdown('<h1 class="main-title">✨ 模板工厂</h1>', unsafe_allow_html=True)

    # 如果是编辑已有模板
    if st.session_state.editing_template_id:
        template = api_get(f"/api/templates/{st.session_state.editing_template_id}")
        if template:
            default_name = template["name"]
            default_desc = template["description"]
        else:
            default_name = ""
            default_desc = ""
    else:
        default_name = ""
        default_desc = ""

    template_name = st.text_input(
        "🏷️ 模板名称",
        value=default_name,
        placeholder="例如：每日站会、产品评审会、技术分享会..."
    )

    template_desc = st.text_area(
        "📝 模板描述 / Prompt 引导",
        value=default_desc,
        placeholder="请描述这个总结模板的要求，例如：\n\n" +
                   "1. 重点提取待办事项\n" +
                   "2. 标注责任人和截止时间\n" +
                   "3. 突出技术决策和风险点",
        height=200
    )

    # 示例提示
    with st.expander("💡 查看示例模板"):
        st.markdown("""
        **示例 1：每日站会**
        ```
        请按以下结构生成会议总结：

        ## 今日完成
        - [列出今日完成的任务]

        ## 明日计划
        - [列出明日计划的任务]

        ## 阻塞问题
        - [列出遇到的困难]
        ```

        **示例 2：产品评审会**
        ```
        请生成包含以下内容的总结：

        ## 需求概述
        [一句话概括需求背景]

        ## 核心功能
        - [功能1]
        - [功能2]

        ## 技术决策
        [关键技术选型说明]

        ## 待办事项
        - [ ] [任务] - [负责人] - [截止日期]
        ```
        """)

    col_save, col_cancel = st.columns(2)

    with col_save:
        if st.button("💾 保存模板", type="primary", use_container_width=True):
            if not template_name or not template_desc:
                st.warning("⚠️ 请填写模板名称和描述")
            else:
                # 调用 API 保存模板
                result = api_post(
                    "/api/templates",
                    json={"name": template_name, "description": template_desc}
                )
                if result:
                    st.success("✅ 模板保存成功！")
                    time.sleep(1)
                    st.session_state.show_template_editor = False
                    st.session_state.editing_template_id = None
                    st.rerun()

    with col_cancel:
        if st.button("🔙 返回", use_container_width=True):
            st.session_state.show_template_editor = False
            st.session_state.editing_template_id = None
            st.rerun()


# ============================================================
# 页面：模板管理（查看所有模板）
# ============================================================

def page_template_list():
    """模板列表页面"""
    st.markdown('<h1 class="main-title">🎨 模板管理</h1>', unsafe_allow_html=True)

    templates = api_get("/api/templates")

    if not templates:
        st.info("📭 还没有任何自定义模板")
    else:
        # 三列网格显示
        cols = st.columns(3)

        for idx, template in enumerate(templates):
            col = cols[idx % 3]

            with col:
                # 模板卡片 - 克莱因蓝风格
                st.markdown(f"""
                <div class="meeting-card">
                    <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 8px;">
                        <span style="font-size: 1.5rem;">🎨</span>
                        <div style="font-size: 1rem; font-weight: 600; color: #212529;">
                            {template['name']}
                        </div>
                    </div>
                    <div style="color: #6C757D; font-size: 0.85rem; margin-top: 12px; line-height: 1.5;">
                        {template['description'][:100]}...
                    </div>
                </div>
                """, unsafe_allow_html=True)

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✏️ 编辑", key=f"edit_{template['id']}", use_container_width=True):
                        st.session_state.show_template_editor = True
                        st.session_state.editing_template_id = template['id']
                        st.rerun()
                with col2:
                    if st.button("🗑️ 删除", key=f"del_{template['id']}", use_container_width=True):
                        # 调用删除 API
                        st.warning("⚠️ 删除功能开发中")

    if st.button("➕ 新增模板", type="primary", use_container_width=True):
        st.session_state.show_template_editor = True
        st.session_state.editing_template_id = None
        st.rerun()


# ============================================================
# 主程序入口
# ============================================================

def main():
    # 检查是否显示模板编辑器（覆盖层）
    if st.session_state.show_template_editor:
        page_template_editor()
        return

    # 顶部导航栏 - Logo + 选项菜单
    st.markdown(f"""
    <div class="nav-container">
        <div class="logo-container">
            <span style="font-size: 2rem;">🧞</span>
            <span class="logo-text">Jinni Meeting Elf</span>
        </div>
        <div class="nav-options">
    """, unsafe_allow_html=True)

    selected_page = option_menu(
        menu_title=None,
        options=["智能会议处理", "个人会议库", "模板管理"],
        icons=["mic", "archive", "palette"],
        default_index=0 if st.session_state.current_page == "智能会议处理" else
                      1 if st.session_state.current_page == "个人会议库" else 2,
        orientation="horizontal",
        styles={
            "container": {"padding": "0!important", "background-color": "transparent"},
            "icon": {"color": "#002FA7", "font-size": "16px"},
            "nav-link": {
                "font-size": "14px",
                "color": "#6C757D",
                "margin": "0px 4px",
                "padding": "8px 16px",
                "border-radius": "10px",
                "font-weight": "500",
            },
            "nav-link-selected": {
                "background-color": "#002FA7",
                "color": "#FFFFFF",
            },
        }
    )

    st.markdown('</div></div>', unsafe_allow_html=True)

    # 更新当前页面状态
    st.session_state.current_page = selected_page

    # 页面路由
    if selected_page == "智能会议处理":
        page_main()
    elif selected_page == "个人会议库":
        page_library()
    elif selected_page == "模板管理":
        page_template_list()


if __name__ == "__main__":
    main()
