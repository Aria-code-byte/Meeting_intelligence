# Jinni AI Meeting Intelligence - 快速启动指南

## 项目概述

Jinni AI 是一个智能会议处理系统，支持：
- 📤 **会议上传** - 支持音频/视频文件上传
- 🎙️ **语音转录** - Whisper ASR 或 fallback 模式
- 🤖 **AI 总结** - DeepSeek/OpenAI/Anthropic/Ollama 或 fallback 模式
- ✏️ **在线编辑** - 标题、总结、行动项编辑
- 📤 **多格式导出** - Markdown/TXT/JSON
- ⚙️ **模板管理** - 自定义总结模板

---

## 快速启动

### 1. 环境要求

- Python 3.12+
- Node.js 18+
- npm 或 yarn

### 2. 后端启动

```bash
# 进入项目目录
cd /mnt/d/projects/Meeting_intelligence

# （可选）创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate  # Linux/Mac
# 或 .venv\Scripts\activate  # Windows

# 安装依赖
pip install -r backend/requirements.txt

# 配置环境变量
cp backend/.env.example backend/.env
# 编辑 backend/.env 配置 AI provider

# 启动后端
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

后端将运行在 `http://localhost:8000`

### 3. 前端启动

```bash
# 进入前端目录
cd web_backend/react-ui

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端将运行在 `http://localhost:5173`

---

## 环境变量配置

### Fallback 模式（无需 API Key）

编辑 `backend/.env`：

```bash
AI_TRANSCRIPTION_PROVIDER=fallback
AI_SUMMARY_PROVIDER=fallback
```

### DeepSeek 模式（推荐）

编辑 `backend/.env`：

```bash
AI_TRANSCRIPTION_PROVIDER=whisper
AI_SUMMARY_PROVIDER=backend
LLM_PROVIDER=openai
OPENAI_API_KEY=<YOUR_DEEPSEEK_API_KEY>
OPENAI_BASE_URL=https://api.deepseek.com/v1
OPENAI_MODEL=deepseek-chat
```

获取 DeepSeek API Key：https://platform.deepseek.com/

### Ollama 本地模式

编辑 `backend/.env`：

```bash
AI_TRANSCRIPTION_PROVIDER=whisper
AI_SUMMARY_PROVIDER=backend
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2:7b
```

先启动 Ollama：`ollama serve`

---

## Provider 切换

### 只切换转录 Provider

```bash
# 使用 Whisper
AI_TRANSCRIPTION_PROVIDER=whisper

# 使用 Fallback
AI_TRANSCRIPTION_PROVIDER=fallback
```

### 只切换总结 Provider

```bash
# 使用 DeepSeek
AI_SUMMARY_PROVIDER=backend
LLM_PROVIDER=openai
OPENAI_BASE_URL=https://api.deepseek.com/v1
OPENAI_MODEL=deepseek-chat

# 使用 Ollama
AI_SUMMARY_PROVIDER=backend
LLM_PROVIDER=ollama

# 使用 Fallback
AI_SUMMARY_PROVIDER=fallback
```

---

## API 端点

### 健康检查

```bash
curl http://localhost:8000/api/v1/health
```

### Provider 状态

```bash
curl http://localhost:8000/api/v1/providers/info
```

返回示例：

```json
{
  "transcription": {
    "type": "backend",
    "available": true,
    "configured": true,
    "model": "whisper-base"
  },
  "summary": {
    "type": "backend",
    "available": true,
    "configured": true,
    "model": "deepseek-chat"
  }
}
```

---

## 安全注意事项

### ❌ 不要做

- 不要将 API Key 提交到 Git
- 不要在前端代码中包含 API Key
- 不要创建 `VITE_OPENAI_API_KEY` 等前端环境变量
- 不要将 `.env` 文件添加到 Git

### ✅ 要做

- 将 API Key 配置在 `backend/.env` 中
- 确保 `.gitignore` 包含 `.env`
- `.env.example` 只包含空值或占位符
- API Key 只在后端使用

---

## 当前限制

- ❌ 无用户登录系统
- ❌ 无云同步功能
- ❌ 无实时转录
- ❌ PDF/DOCX 导出暂未支持
- ❌ 长音频自动分片暂未实现
- ✅ 数据主要存储在浏览器本地

---

## 构建生产版本

```bash
cd web_backend/react-ui
npm run build
```

构建产物在 `dist/` 目录，可部署到静态服务器。

---

## 故障排查

### 后端启动失败

1. 检查端口 8000 是否被占用
2. 确认 Python 依赖已安装：`pip install -r backend/requirements.txt`
3. 检查 `.env` 文件格式是否正确

### 前端无法连接后端

1. 确认后端正在运行
2. 检查 Vite proxy 配置
3. 查看浏览器控制台错误

### Provider 总是 Fallback

1. 检查 API Key 是否配置
2. 验证 API Key 是否有效
3. 查看后端日志中的错误信息

---

## 相关文档

- [Backend Proxy 指南](web_backend/react-ui/BACKEND_PROXY_GUIDE.md)
- [DeepSeek 配置](DEEPSEEK_CONFIGURED.md)
- [3B-C 验收报告](web_backend/react-ui/STAGE_3B-C_FINAL_ACCEPTANCE_REPORT.md)
- [6B-C 验收报告](STAGE_6BC-FINAL_ACCEPTANCE_REPORT.md)

---

*最后更新: 2026-05-21*
