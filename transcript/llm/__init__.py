"""
LLM Enhancement Module - LLM 增强模块

PR3 轻量版：直接 LLM 调用，无复杂协议
PR4 高精度版：单句级增强 + 混合映射策略
"""

# PR3 导出
from transcript.llm.enhancer import (
    LLMTranscriptEnhancer,
    LLMEnhancerConfig,
    EnhancedTranscriptResult,
    PromptTemplate,
    PREDEFINED_TEMPLATES,
    EnhancementError,
    LLMProviderError,
    ParseError,
)

# PR4 导出
from transcript.llm.types import (
    MappingQuality,
    FallbackLevel,
    MappingMethod,
    MappingInfo,
    FallbackInfo,
    ConfidenceBreakdown,
    SentenceMappingResult,
    MultiRoundMetadata,
    MultiRoundResult,
)

from transcript.llm.confidence import (
    ConfidenceCalculator,
    ConfidenceCalculatorConfig,
    calculate_confidence,
)

from transcript.llm.mapper import (
    SentenceMapper,
    ExactMapper,
    EmbeddingMapper,
    PositionMapper,
    HybridMapper,
    create_mapper,
)

from transcript.llm.fallback import (
    FallbackConfig,
    FallbackEngine,
    SentenceCandidate,
    EnhancedSentence,
    apply_fallback,
)

__all__ = [
    # PR3
    "LLMTranscriptEnhancer",
    "LLMEnhancerConfig",
    "EnhancedTranscriptResult",
    "PromptTemplate",
    "PREDEFINED_TEMPLATES",
    "EnhancementError",
    "LLMProviderError",
    "ParseError",
    # PR4 - Types
    "MappingQuality",
    "FallbackLevel",
    "MappingMethod",
    "MappingInfo",
    "FallbackInfo",
    "ConfidenceBreakdown",
    "SentenceMappingResult",
    "MultiRoundMetadata",
    "MultiRoundResult",
    # PR4 - Confidence
    "ConfidenceCalculator",
    "ConfidenceCalculatorConfig",
    "calculate_confidence",
    # PR4 - Mapper
    "SentenceMapper",
    "ExactMapper",
    "EmbeddingMapper",
    "PositionMapper",
    "HybridMapper",
    "create_mapper",
    # PR4 - Fallback
    "FallbackConfig",
    "FallbackEngine",
    "SentenceCandidate",
    "EnhancedSentence",
    "apply_fallback",
]
