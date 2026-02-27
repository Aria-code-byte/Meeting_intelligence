# Change: Add Transcript Module

## Why

ASR 模块已经能够将音频转换为带时间戳的文字片段（utterances），但这些片段是原始的、碎片化的数据。用户需要一个完整的、结构化的**原始会议文档**，它应该包含：

1. 完整的文字记录（按时间顺序组织）
2. 清晰的时间戳信息
3. 可读的段落结构
4. 元数据（音频来源、时长、ASR提供商等）

这个模块是数据流中的关键中间层：**ASR → Raw Transcript → Template → Summary**

## What Changes

- 新增 `transcript/` 模块
- 实现 `build_transcript()` 函数，从 ASR 结果生成结构化文档
- 实现文档持久化（保存到 `data/transcripts/`）
- 实现文档加载和导出功能
- 支持多种导出格式（JSON、TXT、Markdown）

## Impact

- Affected specs: 新增 `transcript` 规范
- Affected code:
  - 新增 `transcript/` 目录
  - 新增 `transcript/types.py` (TranscriptDocument 类型)
  - 新增 `transcript/build.py` (build_transcript 函数)
  - 新增 `transcript/export.py` (导出功能)
  - 新增 `data/transcripts/` 数据目录
- Dependencies: 依赖 `asr/` 模块的 `TranscriptionResult`
