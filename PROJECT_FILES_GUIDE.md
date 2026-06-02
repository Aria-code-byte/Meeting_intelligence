# Meeting Intelligence 项目文件功能说明

> 最后更新: 2026-05-24 (交付版本)

## 📁 项目概述

**架构**: FastAPI 后端 + React 前端 + CLI 命令行工具  
**用途**: 音频/视频会议智能转录与总结系统  
**状态**: 生产就绪

---

## 🚀 快速启动

### Windows
- 双击 `start.bat` 启动服务
- 双击 `stop.bat` 停止服务

### Linux/macOS
- `./start.sh` 启动服务
- `./stop.sh` 停止服务

### 访问地址
- 后端 API: http://localhost:8000
- 前端界面: http://localhost:5173

---

## 📂 核心目录结构

```
Meeting-Intelligence/
├── start.bat / start.sh    # 启动脚本
├── stop.bat / stop.sh      # 停止脚本
├── requirements.txt        # Python 依赖
│
├── asr/                   # ASR 语音识别模块
├── audio/                 # 音频处理模块
├── input/                 # 文件输入模块
├── transcript/            # 转录文档模块
├── summarizer/            # AI 总结模块
├── template/              # 模板系统
├── meeting_intelligence/  # CLI 命令行工具
│
├── backend/               # FastAPI 后端
│   ├── main.py           # 后端入口
│   ├── api_routes.py     # API 路由
│   ├── services/         # 核心服务
│   └── tests/            # 后端测试
│
├── web_backend/
│   ├── react-ui/         # React 前端
│   │   ├── src/          # 源代码
│   │   │   ├── pages/    # 页面组件
│   │   │   ├── components/ # UI 组件
│   │   │   └── services/ # API 服务
│   │   └── package.json  # Node 依赖
│   └── storage/          # 数据存储
│
├── tests/                # 单元测试
├── data/                 # 数据文件
│   └── templates/        # 会议模板
│
└── examples/             # 示例代码
```

---

## 📄 项目文档

### 用户文档
- **README.md** - 项目主文档
- **QUICKSTART.md** - 快速开始指南
- **INSTALL_FFMPEG.md** - FFmpeg 安装说明
- **环境要求.md** - 环境要求说明
- **双创作品安装说明.md** - 中文安装说明

### 技术文档
- **商业计划书-技术实现.md** - 技术实现说明
- **PROJECT_FILES_GUIDE.md** - 项目文件清单（本文件）

---

## 🎯 核心模块

### ASR (自动语音识别)
- `transcribe.py` - 语音转文字核心
- `providers/` - Whisper/Faster-Whisper 提供者

### Audio (音频处理)
- `extract_audio.py` - 视频提取音频
- `preprocess.py` - 音频预处理

### Input (文件输入)
- `upload_audio.py` - 音频上传 (MP3/WAV/M4A)
- `upload_video.py` - 视频上传 (MP4/MKV/MOV)
- `record_audio.py` - 实时录音

### Transcript (转录文档)
- `build.py` - 构建转录文档
- `formatter.py` - 格式化转录
- `llm/` - LLM 增强功能

### Summarizer (AI 总结)
- `generate.py` - 生成会议总结
- `llm/` - DeepSeek/OpenAI/Anthropic 客户端

### Template (模板系统)
- `manager.py` - 模板管理器
- `render.py` - 模板渲染
- `data/templates/` - 会议模板 JSON

---

## 🖥️ 后端服务

### FastAPI 主程序
- `main.py` - FastAPI 主入口
- `api_routes.py` - API 路由定义
- `llm_client.py` - LLM 客户端
- `models.py` - 数据模型

### 后端服务
- `services/whisperx_service.py` - WhisperX 服务
- `services/async_transcription_manager.py` - 异步转录管理

### 后端提供者
- `providers/transcription.py` - 转录提供者
- `providers/summary.py` - 总结提供者

---

## 🎨 前端界面

### 页面组件
- `DashboardPage.tsx` - 仪表板/上传页面
- `MeetingLibraryPage.tsx` - 会议库页面
- `SummaryDetailPage.tsx` - 会议详情页面
- `ProcessingPage.tsx` - 处理进度页面
- `TemplatePage.tsx` - 模板管理页面

### UI 组件
- `Sidebar.tsx` - 侧边栏导航
- `TopNav.tsx` - 顶部导航栏
- `RecentMeetingCard.tsx` - 最近会议卡片
- `SettingsPanel.tsx` - 设置面板
- `NotificationCenter.tsx` - 通知中心

### 服务层
- `api.ts` - API 服务
- `transcriptionService.ts` - 转录服务
- `summaryGenerationService.ts` - 总结生成服务
- `meetingProcessingService.ts` - 会议处理服务

---

## 🧪 测试文件

### 单元测试
- `tests/test_asr_*.py` - ASR 模块测试
- `tests/test_transcript_*.py` - 转录模块测试
- `tests/test_summarizer_*.py` - 总结模块测试
- `tests/test_upload_*.py` - 上传功能测试

### 后端测试
- `backend/tests/test_whisperx_*.py` - WhisperX 测试

---

## 📦 配置文件

### 环境配置
- `.env` - 环境变量 (API 密钥、模型设置)
- `requirements.txt` - Python 依赖
- `templates.json` - 模板配置

### 前端配置
- `web_backend/react-ui/package.json` - Node 依赖
- `web_backend/react-ui/vite.config.ts` - Vite 构建配置
- `web_backend/react-ui/tailwind.config.js` - Tailwind CSS 配置

---

## 📁 数据目录

- `data/templates/` - 会议模板 JSON
- `data/proper_nouns.yaml` - 专有名词词典
- `web_backend/storage/cache/` - 缓存目录
- `web_backend/storage/db/` - 数据库目录
- `web_backend/storage/transcripts/` - 转录文档
- `web_backend/storage/videos/` - 视频文件

---

## 🔧 CLI 工具

- `meeting_cli.py` - CLI 主入口
- `meeting_intelligence/cli.py` - CLI 命令逻辑
- `meeting_intelligence/config.py` - 配置管理

---

## 📊 项目统计

| 类别 | 数量 |
|------|------|
| 核心模块 | 7 个 |
| 页面组件 | 5 个 |
| UI 组件 | 12 个 |
| API 服务 | 7 个 |
| 测试文件 | 40+ 个 |
| 会议模板 | 10 个 |

---

**版本**: 2.0 (交付版)  
**更新日期**: 2026-05-24  
**状态**: 生产就绪
