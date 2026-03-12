# 🧞 Jinni 会议精灵 - Web 版

> **挑战杯作品** | 基于底层 C++ 引擎与 DeepSeek LLM 的智能会议处理平台

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)](https://streamlit.io/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## ✨ 特性亮点

- **🚀 底层 C++ 引擎**：Whisper 浮点优化推理，比 Python 快 3-5 倍
- **🤖 DeepSeek LLM**：高性价比智能增强与多模板总结
- **🎯 极简操作**：拖拽上传，一键处理，实时进度
- **💾 本地部署**：SQLite 单文件存储，数据完全掌控
- **🎨 科技感 UI**：Streamlit 深色渐变主题

---

## 🏗️ 架构设计

```
┌─────────────────────────────────────────────────────────────┐
│                     Streamlit 前端                          │
│  (文件上传 / 进度展示 / 结果渲染 / 历史记录)                 │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTP/REST API
┌────────────────────▼────────────────────────────────────────┐
│                   FastAPI 后端服务                          │
│  ┌────────────────┐  ┌────────────────┐  ┌──────────────┐  │
│  │  文件上传 API  │  │  异步任务调度  │  │  状态轮询 API │  │
│  └────────┬───────┘  └────────┬───────┘  └──────┬───────┘  │
│           │                   │                  │          │
└───────────┼───────────────────┼──────────────────┼──────────┘
            │                   │                  │
            ▼                   ▼                  │
┌───────────────────┐   ┌──────────────┐         │
│  C++ 核心引擎     │   │   SQLite     │         │
│  • FFmpeg 音频提取│   │   • meetings │         │
│  • Whisper 推理   │   │   • results  │         │
│  • LLM API 调用   │   └──────────────┘         │
└───────────────────┘                             │
                                                    │
                ┌───────────────────────────────────┘
                ▼
        ┌──────────────────┐
        │  DeepSeek API    │
        │  (高性价比 LLM)  │
        └──────────────────┘
```

---

## 🚀 快速开始

### 1. 环境要求

- Python 3.12+
- FFmpeg 4.0+

### 2. 安装依赖

```bash
# 安装 Python 依赖
pip install -r requirements.txt

# 安装 FFmpeg
# Ubuntu/Debian:
sudo apt-get install ffmpeg

# macOS:
brew install ffmpeg
```

### 3. 项目初始化

```bash
# 一键初始化（创建目录、数据库）
python init_project.py
```

### 4. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env，填入 DeepSeek API Key
# DEEPSEEK_API_KEY=sk-xxxxx
```

### 5. 启动服务

```bash
# 终端 1：启动 FastAPI 后端
python main.py

# 终端 2：启动 Streamlit 前端
streamlit run app.py
```

### 6. 访问应用

- **前端界面**: http://localhost:8501
- **API 文档**: http://localhost:8000/docs

---

## 📂 项目结构

```
web_backend/
├── main.py              # FastAPI 后端服务
├── app.py               # Streamlit 前端界面
├── models.py            # SQLAlchemy 数据模型
├── init_project.py      # 项目初始化脚本
├── requirements.txt     # Python 依赖
├── README.md            # 本文件
│
├── core/                # C++ 核心引擎
│   ├── jinni_engine     # C++ 编译的可执行文件
│   ├── jinni_engine.py  # Python 模拟版（开发测试）
│   └── README.md        # C++ 引擎编译说明
│
└── storage/             # 数据存储目录
    ├── videos/          # 上传的视频文件
    ├── db/              # SQLite 数据库
    ├── transcripts/     # 转录结果缓存
    └── cache/           # 临时缓存
```

---

## 🔧 C++ 核心引擎

### 编译说明

详见 `core/README.md`

```bash
cd core
g++ -std=c++17 -O3 \
    -I/usr/include/ffmpeg \
    -lavformat -lavcodec -lavutil -lswresample \
    -lcurl \
    jinni_engine.cpp \
    -o jinni_engine
```

### Python 调用

```python
# 后端通过 subprocess 调用
subprocess.run([
    "./core/jinni_engine",
    "--input", "video.mp4",
    "--output", "result.json",
    "--llm", "deepseek"
])
```

---

## 📊 数据库设计

### meetings 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| title | VARCHAR(255) | 会议标题 |
| video_path | VARCHAR(500) | 视频文件路径 |
| status | VARCHAR(20) | 状态 |
| progress | INTEGER | 进度 0-100 |
| created_at | DATETIME | 创建时间 |

### results 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| meeting_id | INTEGER | 关联会议 |
| transcript_raw | TEXT | 原始转录 |
| summary_json | JSON | 多模板总结 |
| llm_provider | VARCHAR(50) | LLM 提供商 |

---

## 🎯 技术亮点（竞赛展示）

### 1. 软件工程专业深度

- **分层架构**：API → Service → Domain，职责清晰
- **ORM 设计**：SQLAlchemy 抽象数据访问
- **异步处理**：BackgroundTasks 非阻塞任务
- **RESTful API**：标准化接口设计

### 2. 性能优化

- **C++ 核心引擎**：Whisper 浮点优化，推理速度提升 3-5 倍
- **连接池复用**：数据库连接池管理
- **流式处理**：大文件分块上传

### 3. 成本控制

- **DeepSeek LLM**：性价比远高于 GPT-4
- **本地部署**：数据完全掌控，无云服务费

---

## 📝 API 文档

### POST /api/upload

上传会议音视频文件

**请求**:
- `file`: 音视频文件 (multipart/form-data)
- `title`: 会议标题

**响应**:
```json
{
  "id": 1,
  "title": "产品周会",
  "status": "pending",
  "progress": 0
}
```

### GET /api/history

获取会议历史记录

**参数**:
- `skip`: 分页偏移
- `limit`: 返回数量
- `search`: 搜索关键词

### GET /api/meetings/{id}

获取会议详情（包含处理结果）

---

## 🏆 竞赛答辩准备

### 技术问答

**Q: 为什么用 C++ 写核心引擎？**
A: Whisper 推理涉及大量浮点运算，C++ 编译优化后比 Python 快 3-5 倍，能显著提升用户体验。

**Q: 为什么选择 SQLite 而不是 PostgreSQL？**
A: SQLite 单文件存储，部署简单，数据迁移方便，非常适合竞赛和中小型部署。

**Q: 如何保证处理不阻塞？**
A: 使用 FastAPI 的 BackgroundTasks，将耗时的 C++ 引擎调用放到后台执行，API 立即返回，前端轮询状态。

**Q: 多模板总结如何实现？**
A: C++ 引擎内部使用线程池并行调用 DeepSeek API，一次生成多个角色视角的总结。

---

## 📄 License

MIT License

---

## 🙏 致谢

- [FastAPI](https://fastapi.tiangolo.com/) - 现代化 Web 框架
- [Streamlit](https://streamlit.io/) - 快速构建数据应用
- [DeepSeek](https://www.deepseek.com/) - 高性价比 LLM
- [Whisper](https://github.com/openai/whisper) - OpenAI 语音识别

---

**🧞 Jinni 会议精灵 - 让每一场会议都结构化、可复用**
