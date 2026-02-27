# Transcript Artifact Layering - 架构决策

## 背景

ASR 转录生成的原始文本 (`raw transcript`) 包含时间戳和精确的 utterance 边界，是所有下游处理的基础事实源。任何 LLM 增强处理都应生成独立工件，而非覆盖原始数据。

## 核心原则

### 1. Raw 不可覆盖

```
data/transcripts/transcript_*.json  ← 始终为 ASR 原始输出
```

- `TranscriptionResult.transcript_path` **永远指向** raw ASR transcript
- 任何 LLM 处理后的文本必须写入**新文件**
- 可追溯性：`TranscriptDocument.source_transcript_path` 指向原始 ASR 工件

### 2. Enhanced 分层存储

```
TranscriptionResult
├── transcript_path: str              ← raw ASR (必需)
└── enhanced_transcript_path: str?    ← enhanced output (可选)
```

- enhanced 是独立的、可选的衍生工件
- raw 存在时 enhanced 才有意义
- enhanced 失败可降级到 raw，不影响基础功能

### 3. PR1 纯结构、零行为变化

PR1 **仅**引入数据结构字段，不实现任何处理逻辑：

| 添加项 | 作用 | 实现时机 |
|-------|------|---------|
| `enhanced_transcript_path` | 预留路径字段 | PR1 |
| `source_transcript_path` | 追溯原始工件 | PR1 |
| `enable_enhanced` 参数 | 预留接口 | PR1 |
| Enhanced 文件生成 | PR2-PR5 逐步实现 | Future |

**原因**：小步提交，每步可验证、可回滚。

## PR 递进关系

| PR | 内容 | 交付物 |
|----|------|--------|
| **PR1** | 结构预留 | 字段定义、类型追溯、测试覆盖 |
| **PR2** | 时间分块 | `UtteranceChunker`，支持 overlap、gap 寻找 |
| **PR3** | 标记协议 | `UtteranceMarkup`、解析器、局部回退 |
| **PR4** | 重叠合并 | 确定性 merge 策略 |
| **PR5** | Pipeline 集成 | 端到端流程、降级策略、mock e2e 测试 |

## 兼容性保证

- ✅ 旧版 JSON 缺少新字段时 `from_dict()` 自动兼容（返回 None）
- ✅ 新版 `to_dict()` 仅在字段非 None 时写入（避免 `null` 污染）
- ✅ `enable_enhanced=False`（默认）时行为与原版完全一致
- ✅ `get_full_text()` 保持原样，不受 enhanced 影响
