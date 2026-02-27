# Change: Add Summarizer Module

## Why

前面5个模块已经完成：
- ✓ Input: 会议输入
- ✓ Audio: 音频处理
- ✓ ASR: 语音转文字
- ✓ Transcript: 原始会议文档
- ✓ Template: 用户模板

现在需要最后一个模块将它们整合起来，生成**角色视角的结构化总结**。

这是产品的核心价值实现：**让用户以自己的角色视角重新体验会议**。

## What Changes

- 新增 `summarizer/` 模块
- 实现 `generate_summary()` 函数，整合 transcript + template → summary
- 支持 LLM API（OpenAI、Anthropic 等）
- 实现总结结果持久化
- 实现总结结果导出（JSON、TXT、Markdown）

## Impact

- Affected specs: 新增 `summarizer` 规范
- Affected code:
  - 新增 `summarizer/` 目录
  - 新增 `summarizer/types.py` (SummaryResult 类型)
  - 新增 `summarizer/generate.py` (generate_summary 函数)
  - 新增 `summarizer/llm/` (LLM provider 抽象)
  - 新增 `data/summaries/` 数据目录
- Dependencies: 依赖 `transcript/` 和 `template/` 模块
