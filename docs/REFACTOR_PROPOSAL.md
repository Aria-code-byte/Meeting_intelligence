# 文稿生成模块重构方案

> **创建日期**: 2026-02-27
> **目标**: 解决文稿无标点、错别字及缺乏语境感知问题

---

## 1. 重构概览

### 1.1 修改文件清单

| 文件 | 修改类型 | 优先级 |
|------|----------|--------|
| `asr/providers/base.py` | 扩展接口 | P0 |
| `asr/providers/whisper.py` | 添加 initial_prompt | P0 |
| `asr/transcribe.py` | 集成 LLM 增强 | P0 |
| `asr/types.py` | 新增配置类型 | P1 |

### 1.2 数据流变化

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          重构后的数据流                                   │
└─────────────────────────────────────────────────────────────────────────┘

音频文件
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│ WhisperProvider.transcribe()                                  │
│   - 使用 initial_prompt 引导识别                               │
│   - 返回原始 Utterance 列表                                     │
└─────────────────────────────────────────────────────────────┘
    │
    ▼ 原始 Utterances (无标点、有错别字)
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│ _apply_llm_enhancement()  [新增函数]                          │
│                                                               │
│   输入: List[Utterance] (原始)                                │
│   输出: List[Utterance] (增强后)                              │
│                                                               │
│   步骤:                                                       │
│   1. 按时间顺序分块 (智能分块策略)                             │
│   2. 对每个块调用 LLM 进行增强                                 │
│   3. 将增强文本映射回原始 Utterance 结构                        │
│   4. 保持时间戳不变                                            │
└─────────────────────────────────────────────────────────────┘
    │
    ▼ 增强 Utterances (有标点、无错别字)
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│ (可选) 规则后处理 postprocess_transcript()                    │
│   - 专有名词修正                                              │
│   - 数字格式化                                                │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│ TranscriptionResult                                          │
│   - utterances: List[Utterance]  [结构不变，内容增强]         │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
TranscriptDocument / SummaryResult  [无需修改]
```

---

## 2. WhisperProvider 增强

### 2.1 配置类扩展

```python
# 文件位置: asr/types.py (新增)

@dataclass
class WhisperConfig:
    """Whisper 配置"""
    model_size: str = "small"
    language: str = "zh"  # 明确指定中文，提升准确率
    temperature: float = 0.0  # 降低随机性

    # 新增: 引导提示词
    initial_prompt: Optional[str] = None
    # 默认提示词模板
    DEFAULT_INITIAL_PROMPT = (
        "这是一段中文会议记录，发言者讨论了项目进度、技术方案和行动计划。"
        "专有名词包括：GLM、智谱AI、GitHub、Docker 等。"
    )

    # 热词支持 (faster-whisper)
    hotwords: Optional[List[str]] = None
```

### 2.2 WhisperProvider 修改

```python
# 文件位置: asr/providers/whisper.py

class WhisperProvider(BaseASRProvider):
    """
    Whisper ASR 提供商 (增强版)

    新增功能:
    - initial_prompt 支持
    - temperature 控制
    - hotwords 支持 (faster-whisper)
    """

    def __init__(
        self,
        model_size: str = "small",
        use_api: bool = False,
        api_key: str = None,
        config: WhisperConfig = None
    ):
        """
        初始化 Whisper 提供商

        Args:
            model_size: 模型大小
            use_api: 是否使用 API
            api_key: API key
            config: Whisper 配置 (新增)
        """
        self.model_size = model_size
        self.use_api = use_api
        self.api_key = api_key
        self.config = config or WhisperConfig(model_size=model_size)
        self._local_available = self._check_local_whisper()

    def _transcribe_local(
        self,
        audio_path: str,
        language: str
    ) -> List[Utterance]:
        """
        使用本地 Whisper 转写 (增强版)

        新增参数:
        - initial_prompt: 引导 Whisper 识别专有名词和风格
        - temperature: 控制输出随机性
        """
        if not self._local_available:
            raise RuntimeError("本地 Whisper 未安装")

        try:
            import whisper

            # 加载模型
            model = whisper.load_model(self.model_size)

            # 语言参数处理
            language_arg = None if language == "auto" else language

            # 准备转写参数
            transcribe_kwargs = {
                "language": language_arg,
                "word_timestamps": False,
            }

            # 新增: initial_prompt
            if self.config.initial_prompt:
                transcribe_kwargs["initial_prompt"] = self.config.initial_prompt

            # 新增: temperature
            if self.config.temperature is not None:
                transcribe_kwargs["temperature"] = self.config.temperature

            # 转写
            result = model.transcribe(audio_path, **transcribe_kwargs)

            # 转换为 Utterance 格式
            utterances = []
            for segment in result.get("segments", []):
                text = segment["text"].strip()
                if text:
                    utterances.append(Utterance(
                        start=segment["start"],
                        end=segment["end"],
                        text=text
                    ))

            return utterances

        except Exception as e:
            raise RuntimeError(f"Whisper 转写失败: {e}")
```

---

## 3. LLM 增强处理 - 核心逻辑

### 3.1 分块策略

**挑战**: LLM 有 token 限制，需要将长文本分块处理，但需要：
1. 保持语义完整性（不在句子中间分块）
2. 保持时间戳对齐（处理后能映射回原始 Utterance）
3. 处理边界问题（块之间的衔接）

**解决方案**: 按时间窗口分块 + 重叠缓冲

```python
# 文件位置: asr/transcribe.py (新增)

def _split_utterances_into_chunks(
    utterances: List[Utterance],
    max_duration: float = 300.0,  # 每块最大时长（秒）
    overlap_duration: float = 10.0  # 重叠时长（秒）
) -> List[List[Utterance]]:
    """
    将 utterances 划分为适合 LLM 处理的块

    策略:
    1. 按时间顺序遍历
    2. 累积时长直到 max_duration
    3. 在"停顿点"（gap > 3秒）进行分割
    4. 下一块包含 overlap_duration 的重叠内容

    Args:
        utterances: 原始 utterance 列表
        max_duration: 单块最大时长
        overlap_duration: 块之间重叠时长

    Returns:
        分块后的 utterance 列表的列表
    """
    if not utterances:
        return []

    chunks = []
    current_chunk = []
    current_duration = 0.0
    last_end_time = 0.0

    # 重叠缓冲区：记录上一块末尾的 utterances
    overlap_buffer = []

    for i, utt in enumerate(utterances):
        gap = utt.start - last_end_time if last_end_time > 0 else 0
        utt_duration = utt.end - utt.start

        # 检查是否需要开始新块
        should_split = (
            current_duration >= max_duration and  # 超过最大时长
            gap > 3.0  # 且有停顿（不在句子中间分割）
        )

        if should_split and current_chunk:
            # 保存当前块
            chunks.append(current_chunk.copy())

            # 将当前 utterance 加入重叠缓冲区
            overlap_buffer = [utt]

            # 开始新块
            current_chunk = []
            current_duration = overlap_buffer[0].end - overlap_buffer[0].start

            # 查找更多重叠内容
            for j in range(i + 1, min(i + 20, len(utterances))):
                next_utt = utterances[j]
                if next_utt.start - overlap_buffer[-1].end < overlap_duration:
                    overlap_buffer.append(next_utt)
                else:
                    break

            current_chunk = overlap_buffer.copy()
            current_duration = sum(
                u.end - u.start for u in current_chunk
            )
            overlap_buffer = []
        else:
            # 加入当前块
            current_chunk.append(utt)
            current_duration += utt_duration + gap
            last_end_time = utt.end

    # 添加最后一个块
    if current_chunk:
        chunks.append(current_chunk)

    return chunks
```

### 3.2 LLM 增强处理

```python
# 文件位置: asr/transcribe.py (新增)

@dataclass
class LLMEnhancementConfig:
    """LLM 增强配置"""
    enabled: bool = False  # 是否启用 LLM 增强
    max_duration_per_chunk: float = 300.0  # 单块最大时长
    overlap_duration: float = 10.0  # 重叠时长
    temperature: float = 0.3  # LLM 温度（较低以保持稳定性）

    # 增强模式
    mode: str = "balanced"  # conservative, balanced, aggressive

    # 填充词配置
    remove_filler_words: bool = True
    preserved_particles: List[str] = field(default_factory=lambda: ["吗", "呢", "吧", "哦"])


def _apply_llm_enhancement(
    utterances: List[Utterance],
    llm_provider: BaseLLMProvider,
    config: LLMEnhancementConfig,
    progress_callback: Optional[Callable[[str, int], None]] = None
) -> List[Utterance]:
    """
    使用 LLM 对 ASR 结果进行增强处理

    处理内容:
    1. 添加缺失的标点符号
    2. 修正同音字/错别字
    3. 删除口语填充词（保留语气词）
    4. 优化断句和段落结构

    核心约束:
    - 处理后必须保持 Utterance 结构
    - 时间戳保持不变
    - 语义内容不丢失

    Args:
        utterances: 原始 ASR 识别结果
        llm_provider: LLM 提供商
        config: 增强配置
        progress_callback: 进度回调

    Returns:
        增强后的 Utterance 列表（保持相同数量和时间戳）
    """
    if not utterances:
        return utterances

    def report(stage: str, progress: int):
        if progress_callback:
            progress_callback(stage, progress)

    report("llm_enhancement_start", 0)

    # 步骤 1: 分块
    report("splitting_chunks", 10)
    chunks = _split_utterances_into_chunks(
        utterances,
        max_duration=config.max_duration_per_chunk,
        overlap_duration=config.overlap_duration
    )

    total_chunks = len(chunks)
    report(f"split_into_{total_chunks}_chunks", 20)

    # 步骤 2: 处理每个块
    enhanced_chunks = []
    chunk_index_to_utterance_indices = []  # 记录每个块对应的原始索引

    current_idx = 0
    for chunk_idx, chunk in enumerate(chunks):
        # 记录索引映射
        start_idx = current_idx
        end_idx = start_idx + len(chunk) - 1
        chunk_index_to_utterance_indices.append((start_idx, end_idx))
        current_idx = end_idx + 1

        # 构建块文本（保留时间戳信息用于映射）
        chunk_text = _build_chunk_text_with_markers(chunk)
        chunk_metadata = _build_chunk_metadata(chunk)

        progress = int(20 + (chunk_idx / total_chunks) * 70)
        report(f"processing_chunk_{chunk_idx + 1}", progress)

        # 调用 LLM
        enhanced_text = _enhance_chunk_with_llm(
            chunk_text,
            chunk_metadata,
            llm_provider,
            config
        )

        # 将增强文本映射回 Utterance 结构
        enhanced_utterances = _map_enhanced_text_to_utterances(
            enhanced_text,
            chunk,
            chunk_metadata
        )

        enhanced_chunks.append(enhanced_utterances)

    report("merging_chunks", 95)

    # 步骤 3: 合并块（处理重叠部分）
    final_utterances = _merge_enhanced_chunks(
        enhanced_chunks,
        chunk_index_to_utterance_indices,
        config.overlap_duration
    )

    report("llm_enhancement_complete", 100)

    return final_utterances


def _build_chunk_text_with_markers(utterances: List[Utterance]) -> str:
    """
    构建带标记的块文本

    标记格式:
    [UTTERANCE_START]
    原始文本
    [UTTERANCE_END]

    这样 LLM 可以在增强时保持结构
    """
    lines = []
    for utt in utterances:
        lines.append("[UTTERANCE_START]")
        lines.append(utt.text)
        lines.append("[UTTERANCE_END]")
    return "\n".join(lines)


def _build_chunk_metadata(utterances: List[Utterance]) -> dict:
    """构建块的元数据"""
    return {
        "utterance_count": len(utterances),
        "total_duration": utterances[-1].end - utterances[0].start if utterances else 0,
        "time_range": (utterances[0].start, utterances[-1].end) if utterances else (0, 0)
    }


def _enhance_chunk_with_llm(
    chunk_text: str,
    metadata: dict,
    llm_provider: BaseLLMProvider,
    config: LLMEnhancementConfig
) -> str:
    """
    使用 LLM 增强文本块

    系统提示词设计:
    - 保持语义完整性
    - 添加标点符号
    - 修正错别字
    - 删除口语填充词
    - 保持 [UTTERANCE_START/END] 标记
    """
    # 构建系统提示词
    system_prompt = _build_enhancement_system_prompt(config)

    # 构建用户提示词
    user_prompt = f"""请优化以下会议转录文本（共 {metadata['utterance_count']} 个片段）:

{chunk_text}

要求:
1. 添加适当的标点符号（句号、逗号、问号、感叹号等）
2. 修正明显的错别字
3. 删除无意义的口语填充词（如"就是"、"然后"、"那个"、"这个"等）
4. 保留有意义的语气词（如"吗"、"呢"、"吧"等）
5. 保持 [UTTERANCE_START] 和 [UTTERANCE_END] 标记不变
6. 不要改变原意，不要删除或增加内容

请直接返回优化后的文本，不要添加任何解释。"""

    # 调用 LLM
    response = llm_provider.chat(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        temperature=config.temperature
    )

    return response.content


def _build_enhancement_system_prompt(config: LLMEnhancementConfig) -> str:
    """构建增强系统提示词"""
    base_prompt = """你是一个专业的会议文稿编辑助理。你的任务是对语音转文字生成的会议转录文本进行优化，使其更具可读性。

【核心原则 - 必须遵守】
1. 保持语义完整性：绝对不删减、不压缩、不总结任何内容
2. 保持讲话风格：保持说话人的语气、口吻和表达方式
3. 仅做可读性优化：只处理技术性转录缺陷，不改变内容实质

【严格禁止】
- 禁止总结或压缩内容
- 禁止删减核心信息
- 禁止改变或解释说话人的观点
- 禁止加入主观理解或推测

【允许的处理】
1. 删除无意义的口语填充词（如"就是"、"然后"、"那个"、"这个"等）
2. 修正语音识别导致的错别字（根据上下文判断）
3. 优化断句，使句子更通顺
4. 添加适当的标点符号
5. 保留有意义的语气词（如"吗"、"呢"、"吧"等）"""

    if config.mode == "conservative":
        base_prompt += """

【保守模式 - 仅做最小修改】
仅修正明显的错别字和添加基本标点符号，不删除任何口语词，不断句，不改段落结构。"""
    elif config.mode == "aggressive":
        base_prompt += """

【激进模式 - 深度可读性优化】
可以更积极地删除口语冗余词，优化句子结构，使文本更接近书面语风格。
但仍然不能删减或改变任何实质内容。"""

    return base_prompt


def _map_enhanced_text_to_utterances(
    enhanced_text: str,
    original_utterances: List[Utterance],
    metadata: dict
) -> List[Utterance]:
    """
    将增强后的文本映射回原始 Utterance 结构

    策略:
    1. 解析 [UTTERANCE_START/END] 标记
    2. 按顺序将文本分配给原始 Utterance
    3. 保持原始时间戳不变
    """
    import re

    # 解析标记
    pattern = r'\[UTTERANCE_START\]\s*\n(.*?)\s*\n\[UTTERANCE_END\]'
    matches = re.findall(pattern, enhanced_text, re.DOTALL)

    enhanced_utterances = []

    # 将增强文本映射回原始结构
    for i, original in enumerate(original_utterances):
        if i < len(matches):
            enhanced_text_segment = matches[i].strip()
        else:
            # 如果 LLM 输出的标记数量不匹配，使用原始文本
            enhanced_text_segment = original.text

        enhanced_utterances.append(Utterance(
            start=original.start,
            end=original.end,
            text=enhanced_text_segment
        ))

    return enhanced_utterances


def _merge_enhanced_chunks(
    chunks: List[List[Utterance]],
    index_mapping: List[tuple],
    overlap_duration: float
) -> List[Utterance]:
    """
    合并增强后的块（处理重叠部分）

    策略:
    1. 对于重叠区域，优先使用后面块的输出（因为可能有更多上下文）
    2. 移除重复的 utterances
    """
    if not chunks:
        return []

    if len(chunks) == 1:
        return chunks[0]

    merged = []
    last_end_time = -1

    for i, chunk in enumerate(chunks):
        start_idx, end_idx = index_mapping[i]

        # 找到非重叠的起始位置
        for utt in chunk:
            if utt.start > last_end_time + 1.0:  # 1秒容差
                merged.append(utt)
                last_end_time = utt.end
            else:
                # 这是重叠区域，跳过（已在上一块处理）
                continue

    return merged
```

---

## 4. transcribe.py 主函数修改

```python
# 文件位置: asr/transcribe.py

def transcribe(
    audio_path: str,
    provider: Optional[str] = None,
    language: str = "auto",
    model_size: str = "base",
    auto_build_transcript: bool = False,
    enable_postprocess: bool = True,
    # 新增参数
    whisper_config: WhisperConfig = None,
    llm_enhancement_config: LLMEnhancementConfig = None,
    llm_provider: BaseLLMProvider = None,
    progress_callback: Optional[Callable[[str, int], None]] = None
) -> TranscriptionResult:
    """
    转写音频文件 (增强版)

    新增功能:
    - Whisper initial_prompt 支持
    - LLM 增强处理（标点、错别字、口语词）

    Args:
        audio_path: 音频文件路径
        provider: ASR 提供商
        language: 语言代码
        model_size: Whisper 模型大小
        auto_build_transcript: 是否自动构建文档
        enable_postprocess: 是否启用规则后处理
        whisper_config: Whisper 配置（新增）
        llm_enhancement_config: LLM 增强配置（新增）
        llm_provider: LLM 提供商（启用 LLM 增强时必须）
        progress_callback: 进度回调

    Returns:
        TranscriptionResult
    """
    # 获取音频时长
    from audio.extract_audio import _get_audio_duration
    duration = _get_audio_duration(audio_path)

    # 准备 Whisper 配置
    if whisper_config is None:
        whisper_config = WhisperConfig(model_size=model_size, language=language)

    # 选择提供商
    if provider is None or provider == "whisper":
        asr_provider = WhisperProvider(
            model_size=model_size,
            config=whisper_config
        )
    else:
        raise ValueError(f"不支持的 ASR 提供商: {provider}")

    # 执行转写
    utterances = asr_provider.transcribe(audio_path, language)

    # 新增: LLM 增强处理
    if llm_enhancement_config and llm_enhancement_config.enabled:
        if llm_provider is None:
            raise ValueError("启用 LLM 增强时必须提供 llm_provider")

        utterances = _apply_llm_enhancement(
            utterances=utterances,
            llm_provider=llm_provider,
            config=llm_enhancement_config,
            progress_callback=progress_callback
        )

    # 规则后处理（专有名词、数字格式化等）
    if enable_postprocess:
        try:
            from asr.postprocess import postprocess_transcript
            utterances = postprocess_transcript(utterances)
        except ImportError:
            pass

    # 保存结果
    output_path = _save_result(
        utterances=utterances,
        audio_path=audio_path,
        duration=duration,
        asr_provider=asr_provider.name
    )

    # 构建结果
    result = TranscriptionResult(
        utterances=utterances,
        audio_path=audio_path,
        duration=duration,
        output_path=output_path,
        asr_provider=asr_provider.name,
        timestamp=datetime.now().isoformat()
    )

    # 自动构建原始会议文档
    if auto_build_transcript:
        from transcript.build import build_transcript
        transcript_doc = build_transcript(result, save=True)
        result.transcript_path = transcript_doc.document_path

    return result
```

---

## 5. CLI 调用示例

```bash
# 使用 LLM 增强处理
python -m meeting_intelligence process meeting.mp3 \
    --template product-manager \
    --enable-llm-enhancement \
    --enhancement-mode balanced

# 指定自定义 initial_prompt
python -m meeting_intelligence process meeting.mp3 \
    --whisper-prompt "这是一段关于GLM模型开发的会议记录" \
    --enable-llm-enhancement
```

---

## 6. 降级策略

如果 LLM 调用失败，自动降级到规则模式：

```python
def _apply_llm_enhancement_safe(
    utterances: List[Utterance],
    llm_provider: BaseLLMProvider,
    config: LLMEnhancementConfig
) -> List[Utterance]:
    """带降级的 LLM 增强"""
    try:
        return _apply_llm_enhancement(utterances, llm_provider, config)
    except Exception as e:
        import warnings
        warnings.warn(f"LLM 增强失败，降级到规则模式: {e}")
        # 降级到规则模式
        from asr.postprocess import postprocess_transcript
        return postprocess_transcript(utterances)
```

---

## 7. 测试计划

### 7.1 单元测试

```python
# tests/test_llm_enhancement.py

def test_split_utterances_into_chunks():
    """测试分块逻辑"""
    # ...

def test_map_enhanced_text_to_utterances():
    """测试文本映射"""
    # ...

def test_merge_enhanced_chunks():
    """测试块合并"""
    # ...

def test_llm_enhancement_preserves_structure():
    """测试结构保持"""
    original_utterances = [
        Utterance(0.0, 2.5, "大家好"),
        Utterance(2.6, 5.0, "今天讨论项目进度")
    ]

    enhanced = _apply_llm_enhancement(...)

    assert len(enhanced) == len(original_utterances)
    assert enhanced[0].start == original_utterances[0].start
    assert enhanced[0].end == original_utterances[0].end
```

### 7.2 集成测试

```python
def test_full_transcription_with_enhancement():
    """测试完整流程"""
    result = transcribe(
        "test_audio.wav",
        llm_enhancement_config=LLMEnhancementConfig(enabled=True),
        llm_provider=MockLLMProvider()
    )

    # 验证结构
    assert len(result.utterances) > 0
    for utt in result.utterances:
        assert utt.text  # 非空
        assert utt.end > utt.start  # 时间戳有效
```

---

## 8. 性能预估

| 音频时长 | Whisper 耗时 | LLM 增强耗时 | 总耗时 |
|----------|-------------|-------------|--------|
| 10 分钟 | ~30s | ~20s | ~50s |
| 30 分钟 | ~90s | ~60s | ~150s |
| 60 分钟 | ~180s | ~120s | ~300s |

*注: LLM 耗时取决于模型和分块数量*

---

## 9. 成本预估

| 模型 | 输入/输出 token 成本 | 10分钟音频成本 |
|------|---------------------|----------------|
| glm-4-flash | ¥0.001/1K tokens | ~¥0.05 |
| glm-4-plus | ¥0.01/1K tokens | ~¥0.5 |
| GPT-4 | $0.01/1K tokens | ~$0.1 |

---

**文档版本**: v1.0
**创建日期**: 2026-02-27
