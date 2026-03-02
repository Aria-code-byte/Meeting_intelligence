# PR4: 高精度语义增强模块 - 设计方案

## 概述

PR4 在 PR3 轻量级 LLM 接入基础上，提升增强精度和语义理解质量。

**核心改进**:
- 单句回退（而非整块回退）
- 精准句子级映射（embedding 相似度）
- 可选多轮增强（highlights、summary）

---

## 1. 目标

| 功能 | PR3 | PR4 |
|------|-----|-----|
| 增强粒度 | 整块 | 单句 |
| 回退粒度 | 整块 | 单句 |
| 映射策略 | 位置映射 | 3级优先（精确/embedding/位置） |
| 置信度 | 二元 | 连续值（多特征加权） |
| 多轮增强 | ❌ | ✅ 可选 |

---

## 2. 文件结构

```
transcript/llm/
├── mapper.py              # 映射引擎基类及实现
│   ├── SentenceMapper (抽象基类)
│   ├── ExactMapper        # 精确匹配（编号）
│   ├── EmbeddingMapper    # Embedding 相似度匹配
│   └── PositionMapper     # 位置回退映射
├── confidence.py          # 置信度计算器
│   └── ConfidenceCalculator
├── multi_round.py         # 多轮增强处理器
│   └── MultiRoundProcessor
└── enhancer.py            # 扩展 LLMTranscriptEnhancer

tests/
├── test_mapper/           # 映射器测试
│   ├── test_exact_mapper.py
│   ├── test_embedding_mapper.py
│   └── test_position_mapper.py
├── test_confidence.py     # 置信度测试
├── test_multi_round.py    # 多轮增强测试
└── test_regression/       # PR3 兼容回归测试
```

---

## 3. LLM 输出协议（关键）

### 3.1 Schema 定义

**Strict 模式**（PR4 hybrid 推荐）:

```json
{
  "sentences": [
    {
      "sentence_index": 0,
      "enhanced_text": "大家好！",
      "llm_notes": "添加了标点"
    },
    {
      "sentence_index": 1,
      "enhanced_text": "今天我们讨论项目进度。",
      "llm_notes": "修正了语法"
    }
  ],
  "model": "gpt-4o-mini",
  "finish_reason": "stop"
}
```

**Lenient 模式**（降级兼容）:

```
纯文本输出，直接走 PositionMapper
```

### 3.2 枚举类型

```python
# 映射质量
class MappingQuality(Enum):
    HIGH = "high"      # 精确匹配
    MEDIUM = "medium"  # embedding 匹配
    LOW = "low"        # 位置回退

# 回退级别
class FallbackLevel(Enum):
    NONE = "none"           # 无回退
    SENTENCE = "sentence"   # 单句回退
    CHUNK = "chunk"         # 整块回退
    FINAL = "final"         # 完全失败

# 映射方法
class MappingMethod(Enum):
    EXACT = "exact"         # JSON 精确匹配
    EMBEDDING = "embedding" # 相似度匹配
    POSITION = "position"   # 位置回退
```

### 3.3 LLM 输出解析规则

| 模式 | 输入 | 解析方式 | 失败行为 |
|------|------|----------|----------|
| `strict` | JSON | 必须符合 schema | 触发 CHUNK fallback |
| `lenient` | 任意 | 尝试 JSON，失败则文本 | 降级到 PositionMapper |

**确定失败条件**:
```python
# ExactMapper 失败条件
def is_valid_llm_output(output: str) -> bool:
    try:
        data = json.loads(output)
        # 必须有 sentences 字段
        if "sentences" not in data:
            return False
        # 每项必须有 sentence_index 和 enhanced_text
        for item in data["sentences"]:
            if "sentence_index" not in item or "enhanced_text" not in item:
                return False
        return True
    except (json.JSONDecodeError, KeyError, TypeError):
        return False
```

### 3.4 责任边界划分

```
┌─────────────────────────────────────────────────────────────┐
│                    责任边界（清晰划分）                      │
├─────────────────────────────────────────────────────────────┤
│ Mapper 职责:                                                 │
│   - LLM 输出 → 对齐到 original_sentences 的候选 enhanced_text│
│   - 产出: mapping_quality, method, trace, similarity        │
│   - 不做回退判断                                             │
├─────────────────────────────────────────────────────────────┤
│ ConfidenceCalculator 职责:                                  │
│   - 计算置信度分数及各特征分值                               │
│   - 产出: confidence, confidence_breakdown                  │
│   - 不做回退判断                                             │
├─────────────────────────────────────────────────────────────┤
│ Fallback 职责:                                               │
│   - 根据阈值/规则选择 enhanced or original                  │
│   - 写入 fallback_level, fallback_reason, fallback_history  │
├─────────────────────────────────────────────────────────────┤
│ 回归 PR3 行为:                                               │
│   - 使用 PositionMapper + chunk fallback                    │
└─────────────────────────────────────────────────────────────┘
```

### 3.5 EnhancedSentence 数据结构优化

```python
@dataclass
class MappingInfo:
    """映射信息（子结构）"""
    quality: MappingQuality
    method: MappingMethod
    trace: Dict[str, Any]
    embedding_similarity: Optional[float] = None

@dataclass
class FallbackInfo:
    """回退信息（子结构）"""
    level: FallbackLevel
    reason: Optional[str] = None
    history: List[str] = field(default_factory=list)

@dataclass
class ConfidenceBreakdown:
    """置信度分解"""
    total: float
    embedding_similarity: Optional[float] = None
    length_ratio: Optional[float] = None
    llm_metadata: Optional[float] = None

@dataclass
class EnhancedSentence:
    # === PR3 字段（保持兼容）===
    sentence_index: int
    start_ms: int
    end_ms: int
    original_text: str
    enhanced_text: str
    confidence: float = 1.0

    # === PR4 新增字段（结构化）===
    mapping: Optional[MappingInfo] = None
    fallback: Optional[FallbackInfo] = None
    scores: Optional[ConfidenceBreakdown] = None
```

### 3.6 配置扩展（完整）

```python
@dataclass
class LLMEnhancerConfig:
    # === PR3 字段 ===
    enabled: bool = False
    provider: str = "openai"
    model: str = "gpt-4o-mini"
    fallback_on_error: bool = True
    template_name: str = "general"

    # === PR4 新增字段 ===

    # 单句回退控制
    enable_per_sentence_fallback: bool = False  # 默认 False 保持 PR3 行为
    confidence_threshold: float = 0.6
    confidence_weights: Dict[str, float] = field(
        default_factory=lambda: {
            "embedding_similarity": 0.6,
            "length_ratio": 0.2,
            "llm_metadata_score": 0.2
        }
    )

    # 映射策略
    mapping_strategy: str = "hybrid"  # exact / embedding / position / hybrid
    embedding_model: str = "text-embedding-3-small"
    embedding_similarity_threshold: float = 0.7
    enable_embedding_cache: bool = True

    # JSON 解析模式
    strict_json_mode: bool = False  # True: 解析失败触发 CHUNK fallback
                                     # False: 降级到 lenient 模式

    # Multi-round 增强
    enable_multi_round: bool = False
    multi_round_tasks: List[str] = field(default_factory=list)
    multi_round_tolerance: str = "continue"  # continue / stop / skip

    # 性能优化
    enable_parallel_chunks: bool = True
    embedding_batch_size: int = 32
```

---

## 4. 映射策略（三级优先级）

### 4.1 Hybrid 映射流程

```
┌─────────────────────────────────────────────────────────────┐
│                     Hybrid 映射流程                          │
└─────────────────────────────────────────────────────────────┘

Step 1: ExactMapper（优先级 HIGH）
    ├── LLM 输出 JSON 格式（带 sentence_index）
    ├── 直接按编号映射
    └── mapping_quality = HIGH, confidence ≈ 0.95

    ↓ 失败（JSON 解析失败或 schema 不符）

Step 2: EmbeddingMapper（优先级 MEDIUM）
    ├── 构建 similarity_matrix [orig_len x llm_len]
    ├── 匈牙利算法/贪心匹配（一对一）
    ├── 相似度 >= 0.7 且顺序一致性检查
    └── mapping_quality = MEDIUM, confidence ≈ 0.75

    ↓ 失败（匹配率 < 60% 或乱序严重）

Step 3: PositionMapper（优先级 LOW - 兜底）
    ├── PR3 方案：按标点分割 + 位置映射
    └── mapping_quality = LOW, confidence = 0.5
```

### 4.2 EmbeddingMapper 匹配算法（具体）

```python
class EmbeddingMapper(SentenceMapper):
    """基于 embedding 相似度的一对一匹配"""

    def map(self, enhanced_text, original_sentences) -> List[SentenceMappingResult]:
        # Step 1: 分割增强文本为句子列表
        llm_sentences = self._split_into_sentences(enhanced_text)

        # Step 2: 批量计算 embeddings（带缓存）
        orig_embeddings = self._get_embeddings([s["text"] for s in original_sentences])
        llm_embeddings = self._get_embeddings(llm_sentences)

        # Step 3: 构建相似度矩阵 [N x M]
        similarity_matrix = cosine_similarity(orig_embeddings, llm_embeddings)

        # Step 4: 匈牙利算法找最优一对一匹配
        row_ind, col_ind = linear_sum_assignment(-similarity_matrix)

        # Step 5: 过滤低相似度匹配 + 顺序一致性检查
        results = []
        for orig_idx, llm_idx in zip(row_ind, col_ind):
            sim = similarity_matrix[orig_idx, llm_idx]

            # 阈值过滤
            if sim < self.config.embedding_similarity_threshold:
                continue

            # 顺序一致性检查（防止乱序）
            if not self._check_order_consistency(orig_idx, results):
                continue

            results.append({
                "sentence_index": orig_idx,
                "enhanced_text": llm_sentences[llm_idx],
                "embedding_similarity": sim
            })

        # Step 6: 匹配率检查
        match_rate = len(results) / len(original_sentences)
        if match_rate < 0.6:
            # 匹配率过低，触发 PositionMapper
            return PositionMapper().map(enhanced_text, original_sentences)

        return results

    def _check_order_consistency(self, orig_idx, existing_results):
        """检查顺序一致性（防止严重乱序）"""
        if not existing_results:
            return True
        last_idx = existing_results[-1]["sentence_index"]
        # 允许小幅跳跃（±2），但不允许大范围乱序
        return abs(orig_idx - last_idx) <= 2
```

**失败定义**:
- 匹配率 < 60% → 触发 PositionMapper
- 乱序严重（跳跃 > 2）→ 跳过该匹配
- 相似度 < 0.7 → 跳过该匹配

### 4.3 边界情况处理

| 场景 | 处理方式 |
|------|----------|
| LLM 两句合成一句 | one-to-one 匹配后，剩余 llm 句子追加到最后 |
| LLM 一句拆成两句 | one-to-one 匹配，剩余原句使用原文 |
| 中英混合/标点差异 | PositionMapper 时增加 lenient 模式容错 |
| 完全乱序 | 匹配率低，触发 PositionMapper |

---

## 5. 置信度计算

### 5.1 多特征加权公式（含缺失处理）

```
# 权重重归一：缺失特征时按比例分配权重
available_features = {
    "embedding_similarity": (0 if None else value),
    "length_ratio": score,
    "llm_metadata": score
}

# 动态权重重归一
total_weight = sum(weights[k] for k in available_features.keys() if available_features[k] is not None)
renormalized_weights = {k: weights[k] / total_weight for k in available_features.keys()}

# 计算最终置信度
confidence = sum(
    available_features[k] * renormalized_weights[k]
    for k in available_features.keys()
)
```

**缺失特征处理**:
| 场景 | embedding_similarity | 处理方式 |
|------|---------------------|----------|
| ExactMapper | None | 权重重分配到 length_ratio (0.5) + llm_metadata (0.5) |
| PositionMapper | None | 同上 |
| EmbeddingMapper | 有值 | 使用原权重 0.6/0.2/0.2 |

### 5.2 length_ratio_score 具体函数

```python
def calculate_length_ratio_score(original: str, enhanced: str) -> float:
    """
    长度比率得分（clamp 到 [0, 1]）

    理想范围: 原文长度的 0.8 - 1.5 倍
    """
    orig_len = len(original)
    enh_len = len(enhanced)

    if orig_len == 0:
        return 0.0 if enh_len == 0 else 0.3

    ratio = enh_len / orig_len

    # 分段函数
    if 0.8 <= ratio <= 1.5:
        return 1.0  # 理想范围
    elif 0.5 <= ratio < 0.8:
        # 线性插值: 0.5 → 0.6, 0.8 → 1.0
        return 0.6 + (ratio - 0.5) * (1.0 - 0.6) / (0.8 - 0.5)
    elif 1.5 < ratio <= 3.0:
        # 线性插值: 1.5 → 1.0, 3.0 → 0.2
        return 1.0 - (ratio - 1.5) * (1.0 - 0.2) / (3.0 - 1.5)
    else:
        # 过度压缩或扩展
        return 0.2 if ratio > 3.0 else 0.3
```

### 5.3 ConfidenceCalculator 类

```python
class ConfidenceCalculator:
    def __init__(self, config: LLMEnhancerConfig):
        self.base_weights = config.confidence_weights

    def calculate(
        self,
        original: str,
        enhanced: str,
        embedding_similarity: Optional[float] = None,
        llm_metadata: Optional[Dict] = None
    ) -> ConfidenceBreakdown:
        """
        Returns:
            ConfidenceBreakdown (含 total 和各特征分值)
        """
        scores = {}

        # 特征 1: Embedding 相似度（可选）
        scores["embedding_similarity"] = embedding_similarity

        # 特征 2: 长度比率（必须有）
        scores["length_ratio"] = calculate_length_ratio_score(original, enhanced)

        # 特征 3: LLM 元数据（可选）
        scores["llm_metadata"] = self._parse_llm_metadata(llm_metadata)

        # 权重重归一
        available = {k: v for k, v in scores.items() if v is not None}
        total_weight = sum(self.base_weights.get(k, 0) for k in available.keys())
        renormalized = {k: self.base_weights.get(k, 0) / total_weight for k in available.keys()}

        # 计算总分
        total = sum(available[k] * renormalized[k] for k in available.keys())

        return ConfidenceBreakdown(
            total=total,
            embedding_similarity=scores.get("embedding_similarity"),
            length_ratio=scores["length_ratio"],
            llm_metadata=scores.get("llm_metadata")
        )
```

---

## 6. 回退策略（统一优先级）

### 6.1 规则优先级

```
┌─────────────────────────────────────────────────────────────┐
│                    回退规则优先级                            │
├─────────────────────────────────────────────────────────────┤
│ Priority 0: LLM 调用失败/响应不可解析                         │
│   - API 错误、超时                                           │
│   - strict_mode=True 且 JSON 解析失败                        │
│   → CHUNK fallback（整块回退，保 PR3 兼容）                   │
├─────────────────────────────────────────────────────────────┤
│ Priority 1: 单句级质量问题                                   │
│   - confidence < threshold (0.6)                             │
│   - embedding_similarity < threshold (0.7，仅当有 embedding) │
│   - length_ratio 异常 (>3.0 或 <0.3)                         │
│   → SENTENCE fallback（单句回退）                            │
├─────────────────────────────────────────────────────────────┤
│ Priority 2: 继续处理                                        │
│   - 无质量问题 → 接受增强文本                                │
│   - 继续下一句                                              │
└─────────────────────────────────────────────────────────────┘
```

### 6.2 配置字段

```python
@dataclass
class LLMEnhancerConfig:
    # ... 其他字段 ...

    # JSON 解析模式
    strict_json_mode: bool = False  # True: 解析失败触发 CHUNK fallback
                                     # False: 降级到 lenient 模式
```

### 6.3 处理流程

```python
def process_chunk_with_fallback(
    chunk: Chunk,
    sentences: List[Sentence],
    config: LLMEnhancerConfig
) -> List[EnhancedSentence]:

    # Priority 0: LLM 调用
    try:
        llm_output = call_llm(...)
    except LLMError as e:
        if config.fallback_on_error:
            return chunk_fallback(chunk, sentences, reason="llm_call_failed")
        else:
            raise

    # Priority 0a: JSON 解析
    if config.strict_json_mode:
        if not is_valid_llm_output(llm_output):
            return chunk_fallback(chunk, sentences, reason="json_parse_failed")
    else:
        # Lenient 模式：尝试解析，失败则降级
        if not is_valid_llm_output(llm_output):
            mapper = PositionMapper()  # 降级
        else:
            mapper = ExactMapper()
    else:
        mapper = select_mapper(config.mapping_strategy)

    # 映射
    mapping_results = mapper.map(llm_output, sentences)

    # Priority 1: 单句质量检查
    enhanced_sentences = []
    for result in mapping_results:
        # 计算置信度
        breakdown = confidence_calculator.calculate(
            original=result.original_text,
            enhanced=result.enhanced_text,
            embedding_similarity=result.embedding_similarity
        )

        # 判断是否回退
        if breakdown.total < config.confidence_threshold:
            # 单句回退
            enhanced_sentences.append(create_fallback_sentence(
                sentence_index=result.sentence_index,
                original_text=result.original_text,
                fallback_level=FallbackLevel.SENTENCE,
                fallback_reason="low_confidence",
                scores=breakdown
            ))
        elif (result.embedding_similarity is not None
              and result.embedding_similarity < config.embedding_similarity_threshold):
            # 语义偏离回退
            enhanced_sentences.append(create_fallback_sentence(
                sentence_index=result.sentence_index,
                original_text=result.original_text,
                fallback_level=FallbackLevel.SENTENCE,
                fallback_reason="semantic_drift",
                scores=breakdown
            ))
        else:
            # 接受增强
            enhanced_sentences.append(create_enhanced_sentence(
                result=result,
                scores=breakdown
            ))

    return enhanced_sentences
```

---

## 7. Multi-Round 增强

### 7.1 输出约定

**关键原则**: Round 2+ 不再修改 sentences，只产出附加信息

```python
@dataclass
class EnhancedTranscript:
    # Round 1: 主输出（句子级增强）
    sentences: List[EnhancedSentence]

    # Round 2+: 附加信息（独立存储）
    multi_round_results: List[MultiRoundResult] = field(default_factory=list)
```

**原因**: 保持回归测试稳定，避免 multi-round 影响 sentences 输出

### 7.2 支持的任务

| 任务 | 输出类型 | 优先级 | 是否修改 sentences |
|------|----------|--------|-------------------|
| `highlights` | `List[str]` | 1 | ❌ |
| `summary` | `str` | 2 | ❌ |
| `action_items` | `List[str]` | 3 | ❌ |

### 7.3 失败容忍策略

| 策略 | 行为 |
|------|------|
| `continue` | 单轮失败继续处理下一轮（默认） |
| `stop` | 遇到错误停止处理后续任务 |
| `skip` | 跳过失败的任务，继续处理 |

### 7.4 输出结构示例

```python
result = EnhancedTranscript(
    # Round 1: 主输出
    sentences=[
        EnhancedSentence(sentence_index=0, enhanced_text="大家好！"),
        EnhancedSentence(sentence_index=1, enhanced_text="今天我们讨论项目进度。"),
    ],

    # Round 2+: 附加信息
    multi_round_results=[
        MultiRoundResult(
            task_name="highlights",
            content=["讨论了项目进度", "确定了下一步计划"],
            metadata=MultiRoundMetadata(round=2, tokens_used=150, ...)
        ),
        MultiRoundResult(
            task_name="summary",
            content="本次会议主要讨论了项目进度和相关问题。",
            metadata=MultiRoundMetadata(round=3, tokens_used=100, ...)
        )
    ]
)
```

---

## 8. 数据流

```
┌─────────────────────────────────────────────────────────────┐
│                       PR4 数据流                             │
└─────────────────────────────────────────────────────────────┘

Chunk Sentences (带编号)
        │
        ▼
┌───────────────────────┐
│ LLM → JSON 输出        │
└──────────┬────────────┘
           │
           ▼
┌───────────────────────┐
│ SentenceMapper.map()  │
│ - ExactMapper         │ ← 优先级 1
│ - EmbeddingMapper     │ ← 优先级 2
│ - PositionMapper      │ ← 优先级 3 (兜底)
└──────────┬────────────┘
           │
           ▼
┌───────────────────────┐
│ ConfidenceCalculator  │
│ - 多特征加权           │
└──────────┬────────────┘
           │
           ▼
┌───────────────────────┐
│ Per-Sentence Fallback │
│ - confidence < 0.6    │ → 回退到原文
└──────────┬────────────┘
           │
           ▼
┌───────────────────────┐
│ EnhancedSentence[]    │
│ (混合: 增强 + 回退)    │
└──────────┬────────────┘
           │
           ▼
┌───────────────────────┐
│ MultiRoundProcessor   │ (可选)
│ - highlights          │
│ - summary             │
└───────────────────────┘
```

---

## 9. 性能优化

| 优化项 | 策略 |
|--------|------|
| **Embedding 计算** | 批量计算 (batch_size=32) |
| **缓存** | LRU 缓存同句子 embedding |
| **并行处理** | 多 chunk 并行处理（可选） |
| **JSON 解析** | 多格式兼容（纯 JSON / Markdown / 降级） |

---

## 10. 向后兼容

### 默认配置 = PR3 行为

```python
config = LLMEnhancerConfig(
    enable_per_sentence_fallback = False,    # 整块回退
    mapping_strategy = "simple",             # 位置映射
    enable_multi_round = False,              # 单轮
)
```

### 渐进式升级路径

```
Level 0: PR3（稳定）
    ├── 现有用户，无需改动
    │
Level 1: 启用单句回退
    ├── enable_per_sentence_fallback = True
    └── 收益：部分增强 vs 全部回退
    │
Level 2: 启用精确映射
    ├── mapping_strategy = "hybrid"
    └── 收益：映射准确性提升
    │
Level 3: 完整 PR4
    ├── 全部启用
    └── 收益：最佳质量 + 最大可控性
```

---

## 11. 测试覆盖

### 11.1 边界情况测试（关键）

| 场景 | 测试点 | 预期行为 |
|------|--------|----------|
| **两句话合成一句** | LLM 输出句子数 < 原句数 | 剩余原句使用原文 |
| **一句话拆成两句** | LLM 输出句子数 > 原句数 | one-to-one 匹配，多余的丢弃 |
| **完全乱序** | 相似度矩阵无对角线特征 | 匹配率低，触发 PositionMapper |
| **中英混合** | 原文中英混合，LLM 保持 | PositionMapper lenient 模式容错 |
| **标点差异** | 中文标点 vs 英文标点 | 标点归一化后再分割 |
| **空句子** | LLM 返回空字符串 | 触发单句回退 |
| **超长句子** | 长度比率 > 5.0 | 触发单句回退 (excessive_expansion) |

### 11.2 回归测试（PR3 兼容）

```python
# tests/test_regression/test_pr3_pr4_compatibility.py

def test_pr4_default_config_matches_pr3():
    """PR4 默认配置应与 PR3 输出一致"""
    config_pr4 = LLMEnhancerConfig(
        enable_per_sentence_fallback=False,
        mapping_strategy="simple",
        enable_multi_round=False
    )

    result_pr4 = process_transcript(config_pr4)
    result_pr3 = process_transcript_pr3()

    # 输出应一致
    assert len(result_pr4.sentences) == len(result_pr3.sentences)
    for pr4_s, pr3_s in zip(result_pr4.sentences, result_pr3.sentences):
        assert pr4_s.enhanced_text == pr3_s.enhanced_text
```

### 11.3 其他测试类型

| 测试类型 | 覆盖内容 |
|----------|----------|
| **单元测试** | ExactMapper, EmbeddingMapper, PositionMapper, ConfidenceCalculator |
| **集成测试** | 端到端流程、混合回退场景 |
| **质量测试** | 置信度校准、相似度分布统计 |
| **性能测试** | Embedding 缓存命中率、批量计算加速比 |

---

## 12. 未来扩展（PR5+）

- 流式增强（边生成边验证）
- 用户反馈学习（动态调整 threshold）
- 多语言支持
- 领域适配（医疗、法律）

---

*文档版本: 1.0*
*创建日期: 2026-02-27*
