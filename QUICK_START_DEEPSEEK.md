# 🚀 DeepSeek 快速启动卡片

## ⚡ 3 步启用真实 AI 总结

### 1️⃣ 获取 API Key
```
访问：https://platform.deepseek.com/api_keys
创建 API Key
复制：sk-xxxxxxxxxxxxx
```

### 2️⃣ 填写配置
编辑：`backend/.env` 第 17 行

```bash
OPENAI_API_KEY=sk-你真实的api_key
```

### 3️⃣ 启动测试
```bash
# 验证配置
cd backend
python test_deepseek_config.py

# 启动后端
python -m uvicorn main:app --reload --port 8000

# 启动前端
start_jinni.bat
```

---

## ✅ 验证成功标志

**后端日志应显示**：
```
[BACKEND] using REAL LLM for summary generation
[BACKEND] llm_provider: openai
[BACKEND] OpenAI URL: https://api.deepseek.com/v1
[LLM] OpenAI summary generated: length=1234
```

**测试验证**：
- ✅ 不同音频 → 不同总结
- ✅ 不同模板 → 不同结构
- ✅ 总结基于实际内容

---

## 📋 配置文件位置

**主配置**：`backend/.env`
```
第 10 行：LLM_PROVIDER=openai
第 17 行：OPENAI_API_KEY=sk-你的key  ← 修改这里
第 18 行：OPENAI_BASE_URL=https://api.deepseek.com/v1
第 19 行：OPENAI_MODEL=deepseek-chat
```

**测试工具**：`backend/test_deepseek_config.py`
```bash
python test_deepseek_config.py
```

---

## 💰 费用参考

- 1 次总结：¥0.01-0.05
- 100 次总结：¥1-5
- 1000 次总结：¥10-50

---

## 🛠️ 快速修复

**问题**：后端日志显示 `using MOCK`
```
解决：检查 API Key 是否正确填写
```

**问题**：`OpenAI API error: status=401`
```
解决：API Key 无效，重新生成并填写
```

**问题**：配置验证失败
```
解决：运行 python test_deepseek_config.py
```

---

## 📚 详细文档

- `DEEPSEEK_SETUP.md` - 详细配置步骤
- `DEEPSEEK_CONFIG_SUMMARY.md` - 完整配置报告
- `REAL_LLM_GUIDE.md` - 真实 LLM 使用指南

---

**状态**: ⚠️ 等待填写 API Key
**启用**: 填写 API Key 后立即生效
