# 优化计划 - 关键决策确认

> 基于 2026-05-08 用户反馈确认

## ✅ 确认的关键决策

### 1. 默认 LLM Provider
**选择**: DeepSeek（默认）

**原因**: 价格优、速度快、适合国内网络环境

**实施细节**:
```yaml
# 默认配置
llm:
  provider: deepseek
  model: deepseek-chat
  fallback:  # 备选方案
    - glm
    - openai
```

### 2. 打包分发方式
**选择**: PyInstaller 独立可执行文件（优先）

**原因**: 适合普通用户，双击即用，无需 Python 环境

**文件结构**:
```
dist/
├── meeting-assistant-win-x64.exe    # Windows
├── meeting-assistant-macos-arm64    # macOS ARM
├── meeting-assistant-macos-x64      # macOS Intel
└── meeting-assistant-linux          # Linux
```

**打包策略**:
- Python 依赖打包进可执行文件
- FFmpeg 作为内置资源
- Whisper 模型首次使用时下载（减小包体积）

### 3. 启动模式选择
**选择**: 两种都提供，首次启动让用户选择

**首次启动流程**:
```bash
===========================================================
  首次启动 - AI Meeting Assistant
===========================================================

请选择您偏好的界面模式：

  [1] CLI 交互式菜单（推荐新手）
      → 菜单导航、拖拽文件上传、操作简单

  [2] Web 界面（推荐高级用户）
      → 浏览器访问、可视化操作、实时预览

请输入选择 [1-2]: _
```

**记住用户选择**: 保存到配置文件，后续启动直接使用

---

## 🚀 立即可以开始的任务

### 优先级 P0（本周开始）

1. **创建安装脚本框架**
   ```bash
   # 可以立即开始
   mkdir -p installer
   touch installer/install.sh
   touch installer/install.bat
   ```

2. **发言人识别模块技术验证**
   ```bash
   # 验证 pyannote.audio 可行性
   pip install pyannote.audio
   # 测试模型下载流程
   ```

3. **配置向导原型**
   ```bash
   # 创建基础框架
   touch installer/setup_wizard.py
   ```

---

## 📅 调整后的实施计划

### Week 1（核心功能）
| 天数 | 任务 | 交付物 |
|-----|------|--------|
| 1-2 | 安装脚本 + DeepSeek 默认配置 | install.sh/bat |
| 3-4 | 配置向导 + 首次启动选择 | setup_wizard.py |
| 5-7 | 发言人识别（pyannote） | speaker/diarization.py |

### Week 2（产品化）
| 天数 | 任务 | 交付物 |
|-----|------|--------|
| 8-9 | 双模式启动 + 统一入口 | run.sh/bat |
| 10-11 | 发言人管理 UI | speaker/ui.py |
| 12-13 | PyInstaller 打包 | dist/*.exe |
| 14 | 测试 + 文档 | README 更新 |

---

## 🎯 成功指标（基于你的选择）

| 指标 | 目标值 | 测量方式 |
|-----|-------|---------|
| 下载到首次运行 | < 3分钟 | 新用户测试 |
| 安装成功率 | > 95% | 跨平台测试 |
| DeepSeek API 调用成功率 | > 98% | 错误日志统计 |
| 发言人识别准确率 | > 85% | 测试音频验证 |
| 可执行文件体积 | < 200MB | 不含模型 |
| 完整包（含模型） | < 500MB | 含 base 模型 |

---

## 💡 建议的第一步

**今天就可以开始**：

1. 创建发言人识别验证脚本
   ```bash
   # 测试 pyannote.audio 是否可用
   python -c "from pyannote.audio import Pipeline; print('OK')"
   ```

2. 创建 DeepSeek API 验证
   ```bash
   # 确保默认配置可用
   export DEEPSEEK_API_KEY=your-key
   python -m meeting_intelligence.cli --llm deepseek
   ```

3. 设计首次启动界面
   ```bash
   # 创建原型
   touch installer/first_run_wizard.py
   ```

---

**下一步**: 要开始实施吗？我可以帮你创建第一个任务的具体代码。
