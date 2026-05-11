# Jinni Meeting Elf - Web Backend

## 🚀 快速启动

### 启动主版本（v2.0.0 - 现代AI SaaS分步向导）

```bash
cd web_backend
streamlit run app.py --server.port 8501
```

**访问地址**：http://localhost:8501

---

## 🎯 产品定位

**Jinni 不是普通的会议转录工具。**

它的核心能力是：
> "基于用户自定义模板，从不同业务视角生成高度定制化的 AI 会议总结。"

### 核心价值
- ✅ **AI 模板总结** - 不同业务视角的定制化总结
- ✅ **分步向导流程** - 清晰的5步工作流
- ✅ **现代设计体验** - 参考 Notion AI / Linear / Raycast

### 产品特点
- 🎨 **AI-Native 设计** - 突出 AI 模板价值
- 📊 **分步向导** - 自动引导用户完成流程
- 🚀 **现代交互** - 平滑动画 + 实时反馈
- 📋 **模板驱动** - 6+ 种预设业务场景模板

---

## 🏗️ 5步工作流

### Step 1: 上传会议文件
- 现代卡片式上传区
- 支持拖拽上传
- 文件格式：MP3, WAV, MP4, M4A, WEBM
- 最大文件：3GB

### Step 2: 提取会议内容
- AI Processing Timeline
- 动态进度展示
- 自动进入下一步

### Step 3: 选择总结模板（核心页面）
- 模板卡片网格
- 输出结构预览
- 6种预设模板：
  - 通用会议纪要
  - 产品需求讨论
  - 项目评审
  - 周会总结
  - 客户沟通
  - 面试记录

### Step 4: 生成会议总结
- AI Generation Timeline
- 模板信息确认
- 自动进入结果页

### Step 5: 查看结果
- **AI 总结**（默认 Tab，第一优先级）
- **完整文字稿**（辅助 Tab）
- 下载与复制功能

---

## 🎨 设计系统

### 参考产品
- Notion AI
- Linear
- Raycast
- Vercel Dashboard

### 色彩系统
```css
/* 品牌色 */
--primary: #002FA7;  /* 克莱因蓝 */
--primary-gradient: linear-gradient(135deg, #002FA7 0%, #0039CC 100%);

/* 背景 */
--bg-body: linear-gradient(135deg, #FAFBFD 0%, #F5F7FA 100%);
--bg-card: #FFFFFF;

/* 文字 */
--text-primary: #1A1A1A;
--text-secondary: #6B7280;
```

### 组件特点
- 卡片：16-20px 圆角 + 柔和阴影
- 按钮：12px 圆角 + Hover 动效
- 步骤条：连接线 + 状态指示
- 进度条：渐变 + Shimmer 动效

---

## 🔧 技术栈

### 前端
- **Streamlit** - Python Web 框架
- **HTML/CSS** - 自定义样式系统
- **JavaScript** - 交互增强

### 后端
- **FastAPI** - API 服务
- **Whisper** - ASR 转录
- **LLM** - AI 总结（OpenAI/Anthropic/DeepSeek）

### 依赖安装
```bash
pip install streamlit requests streamlit-option-menu
```

---

## 📁 文件说明

```
web_backend/
├── app.py                 # ⭐ 主应用（v2.0.0）
├── app_old.py            # 旧版本备份（v1.x）
├── VERSION_CHANGELOG.md  # 版本更新日志
├── requirements.txt      # Python 依赖
└── .streamlit/
    └── config.toml       # Streamlit 配置
```

---

## 🔄 版本历史

### v2.0.0 (当前版本) - 2026-05-11
**重大更新**：
- ✅ 彻底重构产品定位
- ✅ 分步向导工作流
- ✅ 现代设计系统
- ✅ AI 总结优先展示
- ✅ 模板卡片网格

详细变更：查看 [VERSION_CHANGELOG.md](./VERSION_CHANGELOG.md)

### v1.x (旧版本)
- 传统后台管理风格
- 左右布局配置流程
- transcript 优先展示

---

## 🚦 使用说明

### 第一次使用？

1. **启动服务**
   ```bash
   streamlit run app.py --server.port 8501
   ```

2. **访问应用**
   ```
   http://localhost:8501
   ```

3. **按照5步向导操作**
   - 上传会议文件
   - 等待内容提取
   - 选择总结模板
   - 等待 AI 生成
   - 查看结果

### 想要旧版本？

```bash
streamlit run app_old.py --server.port 8503
```

访问：http://localhost:8503

---

## 🎯 核心差异化

### 1. 模板驱动
```
不是：先转录，再手动总结
而是：基于模板，AI 自动生成定制化总结
```

### 2. AI 优先
```
不是：transcript 是主要输出
而是：AI 总结是核心价值，transcript 是基础能力
```

### 3. 体验优先
```
不是：功能导向，用户需要理解
而是：体验导向，产品自动引导
```

---

## 📊 API 接口

### 上传文件
```http
POST /api/upload
Content-Type: multipart/form-data

{
  "file": <audio/video file>,
  "title": "会议标题"
}
```

### 获取会议列表
```http
GET /api/meetings
```

### 开始转录
```http
POST /api/meetings/{meeting_id}/transcribe
```

### 生成总结
```http
POST /api/meetings/{meeting_id}/summarize?template_id={template_id}
```

### 获取模板列表
```http
GET /api/templates
```

---

## 🔧 配置说明

### Streamlit 配置
```toml
[server]
maxUploadSize = 3072  # 3GB
headless = true
port = 8501

[theme]
primaryColor = "#002FA7"
backgroundColor = "#FAFBFD"
```

### 环境变量
```bash
# LLM 配置
OPENAI_API_KEY=sk-xxx
ANTHROPIC_API_KEY=sk-ant-xxx
DEEPSEEK_API_KEY=sk-xxx

# ASR 配置
WHISPER_MODEL=base
```

---

## 🎨 截图预览

### Step 1: 上传文件
```
┌─────────────────────────────────────┐
│    [Jinni]  智能会议处理 | 会议库    │
├─────────────────────────────────────┤
│  ●──○──○──○──○                       │
│  上传 提取 模板 生成 结果             │
├─────────────────────────────────────┤
│                                     │
│   📁 拖拽会议文件到这里               │
│                                     │
│   支持 MP3, WAV, MP4...              │
│   最大 3GB                          │
│                                     │
└─────────────────────────────────────┘
```

### Step 3: 选择模板
```
┌─────────────────────────────────────┐
│  ●──●──●──○──○                       │
│  上传 提取 模板 生成 结果             │
├─────────────────────────────────────┤
│                                     │
│  ┌──────────┐  ┌──────────┐         │
│  │📋 通用   │  │🎯 产品   │         │
│  │会议纪要  │  │需求讨论  │         │
│  │          │  │          │         │
│  │• 主要议题 │  │• 核心需求 │         │
│  │• 讨论要点 │  │• 用户价值 │         │
│  └──────────┘  └──────────┘         │
│                                     │
└─────────────────────────────────────┘
```

### Step 5: 查看结果
```
┌─────────────────────────────────────┐
│  ●──●──●──●──●                       │
│  上传 提取 模板 生成 结果             │
├─────────────────────────────────────┤
│ [🪄 AI 总结] [📝 完整文字稿]         │
├─────────────────────────────────────┤
│                                     │
│  # 产品需求评审总结                  │
│                                     │
│  ## 一、核心目标                     │
│  提升用户转化率 30%...               │
│                                     │
│  ## 二、重点讨论内容                 │
│  - 新增智能推荐功能                  │
│  - 优化注册流程                      │
│                                     │
└─────────────────────────────────────┘
```

---

## 🎯 未来规划

### 短期
- [ ] 真实动效库集成（Framer Motion 风格）
- [ ] WebSocket 实时进度推送
- [ ] 模板预览功能
- [ ] 多语言界面

### 中期
- [ ] 模板市场（分享与导入）
- [ ] 协作功能
- [ ] 企业版功能
- [ ] 移动端适配

### 长期
- [ ] API 开放平台
- [ ] 移动端原生应用
- [ ] 浏览器插件
- [ ] AI 智能推荐模板

---

## 📞 支持

### 遇到问题？

1. **检查服务状态**
   ```bash
   netstat -ano | findstr 8501
   ```

2. **查看服务日志**
   - 终端输出会显示详细日志

3. **重启服务**
   ```bash
   # Ctrl+C 停止，然后重新启动
   streamlit run app.py --server.port 8501
   ```

### 功能建议？

欢迎提出建议和反馈！

---

## 🎉 结语

**Jinni Meeting Elf v2.0.0**

让 AI 帮你从不同业务视角理解会议内容。

不仅仅是转录，更是理解。

---

**版本**：v2.0.0
**更新日期**：2026-05-11
**作者**：Claude Sonnet 4.6
