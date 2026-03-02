# 最小 CLI 入口 — 调用流程说明

**日期**: 2026-03-02
**版本**: 最小版 v1.0

---

## 一、CLI 命令

### 基本用法

```bash
# 处理音频文件
python -m meeting_intelligence input.mp3

# 处理视频文件
python -m meeting_intelligence input.mp4

# 使用指定模板
python -m meeting_intelligence input.mp3 --template product-manager

# 不保存结果
python -m meeting_intelligence input.mp3 --no-save

# 显示帮助
python -m meeting_intelligence --help
```

---

## 二、数据流程

```
┌─────────────────────────────────────────────────────────────────┐
│                      最小 CLI 数据流                              │
└─────────────────────────────────────────────────────────────────┘

用户命令
    │
    └─► python -m meeting_intelligence input.mp3
            │
            ▼
┌─────────────────────────────────────────────────────────────────┐
│ __main__.py:main() - 参数解析                                     │
├─────────────────────────────────────────────────────────────────┤
│ 1. 解析参数                                                      │
│    input = "input.mp3"                                          │
│    template = "general" (默认)                                  │
│    save = True (默认)                                            │
│                                                                │
│ 2. 验证文件                                                      │
│    - 文件存在性                                                  │
│    - 文件格式 (.mp3/.wav/.m4a/.mp4/.mkv/.mov)                    │
│                                                                │
│ 3. 调用处理流程                                                  │
│    return process_file(input, template, save)                   │
└─────────────────────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────────┐
│ process_file() - 核心处理流程                                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                │
│ Step 1: ASR 转写                                                │
│ ─────────────────────────────────────────────────────────────  │
│ from asr.transcribe import transcribe                          │
│ result = transcribe(input_file)                                │
│                                                                │
│ 输出: TranscriptionResult                                      │
│   - utterances: List[Utterance]                                │
│   - output_path: str (转录JSON文件)                            │
│                                                                │
│ Step 2: 生成摘要                                                │
│ ─────────────────────────────────────────────────────────────  │
│ from summarizer.generate import generate_summary                 │
│ from summarizer.llm.mock import MockLLMProvider               │
│                                                                │
│ llm = MockLLMProvider()  # 默认使用 Mock                       │
│ summary = generate_summary(                                    │
│     transcript=result.output_path,                             │
│     template=template,                                         │
│     llm_provider=llm,                                         │
│     save=True                                                  │
│ )                                                              │
│                                                                │
│ 输出: SummaryResult                                            │
│   - sections: List[SummarySection]                            │
│   - output_path: str (摘要JSON文件)                            │
│                                                                │
│ Step 3: 显示结果                                                │
│ ─────────────────────────────────────────────────────────────  │
│ for section in summary.sections:                               │
│     print(f"## {section.title}")                              │
│     print(section.content)                                      │
└─────────────────────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────────┐
│ 输出文件                                                        │
├─────────────────────────────────────────────────────────────────┤
│ data/transcripts/transcript_YYYYMMDD_HHMMSS.json  # ASR 转录   │
│ data/summaries/summary_YYYYMMDD_HHMMSS.json        # 摘要结果   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 三、关键调用链

### 3.1 ASR 调用

```python
# asr/transcribe.py
def transcribe(
    audio_path: str,
    provider: Optional[str] = None,
    language: str = "auto",
    model_size: str = "base",
    auto_build_transcript: bool = False,
    enable_postprocess: bool = True
) -> TranscriptionResult:
    # 1. 选择 Provider (默认 Whisper)
    # 2. 加载音频
    # 3. 调用 Whisper 转写
    # 4. 后处理 (可选)
    # 5. 保存结果到 data/transcripts/
    # 6. 返回 TranscriptionResult
```

### 3.2 摘要生成调用

```python
# summarizer/generate.py
def generate_summary(
    transcript: Union[TranscriptDocument, str],
    template: Union[UserTemplate, str],
    llm_provider: Optional[BaseLLMProvider] = None,
    save: bool = True
) -> SummaryResult:
    # 1. 加载转录文档
    # 2. 加载模板
    # 3. 使用 Mock Provider (默认)
    # 4. 构建提示词
    # 5. 调用 LLM
    # 6. 解析响应
    # 7. 保存结果到 data/summaries/
    # 8. 返回 SummaryResult
```

### 3.3 Mock Provider 调用

```python
# summarizer/llm/mock.py
class MockLLMProvider(BaseLLMProvider):
    def chat(self, system_prompt, user_prompt) -> LLMResponse:
        # 直接返回预设响应
        # 无需 API Key
        # 无需网络连接
        return LLMResponse(
            content=self.mock_response,
            model="mock-model",
            provider="mock"
        )
```

---

## 四、验收标准验证

### 验证 1: 帮助信息

```bash
$ python -m meeting_intelligence --help

usage: meeting-intelligence [-h] [--template TEMPLATE] [--no-save] input

AI Meeting Assistant - 智能会议总结工具 (最小版)

positional arguments:
  input                 输入文件路径（音频 .mp3/.wav/.m4a 或 视频 .mp4/.mkv/.mov）

options:
  -h, --help            show this help message and exit
  --template TEMPLATE, -t TEMPLATE
                        模板名称（默认: general）
  --no-save             不保存结果到文件
```

### 验证 2: 参数解析

```bash
$ python -m meeting_intelligence test.mp4

AI Meeting Assistant
========================================
输入文件: test.mp4
文件类型: 视频
使用模板: general
LLM: mock (模拟)

Step 1: ASR 转写...
  完成! 识别了 X 个片段
  转录文件: data/transcripts/transcript_...

Step 2: 生成摘要...
  完成! 生成了 X 个章节
  处理时间: X.XX 秒

========================================
摘要结果:
========================================
...
```

### 验证 3: 测试通过

```bash
$ pytest tests/ -q

413 passed in XX.XX s
```

---

## 五、与原版对比

| 功能 | 原版 __main__.py | 最小版 |
|------|------------------|--------|
| 子命令 | process, template, config, summarize, format, refine | 无 |
| 参数 | 10+ 参数 | 2 参数 (input, --template) |
| Provider 选择 | --provider (openai/anthropic/glm) | 固定 Mock |
| Progress 显示 | rich 进度条 | print 输出 |
| 配置文件 | config.yaml | 无 |
| API Key 检查 | 需要 | 不需要 |

---

## 六、下一步

如需扩展 CLI 功能，按优先级：

1. **Provider 切换** (最实用)
   - 添加 `--provider` 参数
   - 检查 API Key
   - 创建真实 Provider

2. **进度显示** (用户体验)
   - 集成 `rich` 库
   - 显示 ASR 进度
   - 显示 LLM 生成进度

3. **子命令** (功能完整)
   - `template list` - 列出模板
   - `template show` - 显示模板详情
   - `format` - 格式化转录

4. **配置文件** (高级用户)
   - config.yaml 支持
   - `config init` 命令

---

*文档版本: 1.0*
*创建日期: 2026-03-02*
