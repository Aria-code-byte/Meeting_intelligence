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
- **Web 界面**: 现代化 React + TypeScript + Tailwind CSS UI
- **CLI 支持**: 完整的命令行接口

---

## 快速开始

### 一键启动 Web 界面（推荐）

**现代化 React UI 界面**，提供直观的用户体验：

```bash
# 进入项目目录
cd /mnt/d/projects/Meeting_intelligence

# 启动 Web 界面（后端 + 前端）
chmod +x start_jinni.sh
./start_jinni.sh
```

**访问地址**：
- 前端界面：http://localhost:5173
- 后端 API：http://localhost:8000
- API 文档：http://localhost:8000/docs

**停止服务**：
```bash
chmod +x stop_jinni.sh
./stop_jinni.sh
```

### Web 界面功能

#### 工作台
- 拖拽上传音视频文件（支持 MP3, WAV, MP4, M4A, WEBM）
- 实时处理进度展示
- 自动转录与 AI 总结生成
- 快速查看最近处理结果

#### 会议库
- 查看所有历史会议记录
- 搜索与筛选会议
- 查看会议详情（文字稿 + AI 总结）
- 重新生成总结（可选择不同模板）

#### 模板管理
- 预设 6 种专业模板：
  - 通用会议纪要
  - 产品需求讨论
  - 项目评审
  - 周会总结
  - 客户沟通
  - 面试记录
- 自定义模板创建
- 模板结构预览
- 设置默认模板

---

## 环境要求

### Python 环境
- Python 3.12+ (项目已适配 3.12 特性)
- FFmpeg（音视频处理）
- Node.js 18+ (Web UI 开发)

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

### 安装依赖

```bash
# 进入项目目录
cd /mnt/d/projects/Meeting_intelligence

# 创建虚拟环境（推荐）
python3 -m venv .venv
source .venv/bin/activate  # Linux/macOS

# 安装 Python 依赖
pip install -r requirements.txt

# 安装 Web UI 依赖
cd web_backend/react-ui
npm install
cd ../..
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

**安全提示**：
- 切勿将 `.env` 文件提交到 Git（已添加到 `.gitignore`）
- 如需分享项目，仅分享 `.env.example` 模板文件
- 定期轮换你的 API Keys

---

## CLI 命令行模式

### 交互式 CLI（推荐新手）

```bash
# 进入项目目录
cd /mnt/d/projects/Meeting_intelligence

# 激活虚拟环境
source .venv/bin/activate

# 启动交互式 CLI
python -m meeting_intelligence.cli

# 或指定 LLM 提供商
python -m meeting_intelligence.cli --llm glm
python -m meeting_intelligence.cli --llm deepseek
python -m meeting_intelligence.cli --llm openai
```

**交互式菜单**：
```
===========================================================
  AI 会议内容理解助手
===========================================================

请选择操作：
  1. 上传音视频文件
  2. 生成文字稿
  3. 生成总结
  4. 模板管理
  5. 退出
```

### 极简命令行（推荐批处理）

```bash
# 基础用法（Mock LLM，用于测试）
python -m meeting_intelligence meeting.mp4

# 使用 GLM（智谱 AI）
python -m meeting_intelligence meeting.mp3 --provider glm

# 使用 OpenAI
python -m meeting_intelligence meeting.mp4 --provider openai

# 指定模板
python -m meeting_intelligence meeting.mp4 --provider glm --template product-manager

# 不保存结果
python -m meeting_intelligence meeting.mp3 --no-save
```

**参数说明**：

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `input` | 输入文件路径（必需） | - |
| `--provider`, `-p` | LLM 提供商 | `mock` |
| `--model`, `-m` | LLM 模型名称 | 根据 provider 自动选择 |
| `--template`, `-t` | 模板名称 | `general` |
| `--no-save` | 不保存结果到文件 | False |

---

## 技术栈

### 核心技术
| 类别 | 技术选型 | 用途 |
|------|----------|------|
| **后端语言** | Python 3.12+ | 核心开发语言 |
| **前端框架** | React 18 + TypeScript | 现代化 Web UI |
| **构建工具** | Vite 5 | 快速开发与构建 |
| **样式系统** | Tailwind CSS 3 | 原子化 CSS 框架 |
| **后端框架** | FastAPI | 高性能 API 服务 |
| **测试** | pytest | 单元测试与集成测试 |
| **数据模型** | dataclasses | 类型安全的数据结构 |

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

### 架构特性
- **整数毫秒时间模型**: 避免浮点精度问题
- **确定性分块**: 基于时间窗口的 chunk 划分
- **分层工件**: raw/enhanced 转录分离
- **OpenSpec**: 规范化的变更提案管理

---

## 项目结构

```
meeting_intelligence/
├── web_backend/          # Web 服务
│   ├── react-ui/         # React 前端 UI
│   │   ├── src/
│   │   │   ├── components/  # UI 组件
│   │   │   ├── pages/       # 页面组件
│   │   │   ├── services/    # API 服务
│   │   │   ├── store/       # 状态管理
│   │   │   └── types/       # TypeScript 类型
│   │   ├── package.json
│   │   └── vite.config.ts
│   ├── backend/           # FastAPI 后端
│   │   ├── main.py        # API 入口
│   │   └── routers/       # API 路由
│   └── start_jinni.sh     # 一键启动脚本
├── meeting_intelligence/  # 核心模块
│   ├── input/             # 会议输入模块
│   ├── audio/             # 音频处理模块
│   ├── asr/               # ASR 语音转文字模块
│   ├── transcript/        # 原始会议文档模块
│   │   └── llm/           # 转录增强 LLM 模块
│   ├── template/          # 用户模板系统
│   ├── summarizer/        # LLM 总结引擎
│   ├── cli.py             # 命令行接口
│   └── __main__.py        # 主入口
├── data/                  # 数据存储
│   ├── raw_audio/         # 音频文件
│   ├── transcripts/       # 转写结果
│   ├── templates/         # 用户模板
│   └── summaries/         # 总结结果
├── tests/                 # 测试套件
├── docs/                  # 文档
├── openspec/              # OpenSpec 规范
├── requirements.txt       # Python 依赖
├── start_jinni.sh         # 一键启动脚本
└── stop_jinni.sh          # 停止服务脚本
```

---

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
- **LLM 抽象**: 支持 OpenAI、Anthropic、GLM、DeepSeek、Mock 提供商
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

---

## 开发指南

### Web UI 开发

```bash
# 前端开发（React）
cd web_backend/react-ui
npm run dev          # 启动开发服务器
npm run build        # 构建生产版本

# 后端开发（FastAPI）
cd backend
python main.py       # 启动后端服务
```

### 运行测试

```bash
# 进入项目目录
cd /mnt/d/projects/Meeting_intelligence

# 激活虚拟环境
source .venv/bin/activate

# 运行所有测试
pytest tests/ -v

# 运行特定模块测试
pytest tests/test_asr_transcribe.py -v
```

### 代码风格

- 文件命名: `snake_case.py`
- 函数命名: `snake_case`
- 类命名: `PascalCase`
- 中文注释业务逻辑，英文注释技术实现

---

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
- [x] React Web UI 界面

### 项目里程碑
- **测试覆盖**: 454 个测试用例
- **代码质量**: 防御性编程、完整类型注解
- **文档完善**: 架构决策文档、OpenSpec 变更提案
- **LLM 支持**: OpenAI, Anthropic, GLM, DeepSeek, Mock
- **Web 界面**: 现代化 React + TypeScript + Tailwind CSS

---

## 许可证

MIT License
