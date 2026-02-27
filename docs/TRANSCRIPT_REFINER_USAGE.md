# Transcript Refiner 模块使用说明

## 功能概述

`transcript_refiner.py` 是会议转录文本优化模块，用于在不改变原意的前提下，优化语音转文字生成的会议转录文本的可读性。

## 核心特性

### ✅ 允许的操作
- 修正明显错别字
- 删除口语冗余词（如"就是"、"然后"、"那个"、"这个"）
- 优化断句和段落结构
- 添加适当的标点符号
- 保持讲话风格和语义完整性

### ❌ 严格禁止
- 删减核心内容
- 改变或解释说话人观点
- 加入主观理解或推测
- 将口语转换为书面语风格
- 进行总结或压缩

## 使用方式

### 1. CLI 命令

#### 规则优化（快速，不调用 LLM）
```bash
python -m meeting_intelligence refine transcript.md --rules-only
```

#### LLM 优化（三种模式）
```bash
# 平衡模式（推荐）
python -m meeting_intelligence refine transcript.md --mode balanced

# 保守模式（仅修正错别字）
python -m meeting_intelligence refine transcript.md --mode conservative

# 激进模式（深度优化）
python -m meeting_intelligence refine transcript.md --mode aggressive
```

#### 指定输出文件
```bash
python -m meeting_intelligence refine transcript.md --output refined.md
```

#### 使用不同的 LLM Provider
```bash
python -m meeting_intelligence refine transcript.md \
    --provider openai \
    --model gpt-4
```

### 2. Python API

```python
from transcript.refiner import refine_transcript, RefineMode
from summarizer.llm import GLMProvider

# 创建 LLM provider
llm = GLMProvider(model='glm-4-flash')

# 优化文本
refined = refine_transcript(
    text=raw_text,
    llm_provider=llm,
    mode=RefineMode.BALANCED
)

print(refined)
```

### 3. 文件处理

```python
from transcript.refiner import refine_transcript_file
from summarizer.llm import GLMProvider

llm = GLMProvider()

# 直接优化文件
output_path = refine_transcript_file(
    input_path='transcript.md',
    output_path='refined.md',
    llm_provider=llm,
    mode='balanced'
)
```

### 4. 纯规则模式（最快）

```python
from transcript.refiner import refine_with_rules

# 不调用 LLM，仅使用规则优化
refined = refine_with_rules(raw_text)
```

## 优化模式对比

| 模式 | 描述 | 适用场景 |
|------|------|----------|
| `conservative` | 仅修正错别字，不做其他修改 | 需要保留原始风格的场合 |
| `balanced` | 删除冗余词，优化断句，保持风格 | 通用场景（推荐） |
| `aggressive` | 深度优化，接近书面语 | 需要正式文档的场合 |

## 输出示例

### 输入（原始转录）
```
就是然后呢我觉的就是这个这个今天的课程的内容是支撑着蓝哥舞从一个东北的18线骗案的小镇来自这个平穷的是吧下岗职工在家庭的孩子到考上了985
```

### 输出（优化后）
```
今天课程的内容是支撑着蓝哥，从东北18线县城的贫困下岗职工家庭的孩子，到考上985。
```

## 完整示例

```bash
# 完整处理流程：格式化 + 优化
python -m meeting_intelligence format transcript.json --output formatted.md
python -m meeting_intelligence refine formatted.md --output refined.md --mode balanced

# 或者使用 LLM 直接优化
python -m meeting_intelligence refine transcript_clean.md \
    --mode balanced \
    --output refined_transcript.md
```

## 注意事项

1. **API 速率限制**：智谱 API 有速率限制，建议一次处理一个文件
2. **文本长度**：大文件会自动分块处理，可能需要较长时间
3. **保持原意**：优化后的文本应与原文语义一致
4. **人工审核**：重要文档建议人工审核优化结果
