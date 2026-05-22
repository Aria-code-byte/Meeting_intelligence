# Jinni Meeting Intelligence - Backend API

**版本**: 1.0.0  
**状态**: 最小可用版本（P0 + P1 接口）  
**更新日期**: 2026-05-13

---

## 📋 功能概述

本后端服务提供会议智能处理的核心 API，支持：

- ✅ 文件上传（音视频）
- ✅ 转录任务（模拟进度）
- ✅ 总结生成（模拟进度）
- ✅ 健康检查
- ⏳ 模板管理（后续版本）

---

## 🚀 快速启动

### 方法 1: 使用启动脚本（推荐）

```bash
cd backend
run_backend.bat
```

### 方法 2: 命令行启动

```bash
# 进入项目根目录
cd D:\projects\Meeting_intelligence

# 激活虚拟环境
.venv\Scripts\activate

# 安装依赖
pip install -r backend/requirements.txt

# 启动服务
cd backend
python -m uvicorn main:app --reload --port 8000
```

### 访问地址

- **API 服务**: http://localhost:8000
- **API 文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/health

---

## 📡 接口清单

### 1. 健康检查

```http
GET /health
```

**响应示例**:
```json
{
  "status": "ok",
  "service": "meeting-intelligence-api",
  "version": "1.0.0",
  "timestamp": "2026-05-13T10:30:00"
}
```

---

### 2. 文件上传

```http
POST /api/upload
Content-Type: multipart/form-data
```

**参数**:
- `file`: 文件对象（必填）
- `title`: 会议标题（可选）

**支持格式**: mp3, wav, mp4, m4a, webm  
**文件大小限制**: 最大 3GB

**响应示例**:
```json
{
  "success": true,
  "meeting_id": "meeting_a1b2c3d4e5f6",
  "file_name": "meeting.mp4",
  "file_size": 123456789,
  "message": "上传成功"
}
```

---

### 3. 启动转录

```http
POST /api/meetings/{meeting_id}/transcribe
```

**响应示例**:
```json
{
  "success": true,
  "task_id": "transcribe_x1y2z3",
  "status": "processing",
  "message": "转录任务已启动"
}
```

**进度模拟**: 约 20 秒完成（0% → 20% → 45% → 70% → 90% → 100%）

---

### 4. 查询转录状态

```http
GET /api/meetings/{meeting_id}/transcription-status
```

**响应示例**:
```json
{
  "success": true,
  "status": "processing",
  "progress": 45,
  "current_step": "正在识别语音内容",
  "message": "转录进行中"
}
```

**状态值**: `processing` | `completed` | `failed`

---

### 5. 获取转录结果

```http
GET /api/meetings/{meeting_id}/transcript
```

**响应示例**:
```json
{
  "success": true,
  "transcript": "[00:00:01] Speaker 1：大家好...",
  "segments": [
    {
      "start": "00:00:01",
      "speaker": "Speaker 1",
      "text": "大家好，我们开始今天的会议。"
    }
  ],
  "message": "获取成功"
}
```

---

### 6. 启动总结生成

```http
POST /api/meetings/{meeting_id}/summarize
Content-Type: application/json
```

**请求体**:
```json
{
  "template_id": "general_meeting",
  "output_format": "markdown"
}
```

**响应示例**:
```json
{
  "success": true,
  "task_id": "summary_x1y2z3",
  "status": "processing",
  "message": "总结生成任务已启动"
}
```

**进度模拟**: 约 20 秒完成（0% → 25% → 50% → 75% → 100%）

---

### 7. 查询总结状态

```http
GET /api/meetings/{meeting_id}/summary-status
```

**响应示例**:
```json
{
  "success": true,
  "status": "processing",
  "progress": 50,
  "current_step": "正在提取关键讨论",
  "message": "总结生成中"
}
```

**状态值**: `processing` | `completed` | `failed`

---

### 8. 获取总结结果

```http
GET /api/meetings/{meeting_id}/summary
```

**响应示例**:
```json
{
  "success": true,
  "summary": "# 会议总结\n\n## 一、会议摘要\n...",
  "markdown": "# 会议总结\n\n## 一、会议摘要\n...",
  "template_id": "general_meeting",
  "template_name": "通用会议纪要",
  "message": "获取成功"
}
```

---

## 🗂️ 文件存储

### 上传文件存储

上传的文件保存在：

```
uploads/
├── meeting_xxx_meeting.mp4
├── meeting_yyy_meeting.wav
└── meeting_zzz_meeting.m4a
```

### 内存存储

当前版本使用内存存储（重启后丢失）：

```python
MEETINGS = {}              # 会议信息
TRANSCRIPTION_TASKS = {}   # 转录任务
SUMMARY_TASKS = {}         # 总结任务
```

**后续升级**: 替换为数据库存储

---

## 🔧 技术栈

- **Web 框架**: FastAPI 0.104+
- **ASGI 服务器**: Uvicorn
- **数据验证**: Pydantic
- **并发处理**: Threading
- **文件上传**: python-multipart

---

## 🌐 跨域配置

已配置 CORS，允许前端访问：

```python
allow_origins=[
    "http://localhost:8501",  # Streamlit 前端
    "http://127.0.0.1:8501",
]
```

---

## 📊 Mock 逻辑说明

### 当前 Mock 状态

本版本使用模拟逻辑，不包含真实的：

- ❌ Whisper ASR 转录
- ❌ LLM 总结生成
- ❌ 数据库存储

### Mock 转录结果

固定生成 7 个片段的会议记录，约 1 分钟时长。

### Mock 总结结果

根据 `template_id` 生成对应的总结结构：

- `general_meeting` - 通用会议纪要（6 章节）
- `weekly_meeting` - 周会总结（3 章节）
- `project_review` - 项目评审（4 章节）
- `default` - 默认模板（4 章节）

---

## 🚨 错误处理

### 统一错误格式

```json
{
  "success": false,
  "message": "错误原因描述"
}
```

### 常见错误

| 错误 | 原因 | 解决方案 |
|------|------|----------|
| 会议不存在 | meeting_id 错误 | 检查 meeting_id 是否正确 |
| 转录任务已存在 | 重复启动 | 等待当前任务完成 |
| 转录未完成 | 时间过早 | 等待转录完成后再请求结果 |
| 不支持的文件格式 | 文件格式错误 | 使用支持的格式：mp3, wav, mp4, m4a, webm |
| 文件过大 | 超过 3GB | 压缩文件或分割上传 |

---

## 🔍 测试接口

### 使用 Swagger UI

1. 启动后端：`python -m uvicorn main:app --reload --port 8000`
2. 访问：http://localhost:8000/docs
3. 点击接口进行测试

### 使用 curl

```bash
# 健康检查
curl http://localhost:8000/health

# 上传文件
curl -X POST http://localhost:8000/api/upload \
  -F "file=@test.mp4" \
  -F "title=测试会议"

# 启动转录
curl -X POST http://localhost:8000/api/meetings/{meeting_id}/transcribe

# 查询转录状态
curl http://localhost:8000/api/meetings/{meeting_id}/transcription-status

# 获取转录结果
curl http://localhost:8000/api/meetings/{meeting_id}/transcript

# 启动总结生成
curl -X POST http://localhost:8000/api/meetings/{meeting_id}/summarize \
  -H "Content-Type: application/json" \
  -d '{"template_id": "general_meeting"}'

# 查询总结状态
curl http://localhost:8000/api/meetings/{meeting_id}/summary-status

# 获取总结结果
curl http://localhost:8000/api/meetings/{meeting_id}/summary
```

---

## 🎯 后续开发计划

### Phase 2: 真实 ASR 对接

- 集成 Whisper ASR
- 支持真实音频转录
- 发言人分离（Diarization）

### Phase 3: 真实 LLM 对接

- 集成 OpenAI/Anthropic API
- 根据模板生成真实总结
- 支持多模型切换

### Phase 4: 模板管理

- GET /api/templates
- GET /api/templates/{template_id}
- POST /api/templates
- PUT /api/templates/{template_id}
- DELETE /api/templates/{template_id}

### Phase 5: 数据库存储

- 会议记录持久化
- 任务状态持久化
- 模板数据持久化

---

## 📝 开发日志

### v1.0.0 (2026-05-13)

**新增功能**:
- ✅ 健康检查接口
- ✅ 文件上传接口
- ✅ 转录任务接口（模拟）
- ✅ 总结生成接口（模拟）
- ✅ CORS 跨域支持
- ✅ 后台任务进度模拟

**技术特点**:
- 使用 FastAPI 框架
- 内存存储（开发阶段）
- Threading 后台任务
- 统一错误处理

**已知限制**:
- Mock 转录和总结生成
- 无数据库持久化
- 重启后数据丢失

---

## 🆘 故障排除

### 后端无法启动

**检查**:
```bash
# 检查端口是否被占用
netstat -ano | findstr :8000

# 如果被占用，终止进程
taskkill /PID <进程ID> /F
```

### 前端无法连接后端

**检查**:
1. 后端是否启动：http://localhost:8000/health
2. 前端 API_BASE_URL 是否正确：`http://localhost:8000`
3. CORS 是否配置正确

### 文件上传失败

**检查**:
1. 文件格式是否支持
2. 文件大小是否超过 3GB
3. uploads 目录是否有写权限

---

## 📞 联系方式

**问题反馈**: 请在项目 Issues 中提交  
**开发文档**: 见项目 docs 目录

---

**后端开发完成！现在可以启动前后端联调测试。**
