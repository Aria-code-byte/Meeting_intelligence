# AI Meeting Assistant V1

> 从会议到结构化记录，用 AI 重新定义会议理解

## 项目简介

AI Meeting Assistant V1 是一个智能会议处理系统，将音频/视频会议转换为：
- **原始会议文档**（逐字转写 + 时间轴）
- **增强版转录**（LLM 修正错别字、优化语句、保持口语风格）
- **带时间索引的纯净实录**（分块整理，带时间戳）
- **角色视角总结**（基于用户自定义模板）

### 当前状态
- **测试覆盖**: 454 个测试用例全部通过
- **开发进度**: PR1-PR4 已完成
- **Python 版本**: 3.12+
- **CLI 支持**: 完整的命令行接口

---

## 技术栈

### 核心技术
| 类别 | 技术选型 | 用途 |
|------|----------|------|
| **语言** | Python 3.12+ | 核心开发语言 |
| **测试** | pytest | 单元测试与集成测试 |
| **数据模型** | dataclasses | 类型安全的数据结构 |

### 音视频处理
| 技术 | 用途 |
|------|------|
| FFmpeg | 音频提取、格式标准化 |
| 音频规范 | WAV, 16kHz, 单声道, 16-bit PCM |

### ASR 语音识别
| Provider | 模型 | 说明 |
|----------|------|------|
| Whisper | base/small/medium | 本地/云端语音识别 |
| faster-whisper | - | 生产环境推荐（更快） |

### LLM 集成
| Provider | 支持模型 | 用途 |
|----------|----------|------|
| OpenAI | gpt-4o-mini, gpt-4 | 转录增强、会议总结 |
| Anthropic | claude-3-5-sonnet | 转录增强、会议总结 |
| GLM (智谱) | glm-4-flash | 国产 LLM 支持 |
| DeepSeek | deepseek-chat | 高性价比国产 LLM |
| Mock | - | 测试环境 |

### 提示词工程
- **Few-shot 学习**: 带示例的提示词模板
- **负面约束**: 明确禁止的行为
- **模板系统**: 通用/技术/高管/个人叙述等多种场景

### 架构特性
- **整数毫秒时间模型**: 避免浮点精度问题
- **确定性分块**: 基于时间窗口的 chunk 划分
- **分层工件**: raw/enhanced 转录分离
- **OpenSpec**: 规范化的变更提案管理

## 快速开始

### 环境要求

- Python 3.12+ (项目已适配 3.12 特性)
- FFmpeg（音视频处理）
- Whisper（ASR 语音识别）

### 安装 FFmpeg

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install ffmpeg

# macOS
brew install ffmpeg

# 验证安装
ffmpeg -version
```

### 安装 Whisper（ASR）

```bash
# 安装 OpenAI Whisper（用于本地语音识别）
pip install openai-whisper

# 或使用 faster-whisper（更快，推荐用于生产环境）
pip install faster-whisper

# 验证安装
whisper --help
```

### 安装依赖

```bash
# 创建虚拟环境（推荐）
python3 -m venv venv
source venv/bin/activate  # Linux/macOS

# 安装依赖
pip install pytest
```

### 配置环境变量

复制示例配置文件并填入你的 API Keys：

```bash
# 复制配置模板
cp .env.example .env

# 编辑 .env 文件，填入你的 API Keys
# 至少配置以下其中一个：
#   - OPENAI_API_KEY (OpenAI GPT)
#   - ANTHROPIC_API_KEY (Anthropic Claude)
#   - ZHIPU_API_KEY (智谱 GLM)
#   - DEEPSEEK_API_KEY (DeepSeek)
```

**⚠️ 安全提示**：
- **切勿**将 `.env` 文件提交到 Git（已添加到 `.gitignore`）
- 如需分享项目，仅分享 `.env.example` 模板文件
- 定期轮换你的 API Keys

### 运行测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定模块测试
pytest tests/test_asr_transcribe.py -v
```

### CLI 使用示例

```bash
# 基础使用（Mock LLM，用于测试）
python -m meeting_intelligence meeting.mp4

# 使用 GLM（智谱 AI）处理
python -m meeting_intelligence meeting.mp3 --provider glm

# 使用 OpenAI 处理，指定模板
python -m meeting_intelligence meeting.mp4 --provider openai --template general

# 使用 Anthropic，指定模型
python -m meeting_intelligence meeting.mp4 --provider anthropic --model claude-3-5-sonnet-20241022

# 使用 DeepSeek（高性价比）
python -m meeting_intelligence meeting.mp4 --provider deepseek --model deepseek-chat

# 不保存结果到文件
python -m meeting_intelligence meeting.mp3 --no-save
```

**输出文件**：
- `data/transcripts/transcript_*.json` - 原始转录（JSON）
- `data/outputs/*_enhanced_*.txt` - 增强文稿
- `data/outputs/*_refined_*.txt` - 带时间索引的纯净实录

## 项目结构

```
meeting_intelligence/
├── input/              # 会议输入模块
│   ├── upload_audio.py
│   ├── upload_video.py
│   └── record_audio.py
├── audio/              # 音频处理模块
│   ├── extract_audio.py
│   └── preprocess.py
├── asr/                # ASR 语音转文字模块
│   ├── transcribe.py
│   ├── providers/
│   │   ├── base.py
│   │   └── whisper.py
│   └── types.py
├── transcript/         # 原始会议文档模块
│   ├── types.py        # TranscriptDocument 类型
│   ├── build.py        # 文档构建
│   ├── load.py         # 文档加载
│   ├── export.py       # 多格式导出
│   ├── enhanced_builder.py  # 增强转录构建
│   └── llm/            # 转录增强 LLM 模块
│       ├── types.py    # 增强数据类型
│       ├── enhancer.py # LLM 增强器
│       ├── mapper.py   # 句子映射引擎
│       ├── confidence.py  # 置信度计算
│       └── fallback.py # 回退引擎
├── template/           # 用户模板系统
│   ├── types.py        # UserTemplate 类型
│   ├── defaults.py     # 默认模板库
│   ├── validation.py   # 模板验证
│   ├── storage.py      # 模板存储
│   ├── manager.py      # 模板管理
│   ├── render.py       # 提示词渲染
│   ├── recorder.py     # 录音模板组件
│   └── refiner.py      # 精修模板组件
├── summarizer/         # LLM 总结引擎
│   ├── types.py        # SummaryResult 类型
│   ├── generate.py     # 总结生成
│   ├── export.py       # 导出功能
│   ├── pipeline.py     # 端到端流程
│   └── llm/            # LLM 提供商
│       ├── base.py
│       ├── openai.py
│       ├── anthropic.py
│       ├── glm.py
│       ├── deepseek.py
│       └── mock.py
├── cli.py              # 命令行接口
├── __main__.py         # 主入口
├── config.py           # 配置管理
├── data/               # 数据存储
│   ├── raw_audio/      # 音频文件
│   ├── transcripts/    # 转写结果
│   ├── templates/      # 用户模板
│   └── summaries/      # 总结结果
├── tests/              # 测试套件
└── openspec/           # OpenSpec 规范
```

## 功能模块

### Phase 1: 会议输入模块 ✅
- **音频上传**: 支持 mp3, wav, m4a 格式
- **视频上传**: 支持 mp4, mkv, mov 格式
- **应用录音**: 本地麦克风录音框架
- **统一接口**: `MeetingInputResult` 数据结构

### Phase 2: 音频处理模块 ✅
- **音频提取**: 使用 ffmpeg 从视频中提取音轨
- **格式标准化**: WAV, 16kHz, 单声道, 16-bit PCM
- **音频预处理**: 音量归一化、可选静音裁剪

### Phase 3: ASR 语音转文字模块 ✅
- **Whisper 集成**: 本地/云端 Whisper 支持
- **多语言**: 中英文混合识别
- **时间戳**: 每句话带精确时间戳
- **结果持久化**: JSON 格式保存

### Phase 4: 原始会议文档模块 ✅
- **文档生成**: 从 ASR 结果生成结构化文档
- **多格式导出**: JSON、TXT、Markdown 格式
- **时间查询**: 按时间范围查询语音片段
- **自动集成**: ASR 转写后自动构建文档

### Phase 5: 用户模板系统 ✅
- **模板定义**: 角色、总结角度、关注重点
- **默认模板**: 产品经理、开发者、设计师、高管、通用
- **模板管理**: 创建、更新、删除自定义模板
- **提示词生成**: 将模板转换为 LLM 提示词

### Phase 6: LLM 总结引擎 ✅
- **LLM 抽象**: 支持 OpenAI、Anthropic、GLM、Mock 提供商
- **总结生成**: 整合 transcript + template → 结构化总结
- **端到端流程**: 音频/视频 → 总结（一键生成）
- **多格式导出**: JSON、TXT、Markdown

### Phase 7: 转录增强模块 ✅ (PR1-PR3)
**核心功能**：
- **原始转录**: Whisper ASR 逐字转写
- **增强转录**: LLM 修正同音错别字、删除冗余语气词
- **时间索引实录**: 分块整理，带时间戳的纯净文本

**技术特性**：
- **确定性分块**: 基于固定时间窗口（60秒）+ 重叠（10秒）
- **整数毫秒模型**: 避免浮点时间精度问题
- **分层工件**: raw/enhanced 转录分离存储
- **Few-shot 提示词**: 带示例的 ASR 错误修正

**支持的提示词模板**：
| 模板名称 | 适用场景 |
|----------|----------|
| general | 通用优化（带 Few-shot 示例） |
| technical | 技术会议（保留术语） |
| executive | 高管汇报（商务风格） |
| minimal | 最小改动（保留原文） |
| speech-to-text-refiner | 个人叙述精修（加粗数字） |

### Phase 8: 高精度语义增强 ✅ (PR4 已完成)
**核心功能**：
- **单句级别增强**: 从整块处理升级为单句粒度
- **多级映射策略**: 精确匹配 → Embedding 相似度 → 位置映射
- **连续置信度**: 多特征加权评分（相似度、位置、编辑距离等）
- **智能回退**: 单句级别的失败回退机制
- **可选多轮增强**: 支持迭代优化

**技术模块**：
| 模块 | 功能 |
|------|------|
| `transcript/llm/mapper.py` | 原句-增强句映射引擎 |
| `transcript/llm/confidence.py` | 置信度计算器 |
| `transcript/llm/fallback.py` | 回退引擎 |

## 音频输出格式规范

所有处理后的音频统一为以下格式：

| 参数 | 值 | 说明 |
|-----|-----|-----|
| 格式 | WAV | 无损波形音频 |
| 采样率 | 16kHz | 语音识别标准 |
| 声道 | Mono (1) | 单声道 |
| 位深 | 16-bit PCM | 标准位深 |

## 使用示例

### 音频上传

```python
from input.upload_audio import upload_audio

result = upload_audio("/path/to/meeting.mp3")
print(f"音频路径: {result.audio_path}")
```

### 视频上传（含音频提取）

```python
from input.upload_video import upload_video

# 上传视频并自动提取音频
result = upload_video("/path/to/meeting.mp4")
print(f"视频路径: {result.video_path}")
print(f"音频路径: {result.audio_path}")
```

### 音频预处理

```python
from audio.preprocess import preprocess_audio, PreprocessOptions

# 默认：音量归一化
processed = preprocess_audio("/path/to/audio.wav")

# 自定义选项
options = PreprocessOptions(
    normalize=True,
    trim_silence=True,
    silence_level=-50
)
processed = preprocess_audio("/path/to/audio.wav", options)
print(f"处理后路径: {processed.path}, 时长: {processed.duration}秒")
```

### 语音转文字（ASR）

```python
from asr import transcribe

# 转写音频文件
result = transcribe("/path/to/audio.wav")

# 查看结果
print(f"识别到 {len(result.utterances)} 条语句")
for utterance in result.utterances:
    print(f"[{utterance.start:.1f}-{utterance.end:.1f}] {utterance.text}")

# 获取完整文本
full_text = result.get_full_text()
print(f"完整文本: {full_text}")
```

### 转写结果 JSON 格式

```json
{
  "utterances": [
    {"start": 0.0, "end": 2.5, "text": "大家好"},
    {"start": 2.6, "end": 5.0, "text": "今天讨论项目进度"}
  ],
  "audio_path": "/path/to/audio.wav",
  "duration": 120.5,
  "asr_provider": "whisper-local-base",
  "timestamp": "2024-01-22T14:30:00"
}
```

### 原始会议文档生成

```python
from asr import transcribe

# 转写时自动构建文档
result = transcribe("/path/to/audio.wav", auto_build_transcript=True)
print(f"文档路径: {result.transcript_path}")

# 手动构建文档
from transcript import build_transcript
document = build_transcript(result, save=True)
```

### 文档导出

```python
from transcript import load_transcript, export_json, export_text, export_markdown

# 加载文档
doc = load_transcript("data/transcripts/transcript_20240122_143000.json")

# 导出为不同格式
export_json(doc, "output/transcript.json")
export_text(doc, "output/transcript.txt")
export_markdown(doc, "output/transcript.md")
```

### 文档查询

```python
# 按时间查询
after_5min = doc.get_utterances_after(300)  # 5分钟之后
before_10min = doc.get_utterances_before(600)  # 10分钟之前
between = doc.get_utterances_between(300, 600)  # 5-10分钟之间

# 获取统计信息
from transcript.build import get_transcript_stats
stats = get_transcript_stats(doc)
print(f"总词数: {stats['total_words']}")
print(f"语速: {stats['words_per_minute']} 字/分钟")
```

### 用户模板系统

```python
from template import get_template_manager, render_template_to_prompt

# 获取模板管理器
manager = get_template_manager()

# 列出所有可用模板
templates = manager.list_templates()
for t in templates:
    print(f"{t['name']}: {t['role']}")

# 获取特定模板
pm_template = manager.get_template("product-manager")
dev_template = manager.get_template("developer")

# 创建自定义模板
custom = manager.create_template(
    name="my-custom",
    role="QA Engineer",
    angle="towards-process",
    focus=["bugs", "testing", "quality"],
    description="QA 工程师模板"
)

# 渲染模板为 LLM 提示词
prompt = render_template_to_prompt(
    pm_template,
    transcript_context={"duration": 1800, "participant_count": 5}
)
print(prompt)
```

### LLM 总结生成

```python
from summarizer.generate import generate_summary
from summarizer.llm import OpenAIProvider

# 配置 LLM 提供商
llm = OpenAIProvider(
    api_key="your-api-key",
    model="gpt-4"
)

# 生成总结
summary = generate_summary(
    transcript="data/transcripts/transcript_20240122_143000.json",
    template="product-manager",
    llm_provider=llm,
    save=True
)

# 查看结果
print(f"模板: {summary.template_name}")
print(f"LLM: {summary.llm_provider}/{summary.llm_model}")
print(f"处理时间: {summary.processing_time:.2f}秒")

# 获取特定 section
key_points = summary.get_section("key-points")
if key_points:
    print(key_points.content)

# 获取完整文本
full_text = summary.get_full_text()
print(full_text)
```

### 总结导出

```python
from summarizer.export import load_summary, export_json, export_text, export_markdown

# 加载总结
summary = load_summary("data/summaries/summary_20240122_143000.json")

# 导出为不同格式
export_json(summary, "output/summary.json")
export_text(summary, "output/summary.txt")
export_markdown(summary, "output/summary.md")
```

### 端到端流程

```python
from summarizer.pipeline import audio_to_summary, video_to_summary

# 音频 → 总结（一键完成）
summary = audio_to_summary(
    audio_path="data/raw_audio/meeting.wav",
    template="developer",
    llm_provider=llm
)

# 视频 → 总结（一键完成）
summary = video_to_summary(
    video_path="data/raw_video/meeting.mp4",
    template="executive",
    llm_provider=llm
)
```

### LLM 提供商配置

```python
from summarizer.llm import OpenAIProvider, AnthropicProvider

# OpenAI 配置
openai_llm = OpenAIProvider(
    api_key="sk-xxx",
    model="gpt-4",
    base_url="https://api.openai.com/v1",  # 可选
    timeout=60,
    max_retries=3
)

# Anthropic 配置
anthropic_llm = AnthropicProvider(
    api_key="sk-ant-xxx",
    model="claude-3-opus-20240229",
    timeout=60,
    max_retries=3
)

# 使用自定义 provider
summary = generate_summary(
    transcript="data/transcripts/transcript.json",
    template="general",
    llm_provider=openai_llm
)
```

## 开发指南

### 代码风格

- 文件命名: `snake_case.py`
- 函数命名: `snake_case`
- 类命名: `PascalCase`
- 中文注释业务逻辑，英文注释技术实现

### 测试策略

- 单元测试: 每个模块独立测试
- 集成测试: 跨模块工作流测试
- 使用 pytest 和 mock 进行隔离测试

## 开发进度

### 已完成 (PR1-PR4)
- [x] PR1: Raw/Enhanced 工件分层架构
- [x] PR2: 确定性分块 + 整数毫秒时间模型
- [x] PR3: 轻量级 LLM 转录增强接入
- [x] PR4: 高精度语义增强模块
- [x] Phase 1-6: 基础会议处理流程
- [x] Phase 7: 转录增强模块（含时间索引实录）
- [x] Phase 8: 高精度语义增强（单句级别）
- [x] CLI 命令行接口

### 项目里程碑
- **测试覆盖**: 454 个测试用例
- **代码质量**: 防御性编程、完整类型注解
- **文档完善**: 架构决策文档、OpenSpec 变更提案
- **LLM 支持**: OpenAI, Anthropic, GLM, DeepSeek, Mock

## 许可证

MIT License
