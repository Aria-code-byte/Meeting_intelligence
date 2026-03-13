# CLI 逻辑迁移到 Web 后端 - 架构文档

## 🎯 核心原则

1. **逻辑注入而非重写** - 直接调用 CLI 核心函数，不修改任何业务逻辑
2. **参数完全对应** - Web API 参数与 CLI argparse 参数一一对应
3. **流式状态同步** - SSE 实时推送 CLI 处理进度到前端

---

## 📊 完整函数调用链对比

### CLI 主流程 (`__main__.py:main()`)

```
CLI 流程                          Web API 对应
─────────────────────────────────────────────────────────
argparse 解析参数          →    Pydantic 模型验证
├── input                  →    UploadFile (file)
├── --template -t          →    template: str = "general"
├── --provider -p          →    provider: str = "mock"
├── --model -m             →    model: Optional[str]
└── --no-save              →    no_save: bool = False

main() 执行流程             →    POST /api/process
├── create_llm_provider()  →    (直接调用)
├── [1/3] transcribe()     →    CLIStepProcessor.step_1_transcribe()
├── [2/3] enhance_transcript() →  CLIStepProcessor.step_2_enhance()
└── [3/3] refine_transcript_with_timestamps() → CLIStepProcessor.step_3_refine()
```

### 核心类映射表

| CLI 模块 | 核心类/函数 | 位置 | Web 复用方式 |
|---------|-----------|------|-------------|
| `__main__.py` | `create_llm_provider()` | line 45 | 直接导入调用 |
| `__main__.py` | `enhance_transcript()` | line 87 | 直接导入调用 |
| `__main__.py` | `refine_transcript_with_timestamps()` | line 285 | 直接导入调用 |
| `asr/transcribe.py` | `transcribe()` | line 89 | 直接导入调用 |
| `template/recorder.py` | `get_recorder_prompts()` | line 108 | 间接调用（通过 CLI 函数） |
| `transcript/llm/enhancer.py` | `LLMTranscriptEnhancer` | line 266 | 间接调用（通过 CLI 函数） |

---

## 🗂️ 文件结构

```
web_backend/
├── cli_wrapper.py          # CLI 逻辑包装层（核心）
│   ├── ProcessRequest      # 请求模型（对应 CLI 参数）
│   ├── ProcessResult       # 结果模型
│   ├── CLIMeetingProcessor # 完整流程处理器
│   └── CLIStepProcessor    # 分步处理器
│
├── sse.py                  # SSE 流式响应模块
│   ├── TaskManager         # 任务管理器
│   ├── sse_event_stream()  # SSE 事件生成器
│   └── StreamingProcessor  # 流式处理器
│
├── main_v2.py              # FastAPI 主应用（更新版）
│   ├── /api/process        # 完整处理 API
│   ├── /api/process/{id}/stream  # SSE 进度订阅
│   ├── /api/steps/1/transcribe   # 分步 API 1
│   ├── /api/steps/2/enhance      # 分步 API 2
│   └── /api/steps/3/refine       # 分步 API 3
│
├── models.py               # 数据库模型（保持不变）
└── main.py                 # 原有主应用（保留）
```

---

## 🔄 数据流图

```
┌─────────────┐
│  Web 前端   │
└──────┬──────┘
       │ 1. 上传文件 + 参数
       ▼
┌─────────────────────────────────────────┐
│         FastAPI (main_v2.py)            │
│  ┌─────────────────────────────────┐   │
│  │  参数验证 (Pydantic)            │   │
│  │  - template: "general"          │   │
│  │  - provider: "mock"             │   │
│  │  - model: Optional[str]         │   │
│  └──────────────┬──────────────────┘   │
└─────────────────┼───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│      CLI Wrapper (cli_wrapper.py)       │
│  ┌─────────────────────────────────┐   │
│  │  CLIMeetingProcessor            │   │
│  │  - _validate_input()            │   │
│  │  - process()                    │   │
│  └──────────────┬──────────────────┘   │
└─────────────────┼───────────────────────┘
                  │ 直接调用（不重写）
                  ▼
┌─────────────────────────────────────────┐
│         CLI 核心模块                     │
│  ┌─────────────────────────────────┐   │
│  │  meeting_intelligence/__main__  │   │
│  │  - create_llm_provider()        │   │
│  │  - enhance_transcript()         │   │
│  │  - refine_transcript_...()      │   │
│  └──────────────┬──────────────────┘   │
│  ┌─────────────────────────────────┐   │
│  │  asr/transcribe.py              │   │
│  │  - transcribe()                 │   │
│  └──────────────┬──────────────────┘   │
│  ┌─────────────────────────────────┐   │
│  │  template/recorder.py           │   │
│  │  - get_recorder_prompts()       │   │
│  └─────────────────────────────────┘   │
└─────────────────┼───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│           SSE 进度推送                   │
│  data: {"stage": "asr", "step": 1, ...} │
│  data: {"stage": "enhance", "step": 2}  │
│  data: {"stage": "complete", ...}       │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────┐
│  Web 前端   │ (实时更新 UI)
└─────────────┘
```

---

## 📋 API 参数对应表

### 完整处理 API (`POST /api/process`)

| Web 参数 | CLI 参数 | 类型 | 默认值 | 说明 |
|---------|---------|------|--------|------|
| `file` | `input` | File | 必填 | 音视频文件 |
| `template` | `--template, -t` | str | `"general"` | 模板名称 |
| `provider` | `--provider, -p` | str | `"mock"` | LLM 提供商 |
| `model` | `--model, -m` | str | `None` | LLM 模型 |
| `no_save` | `--no-save` | bool | `False` | 不保存文件 |

### 分步处理 API

#### `POST /api/steps/1/transcribe`

| Web 参数 | CLI 对应 | 类型 | 默认值 |
|---------|---------|------|--------|
| `file` | `input` | File | 必填 |
| `language` | `transcribe(language=...)` | str | `"auto"` |
| `model_size` | `transcribe(model_size=...)` | str | `"base"` |

#### `POST /api/steps/2/enhance`

| Web 参数 | CLI 对应 | 类型 | 默认值 |
|---------|---------|------|--------|
| `transcript_doc` | `transcript_doc` | dict | 必填 |
| `template` | `args.template` | str | `"general"` |
| `provider` | `args.provider` | str | `"mock"` |
| `model` | `args.model` | str | `None` |

#### `POST /api/steps/3/refine`

| Web 参数 | CLI 对应 | 类型 | 默认值 |
|---------|---------|------|--------|
| `transcript_doc` | `transcript_doc` | dict | 必填 |
| `provider` | `args.provider` | str | `"mock"` |
| `model` | `args.model` | str | `None` |
| `block_duration_minutes` | 硬编码常量 | int | `3` |

---

## 🔌 SSE 事件格式

### 进度事件结构

```json
{
  "stage": "asr",           # asr, enhance, refine, complete, error
  "step": 1,                # 当前步骤 (1/3, 2/3, 3/3)
  "progress": 50,           # 进度百分比 0-100
  "message": "[1/3] 原始转录中...",
  "data": {
    "utterance_count": 120
  },
  "timestamp": "2026-03-13T12:34:56"
}
```

### CLI 输出到 SSE 映射

| CLI 输出 | SSE 事件 |
|---------|---------|
| `[1/3] 原始转录中...` | `{"stage": "asr", "step": 1, "progress": 5, "message": "[1/3] 原始转录中..."}` |
| `✓ 识别了 120 个片段` | `{"data": {"utterance_count": 120}}` |
| `[2/3] 增强文稿（书面化）中...` | `{"stage": "enhance", "step": 2, "progress": 35, ...}` |
| `[3/3] 带时间索引的纯净实录生成中...` | `{"stage": "refine", "step": 3, "progress": 70, ...}` |
| `✓ 处理完成` | `{"stage": "complete", "progress": 100, ...}` |

---

## ✅ 验证清单

### 逻辑完整性验证

- [ ] `create_llm_provider()` - 直接调用 CLI 函数
- [ ] `transcribe()` - 直接调用 CLI 函数
- [ ] `enhance_transcript()` - 直接调用 CLI 函数
- [ ] `refine_transcript_with_timestamps()` - 直接调用 CLI 函数
- [ ] `get_recorder_prompts()` - 间接调用（通过 CLI 函数）
- [ ] 常量 `block_duration_minutes=3` - 保持一致
- [ ] 常量 `REQUEST_DELAY=3` - 保持一致（CLI cli.py:981）

### 参数对应验证

- [ ] `input` → `file` (UploadFile)
- [ ] `--template, -t` → `template: str`
- [ ] `--provider, -p` → `provider: str`
- [ ] `--model, -m` → `model: Optional[str]`
- [ ] `--no-save` → `no_save: bool`

### SSE 进度同步验证

- [ ] [1/3] ASR 转写进度推送
- [ ] [2/3] 增强文稿进度推送
- [ ] [3/3] 带时间戳实录进度推送
- [ ] 完成事件推送
- [ ] 错误事件推送

---

## 🚀 使用示例

### 完整处理流程

```bash
# 1. 上传文件并创建处理任务
curl -X POST "http://localhost:8000/api/process" \
  -F "file=@meeting.mp4" \
  -F "title=周会记录" \
  -F "template=general" \
  -F "provider=deepseek"

# 响应: {"task_id": "abc123...", "status": "pending", ...}

# 2. 订阅 SSE 进度流
curl -N "http://localhost:8000/api/process/abc123.../stream"

# 输出:
# data: {"stage": "asr", "step": 1, "progress": 10, "message": "[1/3] 原始转录中..."}
# data: {"stage": "asr", "step": 1, "progress": 33, "message": "[1/3] 原始转录完成"}
# data: {"stage": "enhance", "step": 2, "progress": 35, "message": "[2/3] 增强文稿中..."}
# ...

# 3. 获取最终结果
curl "http://localhost:8000/api/process/abc123.../result"
```

### 分步处理

```bash
# 步骤 1: ASR 转写
curl -X POST "http://localhost:8000/api/steps/1/transcribe" \
  -F "file=@meeting.mp4" \
  -F "language=auto" \
  -F "model_size=base"

# 响应: {"utterances": [...], "duration": 1800.5, ...}

# 步骤 2: 增强文稿
curl -X POST "http://localhost:8000/api/steps/2/enhance" \
  -H "Content-Type: application/json" \
  -d '{"transcript_doc": {...}, "template": "general"}'

# 步骤 3: 带时间戳实录
curl -X POST "http://localhost:8000/api/steps/3/refine" \
  -H "Content-Type: application/json" \
  -d '{"transcript_doc": {...}, "block_duration_minutes": 3}'
```

---

## 📝 设计决策记录

### 为什么直接导入 CLI 模块？

**决策**：使用 `sys.path.insert()` 直接导入 CLI 模块

**原因**：
1. 保证逻辑 100% 一致性
2. CLI 更新自动同步到 Web API
3. 避免维护双份代码

### 为什么使用 SSE 而非 WebSocket？

**决策**：使用 Server-Sent Events (SSE)

**原因**：
1. 单向推送（服务器→客户端）满足需求
2. 自动重连机制
3. 更简单的实现（不需要 WebSocket 协议协商）

### 为什么需要分步 API？

**决策**：提供 `/api/steps/1/2/3` 分步处理 API

**原因**：
1. 更灵活的处理流程控制
2. 支持中间结果检查
3. 允许自定义组合处理步骤
