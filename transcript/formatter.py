"""
Transcript Formatter - 智能文稿整理模块

将碎片化的 utterances 转换为可读的文稿
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Callable, Union
from pathlib import Path
from enum import Enum
import re
from datetime import datetime


class FormatMethod(Enum):
    """格式化方法"""
    RULE_BASED = "rule_based"      # 纯规则
    SEMANTIC = "semantic"           # LLM 语义分段（未实现）


@dataclass
class FormatterConfig:
    """格式化配置"""
    # 合并规则
    merge_gap_threshold: float = 3.0      # 间隔小于3秒则合并
    paragraph_max_length: int = 300       # 单段落最大字数
    paragraph_min_length: int = 50        # 单段落最小字数

    # 分段规则
    section_break_gap: float = 10.0       # 停顿超过10秒则分段
    section_max_duration: float = 300.0   # 单段最大时长（5分钟）

    # 输出格式
    include_timestamps: bool = False      # 是否包含时间戳
    include_speaker_labels: bool = False  # 是否包含说话人（如果可检测）
    output_format: str = "markdown"       # markdown, plain, html

    # 标点符号处理
    add_missing_punctuation: bool = True  # 是否添加缺失的标点符号


@dataclass
class Paragraph:
    """段落"""
    text: str
    start_time: float
    end_time: float
    utterance_indices: List[int] = field(default_factory=list)

    def duration(self) -> float:
        """段落时长"""
        return self.end_time - self.start_time

    def word_count(self) -> int:
        """字数"""
        return len(self.text)


@dataclass
class Section:
    """文稿段落（语义段落）"""
    paragraphs: List[Paragraph]
    start_time: float
    end_time: float
    section_type: str = "content"  # intro, main, conclusion, content
    title: Optional[str] = None

    def duration(self) -> float:
        """段落时长"""
        return self.end_time - self.start_time

    def word_count(self) -> int:
        """总字数"""
        return sum(p.word_count() for p in self.paragraphs)

    def paragraph_count(self) -> int:
        """段落数"""
        return len(self.paragraphs)


@dataclass
class FormattedTranscript:
    """格式化后的文稿"""
    metadata: Dict[str, Any]
    sections: List[Section]

    def total_duration(self) -> float:
        """总时长"""
        if not self.sections:
            return 0.0
        return self.sections[-1].end_time - self.sections[0].start_time

    def total_word_count(self) -> int:
        """总字数"""
        return sum(s.word_count() for s in self.sections)

    def total_paragraph_count(self) -> int:
        """总段落数"""
        return sum(s.paragraph_count() for s in self.sections)

    def to_markdown(self) -> str:
        """转换为 Markdown 格式"""
        lines = []

        # 标题
        lines.append("# 会议文稿")
        lines.append("")

        # 元数据
        meta = self.metadata
        if meta.get("source_transcript"):
            lines.append(f"**来源**: `{Path(meta['source_transcript']).name}`")
        if meta.get("duration"):
            lines.append(f"**音频时长**: {self._format_duration(meta['duration'])}")
        if meta.get("word_count"):
            lines.append(f"**字数**: 约 {meta['word_count']} 字")
        if meta.get("created_at"):
            lines.append(f"**生成时间**: {meta['created_at']}")
        lines.append("")

        lines.append("---")
        lines.append("")

        # 内容段落
        for i, section in enumerate(self.sections, 1):
            # 添加段落标题（如果有）
            if section.title:
                lines.append(f"## {section.title}")
            elif len(self.sections) > 1:
                # 多段落时添加编号
                time_range = self._format_time_range(section.start_time, section.end_time)
                lines.append(f"## 第 {i} 部分 ({time_range})")

            lines.append("")

            # 添加段落内容
            for para in section.paragraphs:
                lines.append(para.text)
                lines.append("")

            lines.append("---")
            lines.append("")

        return "\n".join(lines)

    def to_plain_text(self) -> str:
        """转换为纯文本格式"""
        lines = []

        lines.append("=" * 60)
        lines.append("会议文稿")
        lines.append("=" * 60)
        lines.append("")

        for section in self.sections:
            for para in section.paragraphs:
                lines.append(para.text)
                lines.append("")

        return "\n".join(lines)

    def to_html(self) -> str:
        """转换为 HTML 格式"""
        html = ["<!DOCTYPE html>", "<html><head>",
                "<meta charset='UTF-8'>",
                "<title>会议文稿</title>",
                "<style>",
                "body { font-family: 'Microsoft YaHei', sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; line-height: 1.8; }",
                "h1 { color: #333; border-bottom: 2px solid #4CAF50; padding-bottom: 10px; }",
                "h2 { color: #555; margin-top: 30px; }",
                ".meta { color: #666; font-size: 14px; margin-bottom: 20px; }",
                "p { text-indent: 2em; margin: 10px 0; }",
                ".section { margin-bottom: 30px; }",
                "hr { border: none; border-top: 1px solid #eee; margin: 20px 0; }",
                "</style>",
                "</head><body>"]

        # 标题
        html.append("<h1>会议文稿</h1>")

        # 元数据
        meta = self.metadata
        html.append("<div class='meta'>")
        if meta.get("duration"):
            html.append(f"音频时长: {self._format_duration(meta['duration'])}<br>")
        if meta.get("word_count"):
            html.append(f"字数: 约 {meta['word_count']} 字<br>")
        if meta.get("created_at"):
            html.append(f"生成时间: {meta['created_at']}")
        html.append("</div>")

        # 内容
        html.append("<hr>")
        for section in self.sections:
            html.append("<div class='section'>")
            if section.title:
                html.append(f"<h2>{section.title}</h2>")
            for para in section.paragraphs:
                html.append(f"<p>{para.text}</p>")
            html.append("</div>")

        html.append("</body></html>")
        return "\n".join(html)

    def save(self, path: Path, format: str = "markdown") -> Path:
        """保存到文件"""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        if format == "markdown" or format == "md":
            content = self.to_markdown()
        elif format == "plain" or format == "txt":
            content = self.to_plain_text()
        elif format == "html":
            content = self.to_html()
        else:
            raise ValueError(f"Unsupported format: {format}")

        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

        return path

    def _format_duration(self, seconds: float) -> str:
        """格式化时长"""
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}分{secs}秒"

    def _format_time_range(self, start: float, end: float) -> str:
        """格式化时间范围"""
        start_min = int(start // 60)
        start_sec = int(start % 60)
        end_min = int(end // 60)
        end_sec = int(end % 60)
        return f"{start_min:02d}:{start_sec:02d} - {end_min:02d}:{end_sec:02d}"

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "metadata": self.metadata,
            "sections": [
                {
                    "title": s.title,
                    "type": s.section_type,
                    "start_time": s.start_time,
                    "end_time": s.end_time,
                    "paragraphs": [
                        {
                            "text": p.text,
                            "start_time": p.start_time,
                            "end_time": p.end_time
                        }
                        for p in s.paragraphs
                    ]
                }
                for s in self.sections
            ]
        }


class TranscriptFormatter:
    """文稿格式化器"""

    # 句子结束标点符号
    SENTENCE_ENDINGS = ('。', '！', '？', '!', '?', '…', '~')

    def __init__(self, config: FormatterConfig = None):
        self.config = config or FormatterConfig()

    def format(
        self,
        utterances: List[Dict[str, Any]],
        method: FormatMethod = FormatMethod.RULE_BASED,
        progress_callback: Optional[Callable[[str, int], None]] = None
    ) -> FormattedTranscript:
        """
        格式化文稿

        Args:
            utterances: utterance 列表，每个包含 {start, end, text}
            method: 格式化方法
            progress_callback: 进度回调 (stage, progress)

        Returns:
            FormattedTranscript 实例
        """
        def report(stage: str, progress: int):
            if progress_callback:
                progress_callback(stage, progress)

        if not utterances:
            return FormattedTranscript(
                metadata={"error": "No utterances provided"},
                sections=[]
            )

        if method == FormatMethod.RULE_BASED:
            return self._format_rule_based(utterances, progress_callback)
        elif method == FormatMethod.SEMANTIC:
            return self._format_semantic(utterances, progress_callback)
        else:
            raise ValueError(f"Unsupported method: {method}")

    def _format_rule_based(
        self,
        utterances: List[Dict[str, Any]],
        progress_callback: Optional[Callable[[str, int], None]] = None
    ) -> FormattedTranscript:
        """纯规则格式化"""
        def report(stage: str, progress: int):
            if progress_callback:
                progress_callback(stage, progress)

        # 步骤 1: 合并 utterances 为句子 (0-30%)
        report("merge_utterances", 0)
        sentences = self._merge_utterances(utterances)
        report("merge_utterances", 30)

        # 步骤 2: 将句子组合为段落 (30-60%)
        report("build_paragraphs", 30)
        paragraphs = self._build_paragraphs(sentences)
        report("build_paragraphs", 60)

        # 步骤 3: 将段落组合为 section (60-90%)
        report("build_sections", 60)
        sections = self._build_sections(paragraphs)
        report("build_sections", 90)

        # 步骤 4: 添加标点符号 (90-100%)
        if self.config.add_missing_punctuation:
            report("add_punctuation", 90)
            self._add_missing_punctuation(sections)
            report("add_punctuation", 100)

        # 计算总时长
        total_duration = utterances[-1]["end"] - utterances[0]["start"] if utterances else 0

        return FormattedTranscript(
            metadata={
                "format_method": "rule_based",
                "paragraph_count": len(paragraphs),
                "section_count": len(sections),
                "word_count": sum(p.word_count() for p in paragraphs),
                "duration": total_duration,
                "utterance_count": len(utterances),
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            },
            sections=sections
        )

    def _merge_utterances(
        self,
        utterances: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """合并连续的 utterances 为句子"""
        sentences = []
        current_text = ""
        current_start = None
        current_end = None
        current_indices = []

        for i, utt in enumerate(utterances):
            text = utt.get("text", "").strip()
            if not text:
                continue

            start = utt.get("start", 0)
            end = utt.get("end", start)

            # 检查是否应该开始新句子
            if current_start is None:
                # 第一个 utterance
                current_text = text
                current_start = start
                current_end = end
                current_indices = [i]
            else:
                gap = start - current_end
                text_ends_with_punct = any(current_text.endswith(p) for p in self.SENTENCE_ENDINGS)

                # 分割条件：
                # 1. 停顿超过阈值
                # 2. 前一句以标点结尾
                should_split = (
                    gap > self.config.merge_gap_threshold or
                    text_ends_with_punct
                )

                if should_split:
                    # 保存当前句子
                    if current_text:
                        sentences.append({
                            "text": current_text,
                            "start": current_start,
                            "end": current_end,
                            "utterance_indices": current_indices.copy()
                        })
                    # 开始新句子
                    current_text = text
                    current_start = start
                    current_end = end
                    current_indices = [i]
                else:
                    # 合并到当前句子
                    current_text += text
                    current_end = end
                    current_indices.append(i)

        # 保存最后一个句子
        if current_text:
            sentences.append({
                "text": current_text,
                "start": current_start,
                "end": current_end,
                "utterance_indices": current_indices.copy()
            })

        return sentences

    def _build_paragraphs(
        self,
        sentences: List[Dict[str, Any]]
    ) -> List[Paragraph]:
        """将句子组合为段落"""
        paragraphs = []
        current_text = ""
        current_start = None
        current_end = None
        current_indices = []

        for sent in sentences:
            text = sent["text"]
            length = len(current_text) + len(text)

            # 分段条件：
            # 1. 累积长度超过最大值
            # 2. 停顿超过分段阈值
            should_split = False
            if current_text:
                gap = sent["start"] - current_end
                length_exceeded = length > self.config.paragraph_max_length
                long_pause = gap > self.config.section_break_gap

                should_split = length_exceeded or long_pause

            if should_split and current_text:
                # 保存当前段落
                paragraphs.append(Paragraph(
                    text=current_text,
                    start_time=current_start,
                    end_time=current_end,
                    utterance_indices=current_indices.copy()
                ))
                # 开始新段落
                current_text = text
                current_start = sent["start"]
                current_end = sent["end"]
                current_indices = sent["utterance_indices"].copy()
            else:
                # 合并到当前段落
                if current_text:
                    current_text += " " + text
                else:
                    current_text = text
                    current_start = sent["start"]
                current_end = sent["end"]
                current_indices.extend(sent["utterance_indices"])

        # 保存最后一个段落
        if current_text:
            paragraphs.append(Paragraph(
                text=current_text,
                start_time=current_start,
                end_time=current_end,
                utterance_indices=current_indices
            ))

        return paragraphs

    def _build_sections(
        self,
        paragraphs: List[Paragraph]
    ) -> List[Section]:
        """将段落组合为 section"""
        if not paragraphs:
            return []

        sections = []
        current_paragraphs = [paragraphs[0]]

        for para in paragraphs[1:]:
            # 检查是否需要新 section
            last_para = current_paragraphs[-1]
            gap = para.start_time - last_para.end_time
            duration = para.end_time - current_paragraphs[0].start_time

            should_split = (
                gap > self.config.section_break_gap or
                duration > self.config.section_max_duration
            )

            if should_split:
                # 保存当前 section
                sections.append(self._create_section(current_paragraphs))
                # 开始新 section
                current_paragraphs = [para]
            else:
                current_paragraphs.append(para)

        # 保存最后一个 section
        if current_paragraphs:
            sections.append(self._create_section(current_paragraphs))

        return sections

    def _create_section(self, paragraphs: List[Paragraph]) -> Section:
        """创建 section"""
        return Section(
            paragraphs=paragraphs,
            start_time=paragraphs[0].start_time if paragraphs else 0,
            end_time=paragraphs[-1].end_time if paragraphs else 0,
            section_type="content"
        )

    def _add_missing_punctuation(self, sections: List[Section]):
        """添加缺失的标点符号（简单版本）"""
        # 这只是基础实现，实际可以使用更智能的 NLP 模型
        for section in sections:
            for para in section.paragraphs:
                text = para.text.strip()

                # 确保段落以标点结尾
                if text and not any(text.endswith(p) for p in self.SENTENCE_ENDINGS):
                    # 检查是否是疑问句
                    if any(w in text for w in ["吗", "呢", "？", "?"]):
                        text += "？"
                    elif any(w in text for w in ["啊", "呀", "哦", "！"]):
                        text += "！"
                    else:
                        text += "。"

                para.text = text

    def _format_semantic(
        self,
        utterances: List[Dict[str, Any]],
        progress_callback: Optional[Callable[[str, int], None]] = None
    ) -> FormattedTranscript:
        """LLM 语义分段（后续实现）"""
        raise NotImplementedError("Semantic formatting not yet implemented. Use FormatMethod.RULE_BASED.")


# ============================================
# 便捷函数
# ============================================

def format_transcript(
    transcript_path: str,
    output_path: str = None,
    config: FormatterConfig = None,
    method: FormatMethod = FormatMethod.RULE_BASED,
    output_format: str = "markdown",
    progress_callback: Optional[Callable[[str, int], None]] = None
) -> FormattedTranscript:
    """
    格式化转录文件

    Args:
        transcript_path: 转录文件路径（JSON）
        output_path: 输出文件路径（可选）
        config: 格式化配置
        method: 格式化方法
        output_format: 输出格式 (markdown, plain, html)
        progress_callback: 进度回调

    Returns:
        FormattedTranscript 实例
    """
    from transcript.load import load_transcript

    # 加载转录文件
    document = load_transcript(transcript_path)

    # 格式化
    formatter = TranscriptFormatter(config)
    formatted = formatter.format(
        document.utterances,
        method=method,
        progress_callback=progress_callback
    )

    # 更新元数据
    formatted.metadata["source_transcript"] = transcript_path

    # 保存
    if output_path:
        formatted.save(Path(output_path), format=output_format)

    return formatted


def format_utterances(
    utterances: List[Dict[str, Any]],
    config: FormatterConfig = None,
    method: FormatMethod = FormatMethod.RULE_BASED
) -> FormattedTranscript:
    """
    直接格式化 utterances 列表

    Args:
        utterances: utterance 列表
        config: 格式化配置
        method: 格式化方法

    Returns:
        FormattedTranscript 实例
    """
    formatter = TranscriptFormatter(config)
    return formatter.format(utterances, method=method)
