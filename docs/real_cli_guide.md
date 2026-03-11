# AI 会议内容理解助手 - 真实版本使用指南

支持真实音视频文件转录和 LLM 总结。

## 功能特性

- **真实 ASR 转录**: 使用 Whisper 模型进行语音识别
- **真实 LLM 总结**: 支持 Mock/智谱/OpenAI/Anthropic
- **多格式支持**: 视频 (.mp4, .mkv, .mov) 和音频 (.mp3, .wav, .m4a)
- **自定义模板**: 创建、编辑、删除总结模板
- **文档输出**: 按 `文件名_类型.txt` 格式命名

## 快速开始

### 安装依赖

```bash
pip install openai-whisper
pip install python-dotenv
```

### 运行 CLI

```bash
# 使用 Mock LLM（演示）
python meeting_cli.py

# 使用智谱 AI
python meeting_cli.py --llm glm

# 使用 OpenAI
python meeting_cli.py --llm openai

# 使用 Anthropic Claude
python meeting_cli.py --llm anthropic
```

### 配置 API Key

创建 `.env` 文件：

```env
# 智谱 AI
ZHIPU_API_KEY=your_zhipu_api_key
DEFAULT_LLM_MODEL=glm-4-flash

# OpenAI
OPENAI_API_KEY=your_openai_api_key
DEFAULT_LLM_MODEL=gpt-4o-mini

# Anthropic
ANTHROPIC_API_KEY=your_anthropic_api_key
DEFAULT_LLM_MODEL=claude-3-5-sonnet-20241022

# Whisper 模型大小
WHISPER_MODEL=base  # tiny/base/small/medium/large
```

## 使用流程

### 1. 上传音视频文件

```
==================================================
  上传音视频文件
==================================================

请输入文件路径（支持 .mp4, .mkv, .mov, .mp3, .wav, .m4a）
提示: 可以直接拖拽文件到终端

文件路径: /path/to/meeting.mp4
✓ 视频文件已加载！
ℹ  文件: meeting.mp4
ℹ  类型: 视频
```

### 2. 生成文字稿

```
==================================================
  生成文字稿
==================================================

正在从视频提取音频...
  [████████████████████████████████] 100%

正在进行语音识别（这可能需要几分钟）...
提示: 首次使用会自动下载 Whisper 模型

✓ 文字稿生成成功！
ℹ  识别片段: 45 条
ℹ  输出文件: meeting_文字稿.txt
```

### 3. 生成会议总结

```
==================================================
  生成会议总结
==================================================

请选择模板：
  1. 通用总结
  2. 大学生视角

请输入序号: 1

正在初始化 LLM 服务...

使用模板：【通用总结】
LLM Provider: glm

正在生成总结...
  [████████████████████████████████] 100%

✓ 会议总结生成成功！
ℹ  输出文件: meeting_通用总结.txt
```

## 输出文件命名

| 文件类型 | 命名格式 | 示例 |
|---------|---------|------|
| 文字稿 | `{文件名}_文字稿.txt` | `meeting_文字稿.txt` |
| 总结 | `{文件名}_{模板名}.txt` | `meeting_通用总结.txt` |

所有文件保存在 `data/outputs/` 目录下。

## 输出文件格式

### 文字稿文件

```text
# 会议文字稿
# 源文件: meeting.mp4
# 生成时间: 2026-03-09T12:34:56
# ASR提供商: whisper
# 识别时长: 180.5秒
# 识别片段: 45条

[0.0s - 3.2s] 大家好，欢迎参加今天的会议
[3.2s - 8.5s] 我们来讨论一下项目进展
...
```

### 总结文件

```text
# 会议总结
# 源文件: meeting.mp4
# 模板: 通用总结
# LLM Provider: glm
# 生成时间: 2026-03-09 12:34:56

## 会议总结
本次会议讨论了...

## 关键要点
- 要点1
- 要点2
...
```

## 支持的 LLM Provider

| Provider | 说明 | 环境变量 |
|---------|------|---------|
| mock | 模拟生成（测试用） | 无需配置 |
| glm | 智谱 AI | `ZHIPU_API_KEY` |
| openai | OpenAI | `OPENAI_API_KEY` |
| anthropic | Anthropic Claude | `ANTHROPIC_API_KEY` |

## Whisper 模型

| 模型 | 大小 | 速度 | 精度 |
|-----|------|-----|-----|
| tiny | ~40MB | 最快 | 较低 |
| base | ~140MB | 快 | 中等 |
| small | ~460MB | 中等 | 较高 |
| medium | ~1.5GB | 慢 | 高 |
| large | ~3GB | 最慢 | 最高 |

设置环境变量：
```env
WHISPER_MODEL=base
```

## 常见问题

### Q: 首次使用很慢？
A: 首次使用会自动下载 Whisper 模型，约 140MB（base 模型）。

### Q: 识别不准确？
A: 尝试更大的模型（small/medium），或确保音频清晰。

### Q: LLM 调用失败？
A: 检查 API Key 配置，使用 `--llm mock` 测试流程。

### Q: 视频文件无法处理？
A: 确保安装了 ffmpeg：
```bash
# Ubuntu/Debian
sudo apt-get install ffmpeg

# macOS
brew install ffmpeg
```
