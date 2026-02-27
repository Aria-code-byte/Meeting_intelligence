"""
Enhanced Transcript Module - 增强版转录文档

此模块为 LLM 增强处理预留结构。
PR1: 仅定义配置结构，不实现任何处理逻辑。
Future PRs (2-5): 将填充 chunking, markup, merge 等逻辑。
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class EnhancedTranscriptConfig:
    """
    Enhanced transcript 处理配置

    PR1 定义此结构，Future PRs 逐步扩展：
    - PR2: 添加 chunker 配置（时间窗口、overlap、漂移）
    - PR3: 添加 markup 协议配置（ID 格式、解析规则）
    - PR4: 添加 merge 策略配置（first-wins/last-wins）
    - PR5: 添加 LLM provider 配置和降级策略
    """
    enabled: bool = False

    # Future fields (PR2-5):
    # chunk_target_seconds: float = 300.0
    # chunk_overlap_seconds: float = 10.0
    # markup_id_prefix: str = "U#"
    # merge_strategy: str = "last-wins"
    # llm_provider: Optional[str] = None
    # fallback_on_error: bool = True


# Future PRs 将添加:
# - class UtteranceChunk
# - class UtteranceMarkup
# - class EnhancedTranscriptParser
# - class EnhancedTranscriptMerger
# - def process_enhanced_transcript()
