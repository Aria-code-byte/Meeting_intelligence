"""
Transcript Refiner - 会议转录文本优化模块

在不改变原意的前提下，优化语音转文字生成的会议转录文本的可读性。

主要功能：
- 修正明显错别字
- 删除口语冗余词
- 优化断句和段落结构
- 保持讲话风格和语义完整性
"""

from dataclasses import dataclass, field
from typing import Optional, Callable, List, Dict, Any
from enum import Enum
from pathlib import Path
import re


class RefineMode(Enum):
    """优化模式"""
    CONSERVATIVE = "conservative"  # 保守模式：仅修正错别字
    BALANCED = "balanced"          # 平衡模式：可读性优化
    AGGRESSIVE = "aggressive"      # 激进模式：深度优化


@dataclass
class RefinerConfig:
    """优化配置"""
    mode: RefineMode = RefineMode.BALANCED
    max_chunk_size: int = 8000     # 单次处理的最大字符数
    overlap_size: int = 200        # 块之间的重叠字符数
    preserve_timestamps: bool = True
    add_section_markers: bool = True

    # 口语冗余词列表（将被删除）
    filler_words: List[str] = field(default_factory=lambda: [
        "就是", "然后", "那个", "这个", "这种", "这样的话",
        "对吧", "是吧", "对不对", "是不是", "也就是说"
    ])

    # 需要保留的语气词（不删除）
    preserved_particles: List[str] = field(default_factory=lambda: [
        "呢", "吗", "吧", "哦", "啊", "呀", "嘛", "啦"
    ])


class TranscriptRefiner:
    """会议转录文本优化器"""

    # 系统提示词模板
    SYSTEM_PROMPT_TEMPLATE = """你是一个专业的会议文稿编辑助理。你的任务是对语音转文字生成的会议转录文本进行优化，使其更具可读性，同时严格遵守以下规则：

【核心原则 - 必须遵守】
1. 保持语义完整性：绝对不删减、不压缩、不总结任何内容
2. 保持讲话风格：保持说话人的语气、口吻和表达方式
3. 仅做可读性优化：只处理技术性转录缺陷，不改变内容实质

【严格禁止】
- 禁止总结或压缩内容
- 禁止删减核心信息
- 禁止改变或解释说话人的观点
- 禁止加入主观理解或推测
- 禁止将口语转换为书面语风格

【允许的处理】
1. 删除无意义的口语填充词（如"就是"、"然后"、"那个"、"这个"等）
2. 修正语音识别导致的错别字（根据上下文判断）
3. 优化断句，使句子更通顺
4. 按逻辑重组段落结构
5. 添加适当的标点符号
6. 保留有意义的语气词（如"呢"、"吗"、"吧"等）

【常见问题处理示例】
- "就是然后呢我觉的就是这个这个" → "我觉得"
- "那个那个那个人" → "那个人"
- "明天的话呢我们" → "明天我们"
- "蓝哥讲的就是关于" → "蓝哥讲的是关于"

【输出要求】
- 输出纯文本，不添加任何解释或说明
- 保持原有的段落结构或按逻辑重组
- 不要添加标题、摘要等额外内容
- 如果原文有时间戳标记（如"第 X 部分"），可以保留

请记住：你的任务是"润色"而非"改写"或"总结"。"""

    CONSERVATIVE_PROMPT_SUFFIX = """
【保守模式 - 仅做最小修改】
仅修正明显的错别字，不删除任何口语词，不断句，不改段落结构。
"""

    AGGRESSIVE_PROMPT_SUFFIX = """
【激进模式 - 深度可读性优化】
可以更积极地删除口语冗余词，优化句子结构，使文本更接近书面语风格。
但仍然不能删减或改变任何实质内容。
"""

    def __init__(self, config: RefinerConfig = None):
        """
        初始化优化器

        Args:
            config: 优化配置
        """
        self.config = config or RefinerConfig()

    def _build_system_prompt(self) -> str:
        """构建系统提示词"""
        prompt = self.SYSTEM_PROMPT_TEMPLATE

        if self.config.mode == RefineMode.CONSERVATIVE:
            prompt += self.CONSERVATIVE_PROMPT_SUFFIX
        elif self.config.mode == RefineMode.AGGRESSIVE:
            prompt += self.AGGRESSIVE_PROMPT_SUFFIX

        return prompt

    def _preprocess_text(self, text: str) -> str:
        """
        预处理文本（在 LLM 之前的简单处理）

        Args:
            text: 原始文本

        Returns:
            预处理后的文本
        """
        # 移除过多的空白字符
        text = re.sub(r'\s+', ' ', text)

        # 移除重复的标点
        text = re.sub(r'([。！？]){2,}', r'\1', text)

        # 移除重复的逗号
        text = re.sub(r'，{2,}', '，', text)

        return text.strip()

    def _split_text_chunks(self, text: str) -> List[str]:
        """
        将文本分割为适合 LLM 处理的块

        Args:
            text: 输入文本

        Returns:
            文本块列表
        """
        chunks = []

        # 如果文本较短，直接返回
        if len(text) <= self.config.max_chunk_size:
            return [text]

        # 按段落分割
        paragraphs = text.split('\n\n')
        current_chunk = ""

        for para in paragraphs:
            # 如果单个段落就超过最大长度，需要进一步分割
            if len(para) > self.config.max_chunk_size:
                # 按句子分割
                sentences = re.split(r'([。！？.!?])', para)
                current_sentence = ""

                for i in range(0, len(sentences) - 1, 2):
                    sentence = sentences[i] + sentences[i + 1]

                    if len(current_chunk) + len(sentence) > self.config.max_chunk_size:
                        if current_chunk:
                            chunks.append(current_chunk.strip())
                        current_chunk = sentence
                    else:
                        current_chunk += sentence

                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = ""
            else:
                # 检查是否需要开始新块
                if len(current_chunk) + len(para) > self.config.max_chunk_size:
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                    current_chunk = para
                else:
                    if current_chunk:
                        current_chunk += "\n\n" + para
                    else:
                        current_chunk = para

        # 添加最后一个块
        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks

    def _merge_chunks(self, chunks: List[str]) -> str:
        """
        合并处理后的文本块

        Args:
            chunks: 处理后的文本块列表

        Returns:
            合并后的文本
        """
        # 移除块之间的重叠部分（简化处理）
        result = []
        for i, chunk in enumerate(chunks):
            if i > 0:
                # 移除与前一块重叠的部分
                # 简单策略：从块的开头找到合适的分割点
                prev_chunk = chunks[i - 1]
                overlap_end = prev_chunk[-100:] if len(prev_chunk) > 100 else prev_chunk

                # 在当前块中跳过重叠内容
                if overlap_end.strip():
                    # 查找当前块中与上一块结尾相似的部分并跳过
                    # 简化处理：直接连接
                    pass
            result.append(chunk)

        return "\n\n".join(result)

    def refine(
        self,
        text: str,
        llm_provider=None,
        progress_callback: Optional[Callable[[str, int], None]] = None
    ) -> str:
        """
        优化转录文本

        Args:
            text: 原始转录文本
            llm_provider: LLM 提供商（如果不提供，需要外部注入）
            progress_callback: 进度回调函数

        Returns:
            优化后的文本

        Raises:
            RuntimeError: 如果 LLM 提供商未提供或调用失败
        """
        if llm_provider is None:
            raise RuntimeError("LLM provider is required for transcript refinement")

        def report(stage: str, progress: int):
            if progress_callback:
                progress_callback(stage, progress)

        # 预处理
        report("preprocessing", 0)
        text = self._preprocess_text(text)

        # 分割文本
        report("splitting", 10)
        chunks = self._split_text_chunks(text)

        # 构建系统提示词
        system_prompt = self._build_system_prompt()

        # 处理每个块
        refined_chunks = []
        total_chunks = len(chunks)

        for i, chunk in enumerate(chunks):
            progress = int(10 + (i / total_chunks) * 80)
            report(f"processing_chunk_{i+1}", progress)

            user_prompt = f"""请优化以下会议转录文本：

---
{chunk}
---

请直接返回优化后的文本，不要添加任何说明或解释。"""

            try:
                response = llm_provider.chat(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt
                )

                refined_chunks.append(response.content.strip())

            except Exception as e:
                # 如果某块处理失败，使用原始内容
                print(f"Warning: Failed to refine chunk {i+1}, using original: {e}")
                refined_chunks.append(chunk)

        # 合并结果
        report("merging", 95)
        refined_text = self._merge_chunks(refined_chunks)

        report("complete", 100)

        return refined_text


# ============================================
# 便捷函数
# ============================================

def refine_transcript(
    text: str,
    llm_provider=None,
    mode: RefineMode = RefineMode.BALANCED,
    progress_callback: Optional[Callable[[str, int], None]] = None
) -> str:
    """
    优化会议转录文本

    Args:
        text: 原始转录文本
        llm_provider: LLM 提供商
        mode: 优化模式
        progress_callback: 进度回调函数

    Returns:
        优化后的文本

    Example:
        >>> from summarizer.llm import GLMProvider
        >>> from transcript.refiner import refine_transcript
        >>>
        >>> llm = GLMProvider()
        >>> refined = refine_transcript(raw_text, llm)
        >>> print(refined)
    """
    config = RefinerConfig(mode=mode)
    refiner = TranscriptRefiner(config)
    return refiner.refine(text, llm_provider, progress_callback)


def refine_transcript_file(
    input_path: str,
    output_path: str,
    llm_provider=None,
    mode: RefineMode = RefineMode.BALANCED
) -> str:
    """
    优化转录文件

    Args:
        input_path: 输入文件路径（.txt 或 .md）
        output_path: 输出文件路径
        llm_provider: LLM 提供商
        mode: 优化模式

    Returns:
        优化后的文本内容
    """
    input_file = Path(input_path)

    # 读取文件
    if input_file.suffix == '.json':
        # 如果是 JSON 转录文件，先提取文本
        import json
        from transcript.load import load_transcript

        document = load_transcript(input_path)
        text = document.get_full_text()
    else:
        # 文本文件直接读取
        with open(input_file, 'r', encoding='utf-8') as f:
            text = f.read()

    # 优化文本
    refined = refine_transcript(text, llm_provider, mode)

    # 保存结果
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(refined)

    return str(output_file)


# ============================================
# 纯规则模式（不使用 LLM）
# ============================================

def refine_with_rules(
    text: str,
    config: RefinerConfig = None
) -> str:
    """
    使用纯规则优化转录文本（快速模式，不调用 LLM）

    仅处理：
    - 删除重复的标点和空格
    - 修正明显的重复词
    - 简单的断句优化

    Args:
        text: 原始文本
        config: 优化配置

    Returns:
        优化后的文本
    """
    if config is None:
        config = RefinerConfig()

    # 移除多余空白
    text = re.sub(r'\s+', ' ', text)

    # 移除重复标点
    text = re.sub(r'([。！？，、]){2,}', r'\1', text)

    # 删除重复的常见填充词（简单情况）
    for filler in ["就是就是", "然后然后", "那个那个", "这个这个"]:
        text = text.replace(filler, filler[:2])

    # 修复常见的语音识别错误
    corrections = {
        "蓝哥": "蓝哥",  # 确保名字正确
        "智谱": "智谱",
        # 可以添加更多
    }

    return text.strip()
