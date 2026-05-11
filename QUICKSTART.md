# AI Meeting Assistant - 快速开始指南

> 5 分钟完成安装和配置

---

## 📦 方式一：自动安装（推荐）

### Linux / macOS

```bash
# 1. 进入项目目录
cd Meeting-Intelligence

# 2. 运行安装脚本
bash installer/install.sh

# 3. 启动程序
./run.sh
```

### Windows

```batch
# 1. 打开 PowerShell，进入项目目录
cd Meeting-Intelligence

# 2. 运行安装脚本
installer\install.bat

# 3. 启动程序
run.bat
```

---

## 🛠️ 方式二：手动安装

### 前置要求

- **Python 3.10+**
- **FFmpeg**（音频处理）

### 安装步骤

```bash
# 1. 创建虚拟环境
python3 -m venv .venv

# 2. 激活虚拟环境
source .venv/bin/activate  # Linux/macOS
# 或
.venv\Scripts\activate     # Windows

# 3. 安装依赖
pip install -r requirements.txt
pip install tqdm python-dotenv

# 4. 运行配置向导（首次）
python installer/setup_wizard.py

# 5. 启动程序
python -m meeting_intelligence.cli
```

---

## 🎯 首次配置

配置向导会引导你完成以下设置：

### 1. 选择界面模式

- **CLI 交互式菜单**：推荐新手，菜单导航
- **Web 界面**：推荐高级用户，浏览器访问

### 2. 选择 LLM 服务商

| 服务商 | 特点 | 推荐场景 |
|-------|------|---------|
| DeepSeek | 速度快，价格优 | **推荐**（默认） |
| 智谱 GLM | 国产，稳定 | 备选 |
| OpenAI | 国际领先 | 需要国际网络 |
| 测试模式 | 不消耗 API | 测试功能 |

### 3. 配置 API Key（可选）

- 可以现在配置，也可以稍后在 `.env` 文件中配置
- 获取 API Key：
  - DeepSeek: https://platform.deepseek.com/api_keys
  - 智谱: https://open.bigmodel.cn/usercenter/apikeys
  - OpenAI: https://platform.openai.com/api-keys

### 4. 选择 Whisper 模型

| 模型 | 大小 | 速度 | 准确率 |
|-----|-----|------|--------|
| tiny | ~40MB | 最快 | 较低 |
| base | ~140MB | 快 | 中等（推荐） |
| small | ~460MB | 中等 | 较高 |
| medium | ~1.5GB | 慢 | 高 |
| large | ~2.9GB | 最慢 | 最高 |

---

## 🚀 开始使用

### CLI 模式

```bash
./run.sh
```

**交互式菜单**：
```
============================================================
  AI 会议内容理解助手 (DeepSeek)
============================================================

请选择操作：
  1. 上传音视频文件
  2. 生成文字稿（含发言人识别）
  3. 生成会议总结
  4. 发言人管理  # 新功能
  5. 模板管理
  6. 退出
```

### Web 模式

```bash
# 自动启动
./run.sh

# 或手动启动
cd web_backend
streamlit run app.py --server.port 8501
```

访问：`http://localhost:8501`

---

## ✨ 新功能：发言人识别

### 自动识别发言人

转录时自动识别不同发言人：

```markdown
[00:00 - 00:15] **发言人 A**: 大家好，欢迎参加会议
[00:15 - 00:30] **发言人 B**: 今天我们讨论项目进度
[00:30 - 00:45] **发言人 A**: 我这边前端已经完成
```

### 发言人管理

在 CLI 中选择「4. 发言人管理」可以：

- 查看所有发言人统计
- 重命名发言人（SPEAKER_00 → 张三）
- 合并发言人（同一人的不同片段）
- 按发言人筛选内容

---

## 📝 基本操作

### 1. 上传文件

```
1. 上传音视频文件
→ 拖拽文件到终端，或输入文件路径
```

### 2. 生成文字稿

```
2. 生成文字稿
→ 自动转录 + 识别发言人
→ 输出：data/outputs/视频名_文字稿.md
```

### 3. 生成总结

```
3. 生成会议总结
→ 选择模板
→ 使用 LLM 生成结构化总结
→ 输出：data/outputs/视频名_模板名_总结.md
```

---

## 📂 文件说明

```
Meeting-Intelligence/
├── installer/           # 安装程序
│   ├── install.sh       # Linux/macOS 安装脚本
│   ├── install.bat      # Windows 安装脚本
│   └── setup_wizard.py  # 配置向导
├── run.sh               # Linux/macOS 启动脚本
├── run.bat              # Windows 启动脚本
├── .env                 # 环境配置（首次运行后生成）
├── .config/             # 用户配置目录
│   ├── preferences.json # 界面偏好
│   └── speakers.json    # 发言人配置
└── data/
    ├── models/          # Whisper 模型缓存
    ├── outputs/         # 输出文件
    │   ├── *_文字稿.md  # 转录结果
    │   └── *_总结.md    # 会议总结
    └── transcripts/     # 原始转录 JSON
```

---

## ⚙️ 配置文件

### .env 文件

```bash
# LLM 配置
DEFAULT_LLM_PROVIDER=deepseek
DEFAULT_LLM_MODEL=deepseek-chat
DEEPSEEK_API_KEY=your-key-here

# Whisper 配置
WHISPER_MODEL_SIZE=base

# 界面模式
UI_MODE=cli
```

### 修改配置

编辑 `.env` 文件，或运行：
```bash
python installer/setup_wizard.py
```

---

## 🐛 常见问题

### 1. FFmpeg 未安装

**Linux**：
```bash
sudo apt-get install ffmpeg
```

**macOS**：
```bash
brew install ffmpeg
```

**Windows**：从 https://ffmpeg.org/download.html 下载

### 2. Python 版本过低

需要 Python 3.10 或更高版本：
```bash
python3 --version
```

### 3. Whisper 模型下载失败

使用国内镜像：
```bash
python scripts/download_whisper_model.py base --mirror
```

### 4. LLM API 速率限制

- 等待 2-3 分钟后重试
- 或切换其他 LLM Provider
- 或检查 API 额度

### 5. 找不到命令

确保已激活虚拟环境：
```bash
source .venv/bin/activate
```

---

## 📖 更多文档

- [完整文档](README.md)
- [优化计划](docs/optimization-plan-2weeks.md)
- [发言人识别](docs/speaker-diarization.md)（待完善）

---

## 💡 提示

1. **首次使用**：运行配置向导，设置默认选项
2. **测试模式**：使用 Mock LLM 测试功能（不消耗 API）
3. **断点续传**：LLM 增强支持断点续传，中断后继续即可
4. **批量处理**：命令行模式支持脚本化批量处理

---

**版本**: 1.0.0
**更新日期**: 2026-05-08
