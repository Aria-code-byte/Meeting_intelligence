# Meeting Intelligence 项目开发进度报告

**报告日期**: 2026-03-02
**项目状态**: 核心模块开发中 (PR1-PR3 已完成，PR4 进行中)
**测试覆盖**: 413 tests passing

---

## 一、项目概述

### 1.1 项目定位

**AI Meeting Assistant V1** - 一个独立的智能模块，将会议音频/视频转换为结构化记录和角色视角摘要。

**核心价值主张**：将会议变为"从你的角色视角重新体验的完整记录"，解决"没时间参会/听不完/摘要不符合需求"的问题。

**产品定位**：不仅是"帮你记住会议"，而是"让你的角色视角重新让会议发生"。

### 1.2 核心功能

```
输入：音频/视频文件 (mp4, mkv, mov, mp3, wav, m4a)
    ↓
[Step 1] 音频提取 - 从视频提取音频
    ↓
[Step 2] ASR 转写 - 语音转文字（带时间戳）
    ↓
[Step 3] 原始转录文档 - 完整、未修改、结构化的会议记录
    ↓
[Step 4] 模板引擎 - 根据用户角色/角度/关注点配置
    ↓
[Step 5] LLM 结构化摘要 - 基于模板的智能摘要
    ↓
输出：原始转录文档 + 角色视角结构化摘要
```

### 1.3 关键概念

| 概念 | 说明 |
|------|------|
| **原始转录文档 (Raw Transcript)** | 会议的"本体" - 完整、未修改、带时间戳的结构化记录。不是摘要，而是会议本身。 |
| **模板 (Template)** | 产品的"灵魂模块" - 定义如何重新体验会议：角色定位、总结角度、重点关注内容。 |
| **结构化摘要 (Structured Summary)** | 基于原始转录和用户模板，由 LLM 生成的输出。结构由模型生成，非硬编码。 |

### 1.4 技术栈

- **语言**: Python 3.12+
- **测试**: pytest
- **核心模式**: dataclasses
- **外部依赖**: FFmpeg (音频处理), ASR服务, LLM API

---

## 二、已完成的 Pull Requests

### PR1: Raw/Enhanced 工件分层 (Commit: 962eb17)

**目标**: 保留原始 ASR 工件，为未来增强版本预留存储路径。

**问题**: 原始 ASR 输出和增强后的转录需要分开存储，避免覆盖原始数据。

**解决方案**:
- 在 `ASRResult` 中新增 `enhanced_transcript_path` 字段
- 在 `TranscriptDocument` 中新增 `source_transcript_path` 字段
- 添加 `enable_enhanced` 开关控制增强功能

**核心改动**:
```
asr/types.py:
    + enhanced_transcript_path: Optional[str]  # 预留给增强版

transcript/types.py:
    + source_transcript_path: Optional[str]    # 指向原始转录

transcript/build.py:
    + enable_enhanced: bool = False            # 增强开关
```

**不变量保证**:
- `transcript_path` 始终指向 raw ASR transcript
- `enhanced_transcript_path` 预留给 future PRs
- `enable_enhanced=False` 时行为 100% 不变

**测试**: 258 passed

---

### PR2: 确定性分块 + 整数毫秒模型 (Commit: a458346)

**目标**: 实现基于时间窗口的分块系统，支持 overlap，使用整数毫秒确保确定性。

**问题**:
1. 长会议需要分块处理
2. 分块之间需要 overlap 保证上下文连续
3. 浮点时间戳导致不确定性

**解决方案**:

**核心数据结构**:
```python
# 时间窗口（整数毫秒）
TimeWindow(start_ms: int, end_ms: int)

# 句子（整数毫秒）
Sentence(sentence_index: int, start_ms: int, end_ms: int, text: str)

# 分块（带实际 overlap 信息）
Chunk(
    chunk_id: int,
    time_window: TimeWindow,
    sentence_indices: List[int],
    actual_overlap_ms_with_previous: int,
    actual_overlap_ms_with_next: int
)
```

**关键算法**:
| 算法 | 功能 |
|------|------|
| `build_fixed_chunks()` | 固定窗口 + overlap，整数毫秒 |
| `match_sentences_to_chunks()` | Sentence 跨 chunk 匹配 |
| `build_chunks_with_overlap()` | 计算 actual_overlap_ms_* |
| `validate_sentences()` | 时间单调性校验 |
| `validate_chunk_progression()` | Chunk 连续性断言 |

**防御性编程**:
- ✅ 时间单调性校验
- ✅ Chunk 连续性断言
- ✅ 循环限制保护 (MAX_CHUNKS=10000)
- ✅ **禁止浮点时间**（所有时间使用 `int` 毫秒）

**测试**: 309 passed (+51)

---

### PR3: 轻量级 LLM 接入 (Commit: a90e5b0)

**目标**: 实现 LLM 转录文本增强，支持多种 provider 和模板。

**问题**: 原始 ASR 转录存在错误（标点、语法、术语），需要 LLM 优化。

**解决方案**:

**核心类**:
```python
class LLMTranscriptEnhancer:
    """LLM 转录文本增强器"""
    def __init__(self, config: LLMEnhancerConfig)
    def enhance(transcript_text: str) -> EnhancedTranscriptResult

class EnhancementProcessor:
    """增强处理器 - PR3 填充"""
    def process_chunk(chunk, sentences) -> Dict[int, EnhancedSentence]
```

**提示词模板系统**:
```python
PREDEFINED_TEMPLATES = {
    "general": "通用优化 - 添加标点、修正语法",
    "technical": "技术会议 - 保留术语、修正格式",
    "executive": "高管汇报 - 提炼要点、规范表达",
    "minimal": "最小改动 - 仅修正明显错误"
}
```

**支持的 LLM Providers**:
- `mock` - 测试用
- `openai` - OpenAI GPT
- `anthropic` - Claude
- `glm` - 智谱 GLM

**错误处理策略**:
- 整块级别 `fallback_on_error`
- LLM 失败 → 使用原文
- 解析失败 → 使用原文

**测试**: 340 passed (+31)

---

## 三、进行中: PR4 高精度语义增强模块

**状态**: 架构设计完成，核心实现进行中

### 3.1 PR4 要解决的问题

| 问题 | PR3 现状 | PR4 目标 |
|------|----------|----------|
| 回退粒度过粗 | 单句失败导致整块回退 | **单句级回退** |
| 映射易误匹配 | 按标点分割+位置映射 | **三级混合映射** |
| 置信度二元化 | 只有"通过/失败" | **多特征加权置信度** |
| 缺乏语义验证 | 无法检测语义偏离 | **Embedding 相似度验证** |

### 3.2 PR4 核心设计

**三级混合映射策略**:
```
Step 1: ExactMapper (优先级 HIGH)
    ├── LLM 返回 JSON (带 sentence_index)
    ├── 直接按编号映射
    └── mapping_quality = HIGH, confidence ≈ 0.95
    ↓ 失败 (JSON 解析失败)
Step 2: EmbeddingMapper (优先级 MEDIUM)
    ├── 构建 similarity_matrix
    ├── 匈牙利算法/贪心匹配
    ├── 相似度 >= 0.7 且顺序一致性
    └── mapping_quality = MEDIUM, confidence ≈ 0.75
    ↓ 失败 (匹配率 < 60%)
Step 3: PositionMapper (优先级 LOW - 兜底)
    ├── PR3 方案：按标点分割 + 位置映射
    └── mapping_quality = LOW, confidence = 0.5
```

**多特征置信度计算**:
```
confidence = 0.6 × embedding_similarity
           + 0.2 × length_ratio
           + 0.2 × llm_metadata
```

**单句级回退**:
- 置信度 < 0.6 → 单句回退
- 相似度 < 0.7 → 单句回退
- 长度比率异常 → 单句回退

### 3.3 PR4 文件结构

```
transcript/llm/
├── types.py           ✅ 数据类型定义（已完成）
├── mapper.py          🚧 映射引擎（进行中）
│   ├── ExactMapper         # JSON 精确匹配
│   ├── EmbeddingMapper     # Embedding 相似度匹配
│   ├── PositionMapper      # 位置回退映射
│   └── HybridMapper        # 三级优先级混合
├── confidence.py      🚧 置信度计算器（进行中）
├── fallback.py        🚧 回退引擎（进行中）
└── __init__.py        ✅ 已更新导出

tests/
├── test_mapper/
│   ├── test_exact_mapper.py       ✅ 已创建
│   └── test_position_mapper.py    ✅ 已创建
├── test_confidence.py              ✅ 已创建
└── test_fallback.py                ✅ 已创建

docs/architecture/
└── pr4-precision-enhancement.md    ✅ 完整设计文档 (782行)

openspec/changes/2026-03-02-pr4-precision-enhancement/
├── proposal.md       ✅ 变更提案
├── tasks.md          ✅ 任务清单
└── specs/llm-precision-enhancement/spec.md  ✅ 规格说明
```

### 3.4 PR4 任务清单

| 模块 | 状态 | 说明 |
|------|------|------|
| types.py | ✅ | 枚举、数据结构定义完成 |
| mapper.py | 🚧 | ExactMapper/PositionMapper 基础完成，EmbeddingMapper 待实现 |
| confidence.py | 🚧 | 骨架待填充 |
| fallback.py | 🚧 | 骨架待填充 |
| 单元测试 | 🚧 | 部分测试文件创建，用例待补充 |
| 集成测试 | ❌ | 待开始 |
| 回归测试 | ❌ | 待开始 |

---

## 四、数据流全景图

```
┌─────────────────────────────────────────────────────────────────┐
│                        完整数据流                                │
└─────────────────────────────────────────────────────────────────┘

音频/视频文件
    ↓
┌─────────────────────┐
│ Audio Processing    │ → ProcessedAudio
└─────────────────────┘
    ↓
┌─────────────────────┐
│ ASR (Whisper)       │ → TranscriptionResult (Utterance[])
│ - 带时间戳          │
│ - speaker_detection │
└─────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────────────┐
│ PR1: Raw/Enhanced 工件分层                                       │
│   - transcript_path → raw ASR                                    │
│   - enhanced_transcript_path → 预留                              │
└─────────────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────────────┐
│ PR2: 确定性分块 (整数毫秒)                                        │
│   - build_fixed_chunks() → Chunk[]                              │
│   - 带 overlap (默认 60s 窗口, 10s 重叠)                         │
└─────────────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────────────┐
│ PR3: LLM 增强 (整块级别)                                         │
│   - LLMTranscriptEnhancer.enhance()                              │
│   - 模板: general/technical/executive/minimal                    │
│   - fallback: 整块回退                                           │
└─────────────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────────────┐
│ PR4: 高精度语义增强 (单句级别) [进行中]                           │
│   - HybridMapper: Exact → Embedding → Position                  │
│   - ConfidenceCalculator: 多特征加权                             │
│   - FallbackEngine: 单句回退                                     │
└─────────────────────────────────────────────────────────────────┘
    ↓
EnhancedTranscript JSON
    ↓
┌─────────────────────────────────────────────────────────────────┐
│ 输出文件                                                         │
│ - data/transcripts/xxx.json      # 原始转录                      │
│ - data/transcripts/xxx_enhanced.json  # 增强转录                │
└─────────────────────────────────────────────────────────────────┘
```

---

## 五、已完成工作总结

### 5.1 核心模块

| 模块 | 文件 | 功能 | 状态 |
|------|------|------|------|
| ASR | `asr/transcribe.py` | Whisper 转写 | ✅ |
| ASR | `asr/types.py` | `TranscriptionResult` | ✅ |
| Transcript | `transcript/build.py` | 构建转录文档 | ✅ |
| Transcript | `transcript/enhanced_builder.py` | PR2 分块逻辑 | ✅ |
| LLM | `transcript/llm/enhancer.py` | PR3 增强器 | ✅ |
| Template | `template/` | 模板系统 | ✅ |
| Summarizer | `summarizer/generate.py` | LLM 摘要 | ✅ |

### 5.2 测试覆盖

| 阶段 | 测试数量 | 新增 |
|------|----------|------|
| 初始 | 248 | - |
| + PR1 | 258 | +10 |
| + PR2 | 309 | +51 |
| + PR3 | 340 | +31 |
| + PR4 (进行中) | 413 | +73 |

### 5.3 架构文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Transcript 工件分层 | `docs/architecture/transcript-artifact-layering.md` | ✅ |
| PR4 精度增强设计 | `docs/architecture/pr4-precision-enhancement.md` | ✅ |

---

## 六、后续工作计划

### 6.1 PR4 剩余任务 (当前优先级)

**Phase 1: 核心模块实现**
- [ ] 完成 `mapper.py`
  - [ ] EmbeddingMapper 实现
  - [ ] HybridMapper 实现
- [ ] 完成 `confidence.py`
  - [ ] 长度比率计算
  - [ ] 多特征加权
  - [ ] 动态权重重归一
- [ ] 完成 `fallback.py`
  - [ ] 单句回退逻辑
  - [ ] 回退历史记录

**Phase 2: 测试覆盖**
- [ ] test_mapper/test_embedding_mapper.py
- [ ] test_confidence.py 完整用例
- [ ] test_fallback.py 完整用例
- [ ] test_regression/test_pr3_pr4_compatibility.py

**Phase 3: 集成与验证**
- [ ] 集成到 `enhanced_builder.py`
- [ ] 端到端测试
- [ ] 性能测试
- [ ] 向后兼容验证

### 6.2 MVP Completion (未开始)

根据 `openspec/changes/2026-02-25-mvp-completion/`，MVP 完成需要：

| 迭代 | 内容 | 状态 |
|------|------|------|
| Iteration 0 | 环境与依赖 (requirements.txt, .env.example) | ❌ |
| Iteration 1 | 核心 LLM 循环验证 | ❌ |
| Iteration 2 | 转录质量优化 (postprocess.py) | ❌ |
| Iteration 3 | LLM Prompt 与解析优化 | ❌ |
| Iteration 4 | CLI 入口点 (__main__) | ❌ |
| Iteration 5 | 配置管理 (config.yaml) | ❌ |
| Iteration 6 | 测试与文档 | ❌ |

### 6.3 V2 功能 (已规划，未实现)

- ❌ PPT 检测与提取
- ❌ 视频分析
- ❌ Slide-Transcript 对齐
- ❌ 向量知识库

---

## 七、OpenSpec 变更提案状态

### 活跃提案

| 提案 | 路径 | 状态 |
|------|------|------|
| MVP Completion | `openspec/changes/2026-02-25-mvp-completion/` | 📋 规划中 |
| PR4 精度增强 | `openspec/changes/2026-03-02-pr4-precision-enhancement/` | 🚧 进行中 |

### 已归档提案

- ✅ add-asr-module
- ✅ add-audio-processing-module
- ✅ add-meeting-input-module
- ✅ add-summarizer-module
- ✅ add-template-module
- ✅ add-transcript-module

---

## 八、关键设计决策

### 8.1 时间模型

**决策**: 所有时间使用整数毫秒 (`int`)，禁止浮点。

**原因**: 避免浮点精度问题，确保确定性。

**影响**:
- `Sentence.start_ms`, `Sentence.end_ms`
- `TimeWindow.start_ms`, `TimeWindow.end_ms`
- 所有时间计算必须使用整数运算

### 8.2 工件分层

**决策**: Raw 和 Enhanced 分开存储，永不覆盖。

**原因**: 保留原始数据，便于调试和回滚。

**影响**:
- `transcript_path` → raw ASR
- `enhanced_transcript_path` → LLM enhanced
- 始终可以追溯到原始数据

### 8.3 增量开发

**决策**: 每个 PR 独立可回滚，渐进式增强。

**原因**: 降低风险，便于调试。

**影响**:
- `enable_enhanced` 开关控制
- PR1-PR3 可以独立启用/禁用
- PR4 向后兼容 PR3

---

## 九、如何继续开发

### 9.1 如果要继续 PR4

```bash
# 查看架构设计
cat docs/architecture/pr4-precision-enhancement.md

# 查看 OpenSpec 任务清单
cat openspec/changes/2026-03-02-pr4-precision-enhancement/tasks.md

# 运行现有测试
pytest tests/test_mapper/ -v
pytest tests/test_confidence.py -v
pytest tests/test_fallback.py -v
```

### 9.2 如果要开始 MVP Completion

```bash
# 查看 MVP 规划
cat openspec/changes/2026-02-25-mvp-completion/proposal.md

# 查看任务清单
cat openspec/changes/2026-02-25-mvp-completion/tasks.md
```

### 9.3 开发约定

- **保持 413 tests passing** - 任何改动不能破坏现有测试
- **整数毫秒时间模型** - 所有时间计算使用 int
- **增量提交** - 每个 PR 保持独立可回滚
- **向后兼容** - PR4 默认配置应与 PR3 输出一致

---

**报告生成时间**: 2026-03-02
**维护者**: Claude (AI Coding Assistant)
**项目路径**: `/mnt/d/projects/Meeting_intelligence`
