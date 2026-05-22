# AI Meeting Assistant - CLI 使用指南

## 🚀 快速启动

### 方法1：使用批处理文件（推荐）
双击运行 `run_cli.bat`

### 方法2：命令行启动
```bash
python meeting_cli.py --llm deepseek
```

### 方法3：使用其他LLM提供商
```bash
# 使用Mock LLM（演示/测试）
python meeting_cli.py --llm mock

# 使用智谱AI
python meeting_cli.py --llm glm

# 使用OpenAI
python meeting_cli.py --llm openai

# 使用Anthropic
python meeting_cli.py --llm anthropic

# 使用DeepSeek（默认）
python meeting_cli.py --llm deepseek
```

## 📋 功能菜单

CLI版本提供以下功能：

1. **上传音频/视频文件** - 支持多种格式的音视频文件上传
2. **编辑会议记录** - 查看和编辑转录的文本记录
3. **生成会议总结** - 使用AI生成会议总结
4. **模板管理** - 管理总结模板
5. **退出** - 退出程序

## 🔧 环境配置

程序会自动读取项目根目录下的 `.env` 文件，需要的配置项：

```env
# 默认LLM提供商
DEFAULT_LLM_PROVIDER=deepseek

# DeepSeek API Key
DEEPSEEK_API_KEY=your-api-key-here

# Whisper模型大小
WHISPER_MODEL_SIZE=base

# 首次运行标记
FIRST_RUN=false
```

## 📝 使用流程

1. 启动CLI程序
2. 选择菜单选项（输入数字1-5）
3. 按照程序提示操作
4. 查看生成的结果文件（保存在 `data/outputs` 目录）

## 🎯 特色功能

- ✅ 支持真实音频/视频文件转录
- ✅ 多种LLM提供商支持
- ✅ 断点续传功能
- ✅ 模板自定义
- ✅ 结果文件自动保存

## 🛠️ 故障排除

### 编码问题
如果中文显示乱码，请确保：
- Windows终端使用UTF-8编码
- 可以运行 `chcp 65001` 设置编码

### API密钥问题
确保 `.env` 文件中配置了正确的API密钥

### 依赖包问题
确保已安装所有依赖：
```bash
pip install -r requirements.txt
```

## 📂 输出文件

生成的文件保存在 `data/outputs` 目录：
- `{文件名}_文字稿.txt` - 转录文本
- `{文件名}_通用总结.txt` - AI总结
- `{文件名}_enhanced_cache.json` - 缓存文件

---

**版本**: v1.0  
**更新日期**: 2026-05-16  
**状态**: ✅ 可用