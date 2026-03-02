# Meeting Intelligence - 环境设置指南

本文档说明如何设置 AI Meeting Assistant V1 的开发环境。

---

## 系统要求

### Python 版本
- **Python 3.10+** (推荐 3.12)

### 外部依赖
- **FFmpeg** - 音频/视频处理

---

## 1. 安装 FFmpeg

FFmpeg 是必需的外部依赖，用于音频提取和处理。

### Ubuntu/Debian (WSL)
```bash
sudo apt-get update
sudo apt-get install ffmpeg
```

### macOS
```bash
brew install ffmpeg
```

### Windows
1. 下载 FFmpeg: https://ffmpeg.org/download.html
2. 解压并添加到系统 PATH

### 验证安装
```bash
ffmpeg -version
ffprobe -version
```

---

## 2. 克隆项目

```bash
git clone <repository-url>
cd Meeting_intelligence
```

---

## 3. 创建虚拟环境

```bash
# 创建虚拟环境
python3 -m venv .venv

# 激活虚拟环境
# Linux/macOS:
source .venv/bin/activate
# Windows:
.venv\Scripts\activate
```

---

## 4. 安装依赖

```bash
pip install -r requirements.txt
```

### 依赖说明

| 类别 | 依赖 | 用途 |
|------|------|------|
| **LLM Providers** | `openai` | OpenAI GPT 支持 |
| | `anthropic` | Anthropic Claude 支持 |
| | `zhipuai` | 智谱 GLM 支持 |
| **ASR** | `openai-whisper` | 本地语音识别 |
| **配置** | `python-dotenv` | 环境变量加载 |
| | `pyyaml` | YAML 配置文件 |
| **CLI** | `rich` | 终端美化 |
| | `tqdm` | 进度条显示 |
| **测试** | `pytest` | 单元测试 |

---

## 5. 配置 API Keys

### 5.1 创建 .env 文件

```bash
# 复制示例配置
cp .env.example .env
```

### 5.2 编辑 .env 文件

至少配置一个 LLM Provider 的 API Key：

```bash
# 使用 GLM (智谱 AI) - 推荐，国内访问快
ZHIPU_API_KEY=your-key-here
DEFAULT_LLM_PROVIDER=glm
DEFAULT_LLM_MODEL=glm-4-flash

# 或使用 OpenAI
OPENAI_API_KEY=sk-xxx
DEFAULT_LLM_PROVIDER=openai
DEFAULT_LLM_MODEL=gpt-4o-mini

# 或使用 Anthropic
ANTHROPIC_API_KEY=sk-ant-xxx
DEFAULT_LLM_PROVIDER=anthropic
DEFAULT_LLM_MODEL=claude-3-5-sonnet-20241022
```

### 5.3 获取 API Keys

| Provider | 获取地址 | 说明 |
|----------|----------|------|
| **Zhipu AI** | https://open.bigmodel.cn/usercenter/apikeys | 国内推荐，价格优惠 |
| **OpenAI** | https://platform.openai.com/api-keys | 需要国际网络 |
| **Anthropic** | https://console.anthropic.com/ | 需要国际网络 |

---

## 6. 验证安装

### 6.1 运行测试

```bash
pytest tests/ -v
```

预期输出：`413 passed`

### 6.2 测试 CLI

```bash
python -m meeting_intelligence --help
```

预期输出：命令帮助信息

### 6.3 测试模板列表

```bash
python -m meeting_intelligence template list
```

---

## 7. 快速开始

### 处理音频文件

```bash
python -m meeting_intelligence process data/raw_audio/meeting.mp3 --template general
```

### 处理视频文件

```bash
python -m meeting_intelligence process data/raw_audio/meeting.mp4 --template product-manager
```

### 从转录文本生成摘要

```bash
python -m meeting_intelligence summarize data/output/transcript.md --template executive
```

---

## 8. 目录结构

```
Meeting_intelligence/
├── .env                    # 环境变量配置 (创建此文件)
├── .env.example            # 配置示例
├── requirements.txt        # Python 依赖
├── CLAUDE.md              # AI 开发指令
├── README.md              # 项目说明
├── meeting_intelligence/  # 主包
├── asr/                   # ASR 模块
├── audio/                 # 音频处理
├── transcript/            # 转录模块
├── summarizer/            # 摘要模块
├── template/              # 模板系统
├── tests/                 # 测试
├── data/                  # 数据目录
│   ├── raw_audio/        # 输入音频
│   ├── transcripts/      # 转录结果
│   └── summaries/        # 摘要结果
└── docs/                  # 文档
```

---

## 9. 常见问题

### Q: 测试失败 "No module named 'xyz'"
**A**: 确保虚拟环境已激活，重新运行 `pip install -r requirements.txt`

### Q: ffmpeg not found
**A**: 确保已安装 FFmpeg 并在系统 PATH 中

### Q: API Key 错误
**A**: 检查 .env 文件是否正确配置，确保 API Key 有效

### Q: Whisper 模型下载慢
**A**: 首次运行会自动下载模型，可使用镜像加速或手动下载

---

## 10. 下一步

- 阅读 `docs/README.md` 了解项目文档结构
- 阅读 `docs/progress/` 了解最新开发进度
- 运行 `python -m meeting_intelligence --help` 查看所有可用命令

---

*更新时间: 2026-03-02*
