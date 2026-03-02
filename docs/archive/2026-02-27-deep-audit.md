# AI 会议助手项目 - 深度审计报告

> **审计日期**: 2026-02-27
> **项目名称**: AI Meeting Assistant V1
> **审计范围**: 全栈架构、文稿生成模块、依赖关系、数据流

---

## 目录

1. [技术栈与依赖](#1-技术栈与依赖)
2. [文稿生成全链路](#2-文稿生成全链路)
3. [关键接口设计](#3-关键接口设计)
4. [现有缺陷诊断](#4-现有缺陷诊断)
5. [冲突预警](#5-冲突预警)
6. [重构建议](#6-重构建议)

---

## 1. 技术栈与依赖

### 1.1 核心依赖 (`requirements.txt`)

| 类别 | 库名称 | 版本 | 用途 |
|------|--------|------|------|
| **LLM提供商** | `openai` | >=1.0.0 | OpenAI API 客户端 |
| | `anthropic` | >=0.18.0 | Anthropic (Claude) API 客户端 |
| | `zhipuai` | >=2.0.0 | 智谱AI (GLM) API 客户端 |
| **ASR引擎** | `openai-whisper` | >=20230314 | 本地语音识别 |
| | `faster-whisper` | >=0.10.0 | (注释) 更快的 Whisper 替代方案 |
| **配置管理** | `python-dotenv` | >=1.0.0 | 环境变量加载 |
| | `pyyaml` | >=6.0 | YAML 配置文件解析 |
| **CLI/UI** | `rich` | >=13.0.0 | 终端美化输出 |
| | `tqdm` | >=4.65.0 | 进度条显示 |
| **测试** | `pytest` | >=7.4.0 | 单元测试框架 |

### 1.2 外部依赖 (系统级)

| 工具 | 用途 | 安装方式 |
|------|------|----------|
| **ffmpeg** | 音视频提取、格式转换、预处理 | `apt-get install ffmpeg` |
| **ffprobe** | 音频时长检测 (ffmpeg 附带) | 随 ffmpeg 安装 |

### 1.3 依赖架构图

```
┌─────────────────────────────────────────────────────────────┐
│                      AI Meeting Assistant                     │
├─────────────────────────────────────────────────────────────┤
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐   │
│  │   LLM 层      │  │   ASR 层      │  │   Audio 层    │   │
│  │ OpenAI SDK    │  │ Whisper       │  │ ffmpeg        │   │
│  │ Anthropic SDK │  │ Faster-Whisper│  │ (外部工具)    │   │
│  │ GLM SDK       │  │ (Python API)  │  │               │   │
│  └───────────────┘  └───────────────┘  └───────────────┘   │
├─────────────────────────────────────────────────────────────┤
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐   │
│  │  Config 层    │  │  CLI 层       │  │  Test 层      │   │
│  │ YAML/DotEnv   │  │ Rich/Argparse │  │ Pytest        │   │
│  └───────────────┘  └───────────────┘  └───────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 1.4 模块依赖关系

```
meeting_intelligence/
├── input/          (会议输入)
│   └── dependencies: pathlib
├── audio/          (音频处理)
│   ├── extract_audio.py  → ffmpeg (外部)
│   └── preprocess.py     → ffmpeg (外部)
├── asr/            (语音识别)
│   ├── providers/whisper.py → openai-whisper
│   ├── transcribe.py      → providers, postprocess
│   └── postprocess.py     → (规则处理，无额外依赖)
├── transcript/     (文稿处理)
│   ├── types.py          → (标准库)
│   ├── build.py          → types, asr.types
│   ├── formatter.py      → (规则处理)
│   └── refiner.py        → (需 LLM provider)
├── template/       (模板系统)
│   └── dependencies: pyyaml
└── summarizer/     (总结引擎)
    ├── generate.py      → template, transcript, llm
    ├── pipeline.py      → asr, transcript, generate
    └── llm/             → openai/anthropic/zhipuai SDKs
```

---

## 2. 文稿生成全链路

### 2.1 数据流概览图

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           文稿生成数据流                                  │
└─────────────────────────────────────────────────────────────────────────┘

输入层
  │
  ├─► [视频文件] .mp4/.mkv/.mov
  │       │
  │       └─► upload_video() ──► MeetingInputResult
  │               │
  │               └─► extract_audio() ──► ProcessedAudio (.wav)
  │
  └─► [音频文件] .mp3/.wav/.m4a
          │
          └─► upload_audio() ──► MeetingInputResult
                  │
                  └─► (可选) preprocess_audio() ──► ProcessedAudio

ASR 识别层
  │
  └─► transcribe(audio_path)
          │
          ├─► WhisperProvider.transcribe()
          │       │
          │       └─► whisper.transcribe() ──► List[Utterance]
          │
          ├─► (可选) postprocess_transcript()
          │       │
          │       └─► TranscriptPostProcessor.correct_transcript()
          │               │
          │               ├─► _remove_filler_words()      # 删除口语词
          │               ├─► _apply_corrections()         # 错别字校正
          │               ├─► _correct_proper_nouns()      # 专有名词大小写
          │               └─► _normalize_numbers()         # 数字格式化
          │
          └─► TranscriptionResult
                  │
                  ├─► 保存到 data/transcripts/transcript_*.json
                  │
                  └─► (可选) build_transcript() ──► TranscriptDocument

文稿构建层
  │
  └─► TranscriptDocument
          │
          ├─► utterances: List[Dict]  # 原始碎片化识别结果
          │       │
          │       └─► 格式: {"start": float, "end": float, "text": str}
          │
          ├─► get_full_text() ──► str  # 拼接所有文本

文稿格式化层 (可选)
  │
  └─► format_transcript()
          │
          └─► TranscriptFormatter.format()
                  │
                  ├─► _merge_utterances() ──► List[Sentence]
                  │       # 合并间隔 <3秒 的片段
                  │
                  ├─► _build_paragraphs() ──► List[Paragraph]
                  │       # 按长度和停顿分段
                  │
                  ├─► _build_sections() ──► List[Section]
                  │       # 按长时间停顿分组
                  │
                  ├─► (可选) _add_missing_punctuation()
                  │       # 简单规则添加标点
                  │
                  └─► FormattedTranscript
                          │
                          ├─► to_markdown() ──► data/formatted/formatted_*.md
                          ├─► to_plain_text() ──► .txt
                          └─► to_html() ──► .html

文稿优化层 (可选)
  │
  └─► refine_transcript()
          │
          └─► TranscriptRefiner.refine()
                  │
                  ├─► _preprocess_text()  # 清理空白
                  │
                  ├─► _split_text_chunks()  # 分块处理
                  │
                  ├─► LLM.chat()  # 使用 LLM 优化
                  │
                  └─► refined_text
                          │
                          └─► data/output/refined_*.md

总结生成层
  │
  └─► generate_summary()
          │
          └─► template.render + transcript ──► LLM ──► SummaryResult
                  │
                  └─► data/summaries/summary_*.json

输出层
  │
  └─► 多种格式输出
          │
          ├─► JSON: 带完整元数据
          ├─► Markdown: 可读文稿
          ├─► Plain Text: 纯文本
          └─► HTML: 网页格式
```

### 2.2 详细处理步骤

#### 阶段 1: 音频提取与预处理

```python
# 文件位置: audio/extract_audio.py, audio/preprocess.py

输入: 视频文件 (.mp4/.mkv/.mov) 或音频文件 (.mp3/.m4a)
      │
      ├─► extract_audio(video_path)  [视频专用]
      │   使用 ffmpeg 命令:
      │   ffmpeg -i video.mp4 -vn -ar 16000 -ac 1 -c:a pcm_s16le output.wav
      │   输出: WAV, 16kHz, 单声道, 16-bit PCM
      │
      └─► (可选) preprocess_audio()
          │
          ├─► convert_to_wav()  # 格式标准化
          │
          ├─► _normalize_audio()  # 音量归一化 (EBU R128 -16 LUFS)
          │
          └─► (可选) _trim_silence()  # 静音裁剪

输出: ProcessedAudio(path="...wav", duration=xxx.x)
```

**关键参数**:
- 采样率: `OUTPUT_SAMPLE_RATE = 16000` (Whisper 标准)
- 声道: `OUTPUT_CHANNELS = 1` (单声道)
- 编码: `OUTPUT_CODEC = "pcm_s16le"` (16-bit PCM)

#### 阶段 2: 语音识别 (ASR)

```python
# 文件位置: asr/transcribe.py, asr/providers/whisper.py

输入: ProcessedAudio
      │
      ├─► WhisperProvider(model_size="base")
      │   可选模型: tiny, base, small, medium, large, large-v2, large-v3
      │
      ├─► whisper.load_model(model_size)
      │
      ├─► whisper.transcribe(audio, language="auto")
      │   返回结构:
      │   {
      │     "segments": [
      │       {"start": 0.0, "end": 2.5, "text": "大家好"},
      │       {"start": 2.6, "end": 5.0, "text": "今天讨论项目进度"}
      │     ]
      │   }
      │
      ├─► 转换为 Utterance 对象列表
      │
      └─► (默认启用) postprocess_transcript()
          │
          └─► 详见 2.3 节

输出: TranscriptionResult(
        utterances: List[Utterance],
        audio_path: str,
        duration: float,
        output_path: str,  # JSON 文件路径
        asr_provider: str,
        timestamp: str
      )
```

#### 阶段 2.3: ASR 后处理 (规则引擎)

```python
# 文件位置: asr/postprocess.py

class TranscriptPostProcessor:
    """
    当前后处理能力:
    1. 删除口语填充词 (FILLER_WORDS)
    2. 错别字映射校正 (COMMON_CORRECTIONS)
    3. 专有名词大小写修正 (DEFAULT_PROPER_NOUNS)
    4. 数字/单位格式化 (NUMBER_PATTERNS)
    5. 清理多余空格

    ⚠️ 缺陷: 无标点符号处理逻辑
    """

处理流程:
  │
  ├─► _remove_filler_words()
  │   删除: "那个", "然后那个", "嗯", "啊", "呃", "就是", "对吧"
  │
  ├─► _apply_corrections()
  │   映射示例:
  │   "一块" → "1元"
  │   "咱们" → "我们"
  │   "咋们" → "我们"
  │
  ├─► _correct_proper_nouns()
  │   大小写修正:
  │   "github" → "GitHub"
  │   "docker" → "Docker"
  │   "python" → "Python"
  │
  ├─► _normalize_numbers()
  │   正则替换:
  │   "(\d+)块钱" → "\1元"
  │   "(\d+)k\b" → "\1K"
  │
  └─► _clean_whitespace()
      压缩多余空格和换行
```

**❌ 关键缺陷**: 后处理模块 **不包含任何标点符号处理**:
- 无句子边界检测
- 无断句逻辑
- 无标点符号添加或修正

#### 阶段 3: 原始文稿构建

```python
# 文件位置: transcript/build.py

输入: TranscriptionResult
      │
      └─► build_transcript()
              │
              ├─► 转换 utterances 格式
              │
              ├─► 创建 TranscriptDocument
              │   metadata = {
              │     "audio_path": str,
              │     "duration": float,
              │     "asr_provider": str,
              │     "created_at": str,
              │     "utterance_count": int
              │   }
              │   utterances = [
              │     {"start": float, "end": float, "text": str},
              │     ...
              │   ]
              │
              └─► 保存到 data/transcripts/transcript_*.json

输出: TranscriptDocument + JSON 文件
```

#### 阶段 4: 文稿格式化 (可读性处理)

```python
# 文件位置: transcript/formatter.py

输入: TranscriptDocument (或 utterances 列表)
      │
      └─► TranscriptFormatter.format(method=FormatMethod.RULE_BASED)
              │
              ├─► _merge_utterances()  # 0-30%
              │   规则:
              │   - 间隔 <= merge_gap_threshold (默认 3秒) 则合并
              │   - 前一句以标点结尾则分句
              │   SENTENCE_ENDINGS = ('。', '！', '？', '!', '?', '…', '~')
              │
              ├─► _build_paragraphs()  # 30-60%
              │   规则:
              │   - 累积长度 > paragraph_max_length (默认 300字) 则分段
              │   - 停顿 > section_break_gap (默认 10秒) 则分段
              │
              ├─► _build_sections()  # 60-90%
              │   规则:
              │   - 停顿 > section_break_gap 或
              │   - 时长 > section_max_duration (默认 300秒) 则分组
              │
              ├─► (可选) _add_missing_punctuation()  # 90-100%
              │   ⚠️ 当前实现极简:
              │   if not text.endswith(('。', '！', '？', '!', '?', '…', '~')):
              │       if any(w in text for w in ["吗", "呢"]): text += "？"
              │       elif any(w in text for w in ["啊", "呀", "哦"]): text += "！"
              │       else: text += "。"
              │
              └─► FormattedTranscript
                      │
                      └─► to_markdown() / to_plain_text() / to_html()

输出: data/formatted/formatted_*.md (可读文稿)
```

**❌ 格式化层缺陷**:
1. `_add_missing_punctuation()` 过于简单，只检查段落结尾
2. 无句子内部标点处理
3. 无上下文感知的断句
4. 无语气和停顿分析

#### 阶段 5: 文稿优化 (LLM 驱动)

```python
# 文件位置: transcript/refiner.py

输入: 文本文件 (.txt/.md) 或 JSON 转录文件
      │
      └─► TranscriptRefiner.refine()
              │
              ├─► _preprocess_text()  # 清理空白
              │
              ├─► _split_text_chunks()  # 分块 (max_chunk_size=8000)
              │
              ├─► 对每个块调用 LLM:
              │   system_prompt = "专业的会议文稿编辑助理..."
              │   user_prompt = "请优化以下会议转录文本:\n\n{chunk}"
              │
              └─► _merge_chunks()  # 合并结果

输出: 优化后的文本 (保存到 data/output/refined_*.md)

⚠️ 注意: 此模块需要外部传入 LLM provider
```

**优化器系统提示词**:
- 保守模式: 仅修正错别字
- 平衡模式: 删除口语词 + 修正错别字 + 优化断句
- 激进模式: 深度可读性优化

---

## 3. 关键接口设计

### 3.1 核心数据结构

#### Utterance (ASR 识别单元)

```python
# 文件位置: asr/types.py

@dataclass
class Utterance:
    """
    单条语音识别结果

    表示一段连续的语音及其对应文本。
    """
    start: float        # 开始时间（秒）
    end: float          # 结束时间（秒）
    text: str           # 识别文本内容

    def to_dict(self) -> dict:
        return {"start": self.start, "end": self.end, "text": self.text}
```

#### TranscriptionResult (ASR 输出)

```python
# 文件位置: asr/types.py

@dataclass
class TranscriptionResult:
    """
    语音识别结果接口

    所有 ASR 操作都返回此结构。
    """
    utterances: List[Utterance]      # 识别结果列表（按时间顺序）
    audio_path: str                   # 源音频文件路径
    duration: float                   # 音频总时长（秒）
    output_path: str                  # 结果 JSON 文件路径
    asr_provider: str                 # ASR 提供商名称
    timestamp: str                    # 识别时间戳
    transcript_path: Optional[str]    # 原始会议文档路径（可选）

    def get_full_text(self) -> str:
        """获取完整文本（所有 utterances 拼接）"""
        return "".join(u.text for u in self.utterances)
```

#### TranscriptDocument (文稿文档)

```python
# 文件位置: transcript/types.py

class TranscriptDocument:
    """
    原始会议文档

    包含完整的会议文字记录，按时间顺序组织，带时间戳和元数据。
    这不是摘要，而是会议本身的完整记录。
    """
    utterances: List[Dict[str, Any]]  # 语音片段列表
    audio_path: str                   # 源音频文件路径
    duration: float                   # 音频总时长（秒）
    asr_provider: str                 # ASR 服务提供商
    created_at: str                   # 文档创建时间（ISO 8601）
    document_path: Optional[str]      # 文档保存路径
    utterance_count: int              # 语音片段数量

    def get_full_text(self) -> str:
        """获取完整文字内容（不含时间戳）"""
        return " ".join(u["text"] for u in self.utterances)
```

#### FormattedTranscript (格式化文稿)

```python
# 文件位置: transcript/formatter.py

@dataclass
class FormattedTranscript:
    """格式化后的文稿"""
    metadata: Dict[str, Any]          # 元数据
    sections: List[Section]            # 章节列表

    # 辅助方法
    def total_duration(self) -> float
    def total_word_count(self) -> int
    def total_paragraph_count(self) -> int

    # 导出方法
    def to_markdown(self) -> str
    def to_plain_text(self) -> str
    def to_html(self) -> str
    def save(self, path: Path, format: str) -> Path
```

#### SummaryResult (会议总结)

```python
# 文件位置: summarizer/types.py

@dataclass
class SummaryResult:
    """
    总结结果

    从转录文档和用户模板生成的结构化总结。
    """
    sections: List[SummarySection]     # 总结章节列表
    transcript_path: str               # 转录文档路径
    template_name: str                 # 模板名称
    template_role: str                 # 模板角色
    llm_provider: str                  # LLM 提供商
    llm_model: str                     # LLM 模型
    processing_time: float             # 处理时间（秒）
    created_at: str                    # 创建时间
    output_path: Optional[str]         # 输出文件路径

    def get_section(self, section_id: str) -> Optional[SummarySection]
    def get_full_text(self) -> str
```

### 3.2 核心函数签名

#### ASR 转写

```python
# 文件位置: asr/transcribe.py

def transcribe(
    audio_path: str,
    provider: Optional[str] = None,          # ASR 提供商 (默认: whisper)
    language: str = "auto",                  # 语言代码
    model_size: str = "base",                # Whisper 模型大小
    auto_build_transcript: bool = False,     # 是否自动构建文档
    enable_postprocess: bool = True          # 是否启用后处理
) -> TranscriptionResult
```

#### 文稿格式化

```python
# 文件位置: transcript/formatter.py

def format_transcript(
    transcript_path: str,                    # 转录文件路径（JSON）
    output_path: str = None,                 # 输出文件路径
    config: FormatterConfig = None,          # 格式化配置
    method: FormatMethod = FormatMethod.RULE_BASED,
    output_format: str = "markdown",         # markdown, plain, html
    progress_callback: Optional[Callable] = None
) -> FormattedTranscript
```

#### 文稿优化

```python
# 文件位置: transcript/refiner.py

def refine_transcript(
    text: str,                               # 原始转录文本
    llm_provider: BaseLLMProvider,           # LLM 提供商
    mode: RefineMode = RefineMode.BALANCED,  # 优化模式
    progress_callback: Optional[Callable] = None
) -> str
```

#### 总结生成

```python
# 文件位置: summarizer/generate.py

def generate_summary(
    transcript: Union[TranscriptDocument, str],  # 文档对象或路径
    template: Union[UserTemplate, str],          # 模板对象或名称
    llm_provider: Optional[BaseLLMProvider] = None,
    save: bool = True,
    output_path: Optional[str] = None
) -> SummaryResult
```

---

## 4. 现有缺陷诊断

### 4.1 标点符号处理缺陷

#### 问题分析

| 层级 | 文件位置 | 现状 | 问题 |
|------|----------|------|------|
| **ASR 后处理** | `asr/postprocess.py` | ❌ 无标点处理 | 只有错别字校正、口语词删除、专有名词修正 |
| **格式化层** | `transcript/formatter.py` | ⚠️ 极简实现 | `_add_missing_punctuation()` 只检查段落结尾 |
| **优化层** | `transcript/refiner.py` | ✅ 有处理 | 依赖 LLM，但未默认启用 |

#### 详细代码分析

**ASR 后处理** (`asr/postprocess.py:226-265`):

```python
class TranscriptPostProcessor:
    # 定义了错别字映射、口语词、专有名词...
    # ❌ 完全没有标点符号处理逻辑

    def correct_utterance(self, utterance: Utterance) -> Utterance:
        text = utterance.text
        # 1. 删除口语填充词
        # 2. 应用错别字校正
        # 3. 专有名词大小写修正
        # 4. 数字/单位格式化
        # 5. 清理多余空格
        # ❌ 没有任何标点符号步骤
```

**格式化层** (`transcript/formatter.py:526-543`):

```python
def _add_missing_punctuation(self, sections: List[Section]):
    """添加缺失的标点符号（简单版本）"""
    for section in sections:
        for para in section.paragraphs:
            text = para.text.strip()
            # ⚠️ 只检查段落结尾，不处理句子内部
            if text and not any(text.endswith(p) for p in self.SENTENCE_ENDINGS):
                if any(w in text for w in ["吗", "呢", "？", "?"]):
                    text += "？"
                elif any(w in text for w in ["啊", "呀", "哦", "！"]):
                    text += "！"
                else:
                    text += "。"
            para.text = text
```

**问题**:
1. 只在段落结尾添加标点，不处理段落内部的句子
2. 无句子边界检测
3. 无语义分析
4. 不处理引号、逗号等内部标点

### 4.2 字词纠错缺陷

#### 现有能力

| 功能 | 文件 | 状态 | 覆盖范围 |
|------|------|------|----------|
| **错别字映射** | `asr/postprocess.py:31-51` | ✅ 实现了 | `COMMON_CORRECTIONS` 字典，仅 10+ 条 |
| **专有名词** | `asr/postprocess.py:54-102` | ✅ 实现了 | `DEFAULT_PROPER_NOUNS` 字典，约 30 条 |
| **同音字** | `asr/postprocess.py:31-51` | ⚠️ 有限 | 仅极少数常见词 |
| **上下文纠错** | ❌ 未实现 | - | 无语义理解 |

#### 具体缺陷

1. **错别字字典太小**: `COMMON_CORRECTIONS` 只有约 10 个映射
2. **无上下文感知**: "一块" → "1元" 这种替换可能是错误的（在某些上下文中）
3. **无 LLM 辅助纠错**: 不利用 LLM 进行语义级纠错
4. **无领域自适应**: 无法根据会议主题调整纠错策略

### 4.3 上下文优化缺陷

#### 问题列表

1. **无说话人识别**: 无法区分不同发言者
2. **无语义分段**: `formatter.py` 的分段仅基于时间间隔
3. **无主题检测**: 无法识别会议主题变化
4. **无指代消解**: "他/她/它" 指代不明时无法修正

### 4.4 Whisper 模型参数配置

#### 当前配置

| 参数 | 默认值 | 影响 |
|------|--------|------|
| `model_size` | `"base"` | 识别精度 |
| `language` | `"auto"` | 语言检测 |
| ❌ `task` | `"transcribe"` (硬编码) | 任务类型 |
| ❌ `word_timestamps` | `False` (未设置) | 词级时间戳 |
| ❌ `initial_prompt` | 未使用 | 引导文本 |
| ❌ `temperature` | 未设置 | 采样随机性 |

#### 缺失功能

1. **无 initial_prompt**: 无法引导模型识别专有名词
2. **无 word_timestamps**: 无法做词级对齐
3. **无 temperature 控制**: 无法平衡准确性和流畅性

---

## 5. 冲突预警

### 5.1 重构文稿生成逻辑的潜在影响

#### 5.1.1 数据格式变化影响

| 变更类型 | 影响范围 | 严重程度 | 缓解方案 |
|----------|----------|----------|----------|
| **Utterance.text 增加标点** | `summarizer/generate.py` | ⚠️ 中等 | LLM 总结通常受益于更好的标点 |
| **断句逻辑变化** | `transcript/formatter.py` | ⚠️ 中等 | 需要重新测试格式化输出 |
| **text 长度变化** (删除口语词) | `summarizer/generate.py` | ✅ 正面 | 减少输入长度，降低成本 |

#### 5.1.2 参会人员视角总结模块依赖分析

```python
# 文件位置: summarizer/generate.py

def generate_summary(
    transcript: Union[TranscriptDocument, str],
    template: Union[UserTemplate, str],
    llm_provider: Optional[BaseLLMProvider] = None,
    ...
) -> SummaryResult:
    # ...
    # 关键依赖: 获取转录文本
    transcript_text = transcript_doc.get_full_text()  # ⚠️ 直接使用拼接文本

    # 构建提示词
    user_prompt = create_user_prompt(template, transcript_text, context)

    # 调用 LLM
    response = llm_provider.chat(system_prompt=system_prompt, user_prompt=user_prompt)
```

**依赖关系**:
```
Utterance.text → get_full_text() → user_prompt → LLM → SummaryResult
```

**影响分析**:

1. **如果 Utterance.text 格式发生变化** (如添加标点):
   - ✅ 正面: LLM 理解更好，总结质量提升
   - ⚠️ 注意: 如果删除了过多内容，可能丢失信息

2. **如果断句逻辑变化** (如增加句子边界):
   - ✅ 正面: 更好的句子结构
   - ⚠️ 注意: 需要确保 `get_full_text()` 的拼接逻辑正确

3. **如果删除口语词**:
   - ✅ 正面: 减少噪音，总结更简洁
   - ⚠️ 注意: 需要保留关键语气词 (如 "吗"、"吧" 表示疑问/建议)

#### 5.1.3 具体冲突点

| 文件 | 依赖项 | 冲突描述 |
|------|--------|----------|
| `summarizer/generate.py` | `TranscriptDocument.get_full_text()` | ⚠️ 依赖文本拼接，如果格式变化需要验证 |
| `summarizer/pipeline.py` | `asr/transcribe.py` | ✅ 独立模块，无直接冲突 |
| `template/render.py` | `transcript_text` | ⚠️ 使用纯文本，格式变化无影响 |
| `transcript/export.py` | `FormattedTranscript` | ⚠️ 如果格式化逻辑变化，导出格式会变化 |

### 5.2 格式化输出依赖

```python
# 文件位置: transcript/formatter.py:101-144

def to_markdown(self) -> str:
    lines = []
    lines.append("# 会议文稿")
    # ...
    for section in self.sections:
        for para in section.paragraphs:
            lines.append(para.text)  # ⚠️ 直接使用 para.text
```

**影响**: 如果重构改变了 `Paragraph.text` 的格式，Markdown 输出会变化。

### 5.3 测试依赖

```bash
# 需要更新的测试文件
tests/test_asr_transcribe.py      # ASR 后处理测试
tests/test_transcript_build.py    # 文档构建测试
tests/test_transcript_format.py   # 格式化测试
tests/test_summarizer_generate.py # 总结生成测试
```

---

## 6. 重构建议

### 6.1 标点符号处理改进方案

#### 方案 A: 增强 ASR 后处理 (轻量级)

```python
# 在 asr/postprocess.py 中添加

class PunctuationConfig:
    """标点符号配置"""
    enable_sentence_boundary_detection: bool = True
    enable_punctuation_inference: bool = True
    use_context_rules: bool = True

class EnhancedTranscriptPostProcessor(TranscriptPostProcessor):
    """增强的后处理器"""

    SENTENCE_BOUNDARY_PATTERNS = [
        (r'([，,、])\s*$', '，'),      # 保留逗号
        (r'([。！？])\s*$', r'\1'),    # 保留句末标点
        # 根据停顿时长添加标点
    ]

    def add_punctuation_by_context(
        self,
        utterance: Utterance,
        next_utterance: Optional[Utterance] = None
    ) -> Utterance:
        """
        根据上下文添加标点符号

        规则:
        1. 检查句子结尾是否已有标点
        2. 检查与下一句的停顿时长
        3. 根据语气词添加标点
        4. 根据句子长度和结构添加逗号
        """
        text = utterance.text
        gap = next_utterance.start - utterance.end if next_utterance else 0

        # 句末标点
        if not any(text.endswith(p) for p in self.SENTENCE_ENDINGS):
            if gap > 2.0:  # 长停顿
                if any(w in text for w in ["吗", "呢", "谁", "什么"]):
                    text += "？"
                elif any(w in text for w in ["啊", "呀", "哦", "！"]):
                    text += "！"
                else:
                    text += "。"
            else:  # 短停顿，可能是逗号
                if len(text) > 10:  # 较长句子
                    text += "，"

        # 句内逗号 (简单规则: 长句且有明显的停顿点)
        if len(text) > 20 and '，' not in in text and text[-1] in '。！？':
            # 在连词前后添加逗号
            for conjunction in ['但是', '然后', '所以', '因为', '如果']:
                if conjunction in text:
                    # 简单处理: 只在第一个连词后加逗号
                    text = text.replace(conjunction, conjunction + '，', 1)
                    break

        return Utterance(start=utterance.start, end=utterance.end, text=text)
```

#### 方案 B: 使用 LLM 进行标点修复 (重量级)

```python
# 在 asr/postprocess.py 中添加

def add_punctuation_with_llm(
    utterances: List[Utterance],
    llm_provider: BaseLLMProvider,
    chunk_size: int = 1000
) -> List[Utterance]:
    """
    使用 LLM 添加标点符号

    ⚠️ 注意: 这会增加成本和延迟
    """
    # 将 utterances 拼接为文本块
    # 调用 LLM 处理
    # 将结果重新映射回 utterances
    pass
```

### 6.2 字词纠错改进方案

#### 方案 A: 扩展规则字典

```python
# 在 data/corrections.yaml 中添加更多映射

# 同音字常见错误
同音字映射:
  "咱俩": "我们俩"
  "咋样": "怎么样"
  "那啥": "那个什么"
  "嘎哈": "干什么"

# 语音识别常见错误
语音识别错误:
  "蓝哥": "蓝哥"  # 确保正确
  "智谱": "智谱"
  "GLM": "GLM"

# 数字/单位
数字单位:
  "一块": "1元"
  "两块": "2元"
  "三块": "3元"
  "几块": "几元"
```

#### 方案 B: LLM 辅助纠错

```python
def correct_with_llm(
    text: str,
    llm_provider: BaseLLMProvider,
    domain: Optional[str] = None
) -> str:
    """
    使用 LLM 进行上下文感知的纠错

    Args:
        text: 原始文本
        llm_provider: LLM 提供商
        domain: 领域提示 (如 "tech", "education", "finance")
    """
    domain_hint = f"这是一个关于{domain}的会议记录。" if domain else ""
    prompt = f"""{domain_hint}
请修正以下文本中的错别字，不要改变其他内容:
{text}

只返回修正后的文本，不要解释。"""
    # ...
```

### 6.3 上下文优化改进方案

#### 方案 A: 语义分段

```python
# 在 transcript/formatter.py 中添加

class FormatMethod(Enum):
    RULE_BASED = "rule_based"
    SEMANTIC = "semantic"  # 新增: LLM 语义分段

class TranscriptFormatter:
    def _format_semantic(self, utterances: List[Dict]) -> FormattedTranscript:
        """
        使用 LLM 进行语义分段

        考虑因素:
        - 话题变化
        - 讨论阶段
        - 逻辑结构
        """
        # 1. 先用规则方法生成初步结构
        initial = self._format_rule_based(utterances)

        # 2. 使用 LLM 优化分段
        # 3. 重新组织段落
        pass
```

#### 方案 B: 说话人识别 (长期)

```python
# 未来扩展: 添加说话人识别

@dataclass
class Utterance:
    start: float
    end: float
    text: str
    speaker: Optional[str] = None  # 新增:说话人标识

# 可以使用 pyannote.audio 等工具
```

### 6.4 Whisper 参数优化

```python
# 在 asr/providers/whisper.py 中添加

class WhisperProviderConfig:
    """Whisper 配置"""
    model_size: str = "small"  # 升级到 small (精度更高)
    language: str = "zh"       # 明确指定中文
    task: str = "transcribe"
    word_timestamps: bool = True  # 启用词级时间戳
    temperature: float = 0.0      # 降低随机性

    # 新增: 引导提示
    initial_prompt: str = "这是一段会议记录，发言者讨论了项目进度、技术方案和行动计划。"

    # 新增: 热词 (专有名词)
    hotwords: List[str] = ["GLM", "智谱AI", "蓝哥", ...]
```

---

## 7. 附录

### 7.1 项目文件结构

```
meeting_intelligence/
├── asr/                          # ASR 模块
│   ├── __init__.py
│   ├── transcribe.py             # 转写接口
│   ├── types.py                  # Utterance, TranscriptionResult
│   ├── postprocess.py            # 后处理器 (规则引擎)
│   └── providers/
│       ├── __init__.py
│       ├── base.py               # BaseASRProvider 抽象类
│       └── whisper.py            # Whisper 实现
│
├── audio/                        # 音频处理模块
│   ├── __init__.py
│   ├── extract_audio.py          # 音频提取 (ffmpeg)
│   ├── preprocess.py             # 音频预处理
│   └── types.py                  # ProcessedAudio
│
├── transcript/                   # 文稿模块
│   ├── __init__.py
│   ├── types.py                  # TranscriptDocument
│   ├── build.py                  # 文档构建
│   ├── load.py                   # 文档加载
│   ├── export.py                 # 文档导出
│   ├── formatter.py              # 格式化器 (规则)
│   └── refiner.py                # 优化器 (LLM)
│
├── summarizer/                   # 总结模块
│   ├── __init__.py
│   ├── types.py                  # SummaryResult, SummarySection
│   ├── generate.py               # 总结生成
│   ├── export.py                 # 总结导出
│   ├── pipeline.py               # 端到端流程
│   └── llm/
│       ├── __init__.py
│       ├── base.py               # BaseLLMProvider
│       ├── openai.py             # OpenAI 实现
│       ├── anthropic.py          # Anthropic 实现
│       ├── glm.py                # GLM (智谱) 实现
│       └── mock.py               # Mock 实现 (测试)
│
├── template/                     # 模板模块
│   ├── __init__.py
│   ├── types.py                  # UserTemplate
│   ├── defaults.py               # 默认模板
│   ├── manager.py                # 模板管理器
│   └── render.py                 # 提示词渲染
│
├── input/                        # 输入模块
│   ├── __init__.py
│   ├── upload_audio.py
│   ├── upload_video.py
│   └── record_audio.py
│
├── meeting_intelligence/         # 主包
│   ├── __init__.py
│   ├── __main__.py               # CLI 入口
│   └── config.py                 # 配置管理
│
├── data/                         # 数据目录
│   ├── raw_audio/                # 原始音频
│   ├── transcripts/              # 转录结果 (JSON)
│   ├── summaries/                # 总结结果 (JSON)
│   ├── formatted/                # 格式化文稿 (MD)
│   ├── templates/                # 用户模板
│   └── proper_nouns.yaml         # 专有名词配置
│
├── tests/                        # 测试目录
│   ├── test_asr_transcribe.py
│   ├── test_audio_extract.py
│   ├── test_transcript_build.py
│   ├── test_summarizer_generate.py
│   └── ...
│
├── requirements.txt
├── .env.example
├── CLAUDE.md
├── README.md
├── STATUS.md
└── MEETING_ASSISTANT_STATUS.md   # 本文档
```

### 7.2 环境配置

```bash
# 必需的环境变量

# LLM API Keys (至少配置一个)
export OPENAI_API_KEY=sk-xxx
export ANTHROPIC_API_KEY=sk-ant-xxx
export ZHIPU_API_KEY=your-key

# 可选配置
export DEFAULT_LLM_PROVIDER=glm           # openai, anthropic, glm
export DEFAULT_LLM_MODEL=glm-4-flash      # gpt-4, claude-3-opus, glm-4-plus
export WHISPER_MODEL_SIZE=small           # tiny, base, small, medium, large
```

### 7.3 CLI 命令速查

```bash
# 处理音频/视频
python -m meeting_intelligence process meeting.mp3 --template product-manager
python -m meeting_intelligence process meeting.mp4 --template developer --provider glm

# 从转录文本生成总结
python -m meeting_intelligence summarize transcript.txt --template general

# 格式化文稿
python -m meeting_intelligence format transcript.json --output formatted.md

# 优化文稿
python -m meeting_intelligence refine transcript.txt --mode balanced --provider glm

# 列出模板
python -m meeting_intelligence template list
python -m meeting_intelligence template show product-manager
```

---

## 8. 总结

### 8.1 当前状态

| 模块 | 状态 | 完成度 | 备注 |
|------|------|--------|------|
| 音频处理 | ✅ 完成 | 100% | ffmpeg 集成完善 |
| ASR 识别 | ✅ 完成 | 95% | Whisper 集成，可添加 faster-whisper |
| ASR 后处理 | ⚠️ 部分 | 60% | 错别字校正有，但标点处理缺失 |
| 文档构建 | ✅ 完成 | 100% | JSON 结构完善 |
| 格式化 | ⚠️ 部分 | 70% | 规则分段有，标点处理简单 |
| 优化 | ✅ 完成 | 90% | LLM 优化器实现完善 |
| 总结生成 | ✅ 完成 | 100% | 多模板、多 LLM 支持 |

### 8.2 关键发现

1. **标点符号处理**: 这是最大的缺陷。ASR 输出通常没有标点，但当前代码仅在格式化层做了极简处理。

2. **字词纠错**: 有基础的规则引擎，但覆盖范围有限，无上下文感知。

3. **上下文优化**: 有 LLM 优化器 (`refiner.py`)，但未在默认流程中启用。

4. **参会人员视角总结模块**: 对文本格式变化有一定抗性（LLM 处理），但需要确保不丢失关键信息。

### 8.3 重构优先级

| 优先级 | 任务 | 预计工作量 | 影响 |
|--------|------|------------|------|
| **P0** | 标点符号处理增强 | 2-3天 | 大幅提升可读性 |
| **P1** | 扩展错别字字典 | 1天 | 降低错误率 |
| **P2** | Whisper 参数优化 | 0.5天 | 提升识别精度 |
| **P3** | LLM 优化器集成到默认流程 | 1天 | 整体质量提升 |
| **P4** | 语义分段 | 3-5天 | 结构化改进 |

---

**文档版本**: v1.0
**审计人员**: Claude (AI 全栈架构师)
**审核日期**: 2026-02-27
