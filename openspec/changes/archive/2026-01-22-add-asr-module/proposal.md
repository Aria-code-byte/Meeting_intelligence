# Change: Add ASR (Speech-to-Text) Module

## Why

Phase 1 和 Phase 2 已完成会议输入和音频处理。ASR（自动语音识别）模块是连接音频与会议记录的桥梁，负责：
1. 将音频转换为带时间戳的逐字文本
2. 支持中英文混合识别
3. 为后续的会议文档生成和总结提供结构化数据

## What Changes

- **ADDED**: `asr/transcribe.py` - 语音转文字核心功能
- **ADDED**: `asr/types.py` - 统一的 `TranscriptionResult` 数据结构
- **ADDED**: 支持多种 ASR 提供商的抽象接口
- **ADDED**: 结果持久化到 `data/transcripts/`

## Impact

- **Affected specs**: New capability `asr`
- **Affected code**: Creates new `asr/` module
- **Dependencies**:
  - 依赖 `audio/` 模块（Phase 2）
  - 需要 ASR 服务提供商 API（Whisper/云服务）

## Key Design Decisions

1. **提供商抽象**: 设计统一接口，支持多种 ASR 服务（Whisper 本地/云端、Google、Azure 等）
2. **时间戳优先**: 每句话必须有 start/end 时间，用于后续对齐和分析
3. **结果持久化**: ASR 结果保存为 JSON，便于调试和重用
4. **分块处理**: 支持长音频分块处理，避免超时和内存问题

## Technical Requirements

- 输入: WAV 音频文件（16kHz, mono）
- 输出格式: JSON 包含 `{"start": float, "end": float, "text": string}` 数组
- 支持语言: 中文、英文、中英混合
- 处理时长: 至少支持 2 小时会议
