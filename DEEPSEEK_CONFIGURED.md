# DeepSeek API 配置完成

**配置时间**: 2026-05-21
**状态**: ✅ 已验证可用

---

## 当前配置

### backend/.env
```bash
AI_SUMMARY_PROVIDER=backend
LLM_PROVIDER=openai
OPENAI_API_KEY=<YOUR_DEEPSEEK_API_KEY>
OPENAI_BASE_URL=https://api.deepseek.com/v1
OPENAI_MODEL=deepseek-chat
```

---

## 验证结果

### LLM Provider 状态
- **类型**: LLMSummaryProvider（真实 LLM）
- **Is Fallback**: False
- **Model**: deepseek-chat

### 性能指标
- **处理时间**: ~2.6 秒
- **总结质量**: 高（结构化、准确、专业）
- **API 状态**: 正常

### 测试脚本
```bash
# 运行验证测试
.venv/bin/python test_deepseek_real.py

# 运行完整测试
.venv/bin/python test_stage_6bc.py
```

---

## 使用方式

### 后端 API 调用
```bash
curl -X POST http://localhost:8000/api/v1/summarize \
  -H "Content-Type: application/json" \
  -d '{
    "transcript": "会议文字稿内容...",
    "template_name": "产品规划会议",
    "template_description": "Q3 产品路线图讨论",
    "template_sections": ["会议概要", "关键决策", "行动项"],
    "template_prompt": "简洁总结"
  }'
```

### 前端调用
```typescript
// summaryGenerationService.ts 已集成
const result = await generateMeetingSummary({
  meetingId,
  transcript,
  templateSnapshot: template
});
```

---

## API 信息

### DeepSeek 平台
- **官网**: https://www.deepseek.com/
- **控制台**: https://platform.deepseek.com/
- **API 文档**: https://platform.deepseek.com/api-docs/

### 定价参考
- **deepseek-chat**: ¥1/M tokens（输入），¥2/M tokens（输出）
- **deepseek-coder**: ¥1/M tokens（输入），¥2/M tokens（输出）

---

## 切换到其他 LLM

### OpenAI 官方
```bash
AI_SUMMARY_PROVIDER=backend
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-openai-key
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini
```

### Anthropic Claude
```bash
AI_SUMMARY_PROVIDER=backend
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-your-key
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
```

### Ollama 本地
```bash
AI_SUMMARY_PROVIDER=backend
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2:7b
```

---

## 故障排查

### LLM 不可用
1. 检查 API Key 是否有效
2. 检查网络连接
3. 查看后端日志：`[LLM] calling OpenAI API...`

### 回退到 Fallback
```bash
# 强制使用 fallback 模式
AI_SUMMARY_PROVIDER=fallback
```

---

*配置完成后，系统会自动使用 DeepSeek 生成高质量会议总结*
