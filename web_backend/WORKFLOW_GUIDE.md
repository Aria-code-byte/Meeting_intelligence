# Jinni 会议精灵 - 功能按钮映射与测试指南

## 服务启动

### 后端 (FastAPI)
```bash
cd /mnt/d/projects/Meeting_intelligence/web_backend
python main.py
# 或
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```
访问: http://localhost:8000/docs (API 文档)

### 前端 (Streamlit)
```bash
streamlit run app.py --server.port 8501
```
访问: http://localhost:8501

---

## 功能按钮映射

### 页面：智能会议处理 (page_main)

#### 左侧：上传区域
| 按钮/元素 | 功能 | API 端点 | 状态 |
|-----------|------|----------|------|
| 文件拖放区 | 上传音视频文件 | - | ✅ |
| "✨ 确认并开始解析" | 上传文件到服务器 | `POST /api/upload` | ✅ |
| "🔄 更改文件" | 返回上传状态 | - | ✅ |

#### 右侧：智能任务配置
| 按钮/元素 | 功能 | API 端点 | 状态 |
|-----------|------|----------|------|
| 状态徽章 | 显示处理状态 | `GET /api/meetings/{id}` | ✅ |
| 进度条 | 显示处理进度 | 轮询状态 | ✅ |
| "📝 提取文字稿" | 启动转录任务 | `POST /api/meetings/{id}/transcribe` | ✅ |
| "➕" 新增模板 | 跳转模板编辑器 | - | ✅ |
| 模板下拉框 | 选择总结模板 | `GET /api/templates` | ✅ |
| "🪄 生成智能总结" | 生成会议总结 | `POST /api/meetings/{id}/summarize?template_id={id}` | ✅ |

---

### 页面：个人会议库 (page_library)

| 按钮/元素 | 功能 | API 端点 | 状态 |
|-----------|------|----------|------|
| 会议卡片 | 显示会议预览 | `GET /api/meetings` | ✅ |
| 点击卡片 | 查看会议详情 | `GET /api/meetings/{id}` | ✅ |
| "🗑️ 删除" | 删除会议记录 | `DELETE /api/meetings/{id}` | ✅ |
| "📋 复制文字稿" | 复制转录文本 | - | ✅ |
| "📋 复制总结" | 复制总结内容 | - | ✅ |

---

### 页面：模板管理 (page_template_list / page_template_editor)

| 按钮/元素 | 功能 | API 端点 | 状态 |
|-----------|------|----------|------|
| 模板列表 | 显示所有模板 | `GET /api/templates` | ✅ |
| "➕ 新建模板" | 创建新模板 | `POST /api/templates` | ✅ |
| "✏️ 编辑" | 编辑模板 | `PUT /api/templates/{id}` | ✅ |
| "🗑️ 删除" | 删除模板 | `DELETE /api/templates/{id}` | ✅ |

---

## API 端点清单

### 会议管理
- `GET /api/meetings` - 获取所有会议
- `GET /api/meetings/{id}` - 获取会议详情
- `POST /api/upload` - 上传会议文件
- `POST /api/meetings/{id}/transcribe` - 提取文字稿
- `POST /api/meetings/{id}/summarize?template_id={id}` - 生成总结
- `DELETE /api/meetings/{id}` - 删除会议
- `GET /api/meetings/{id}/status` - 获取处理状态

### 模板管理
- `GET /api/templates` - 获取所有模板
- `POST /api/templates` - 创建模板
- `PUT /api/templates/{id}` - 更新模板
- `DELETE /api/templates/{id}` - 删除模板

### 系统端点
- `GET /` - API 信息
- `GET /health` - 健康检查

---

## 测试流程

### 1. 上传并处理文件
1. 访问 http://localhost:8501
2. 在左侧拖放音视频文件
3. 输入会议标题
4. 点击 "✨ 确认并开始解析"

### 2. 提取文字稿
1. 右侧点击 "📝 提取文字稿"
2. 等待进度条完成（模拟处理约 2-3 秒）
3. 状态变为 "已完成"

### 3. 生成智能总结
1. 从下拉框选择模板
2. 点击 "🪄 生成智能总结"
3. 查看生成的总结内容

### 4. 查看会议库
1. 切换到 "📚 个人会议库" 页面
2. 点击任意会议卡片查看详情
3. 复制文字稿或总结内容

---

## 真实处理管道说明

当前使用真实的 Python 模块处理会议：

### ASR 模块 (Whisper) - 优化版
- 直接使用 `whisper.load_model()` 和 `model.transcribe()`
- **模型缓存**: 首次加载后全局缓存，后续请求直接复用
- **跳过 I/O**: 不保存中间 JSON 文件，直接返回结果
- 使用 OpenAI Whisper 进行语音转文字
- 支持语言: 中文、英文 (自动检测)
- 模型大小: tiny/base/small/medium/large (环境变量 `WHISPER_MODEL` 控制)

**性能对比**:
- CLI: 每次加载模型 + 保存 JSON 文件
- Web Backend: 模型缓存 + 跳过文件 I/O = **更快**

### 音频提取模块
- 从 `audio/extract_audio.py` 导入
- 使用 ffmpeg 从视频提取音频
- 输出格式: WAV, 16kHz, 单声道
- 支持格式: mp4, mkv, mov, mp3, wav, m4a

### LLM 模块
- 从 `summarizer/llm/` 导入
- 支持的 Provider:
  - `mock`: 测试模式（返回模拟数据）
  - `deepseek`: DeepSeek API
  - `openai`: OpenAI GPT
  - `glm`: 智谱 GLM
  - `anthropic`: Claude
- 通过环境变量 `DEFAULT_LLM_PROVIDER` 选择

### 环境变量配置
```bash
# Whisper 模型大小 (默认: base)
export WHISPER_MODEL=base

# LLM Provider (默认: mock)
export DEFAULT_LLM_PROVIDER=deepseek

# API Keys (根据选择的 provider 配置)
export ZHIPU_API_KEY=xxx          # 智谱
export OPENAI_API_KEY=xxx         # OpenAI
export DEEPSEEK_API_KEY=xxx       # DeepSeek
export ANTHROPIC_API_KEY=xxx      # Anthropic
```

### 处理流程
1. **音频提取**: 视频文件 → 音频提取 → WAV 音频
2. **ASR 转写**: 音频 → Whisper → 原始转录文本
3. **LLM 总结**: 转录文本 + 模板 → LLM → 结构化总结

### 性能优化（Web Backend 专属）
- **模型缓存**: Whisper 模型全局缓存，避免重复加载
- **跳过文件 I/O**: 直接内存处理，不保存中间 JSON 文件
- **静默模式**: Whisper verbose=False 减少输出开销
- **进度报告**: 控制台实时显示处理进度

---

## 常见问题

### 后端启动失败
- 检查端口 8000 是否被占用
- 确保依赖已安装: `pip install fastapi uvicorn sqlalchemy`

### 前端连接失败
- 确保后端正在运行 (http://localhost:8000)
- 检查 API_BASE_URL 配置

### 文件上传失败
- 检查 storage 目录权限
- 确认文件格式支持 (mp4, wav, mp3, m4a, webm)
- 文件大小限制 1GB

---

## 开发者信息

- 后端端口: 8000
- 前端端口: 8501
- 数据库: SQLite (storage/db/jinni.db)
- 视频存储: storage/videos/
- 转录结果: storage/transcripts/
