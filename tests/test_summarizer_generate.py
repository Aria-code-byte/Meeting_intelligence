"""
Tests for summarizer generate module.
"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from summarizer.generate import generate_summary, _parse_summary_response, _title_to_id
from summarizer.llm import MockLLMProvider, LLMMessage, LLMResponse
from transcript.types import TranscriptDocument
from template.types import UserTemplate, SummaryAngle


class TestParseSummaryResponse:
    """_parse_summary_response 函数测试"""

    def test_parse_markdown_sections(self):
        """测试解析 markdown 格式的响应"""
        response = """
## 会议总结
这是会议的总结。

## 关键要点
- 要点1
- 要点2

## 行动项
- 行动1
- 行动2
"""

        template = UserTemplate(
            name="test",
            role="Test",
            angle=SummaryAngle.BALANCED,
            focus=["test"]
        )

        sections = _parse_summary_response(response, template)

        assert len(sections) == 3
        assert sections[0].id == "会议总结"
        assert sections[0].title == "会议总结"
        assert sections[1].id == "关键要点"
        assert sections[2].id == "行动项"

    def test_parse_plain_text(self):
        """测试解析纯文本响应"""
        response = "这是一段简单的总结文字，没有markdown标题。"

        template = UserTemplate(
            name="test",
            role="Test",
            angle=SummaryAngle.BALANCED,
            focus=["test"]
        )

        sections = _parse_summary_response(response, template)

        # 应该创建一个默认 section
        assert len(sections) == 1
        assert sections[0].id == "summary"

    def test_parse_with_template_sections(self):
        """测试使用模板 sections"""
        response = "简单的内容"

        from template.types import TemplateSection, OutputFormat
        template = UserTemplate(
            name="test",
            role="Test",
            angle=SummaryAngle.BALANCED,
            focus=["test"],
            sections=[
                TemplateSection(
                    id="custom-section",
                    title="Custom Section",
                    prompt="Custom prompt",
                    order=1
                )
            ]
        )

        sections = _parse_summary_response(response, template)

        assert len(sections) == 1
        assert sections[0].id == "custom-section"
        assert sections[0].title == "Custom Section"


class TestTitleToId:
    """_title_to_id 函数测试"""

    def test_simple_title(self):
        """测试简单标题"""
        assert _title_to_id("会议总结") == "会议总结"

    def test_title_with_special_chars(self):
        """测试带特殊字符的标题"""
        assert _title_to_id("关键要点：") == "关键要点"
        assert _title_to_id("Action Items!") == "action-items"

    def test_chinese_title(self):
        """测试中文标题"""
        assert _title_to_id("决策事项") == "决策事项"


class TestGenerateSummary:
    """generate_summary 函数测试"""

    def test_generate_with_mock_llm(self, tmp_path):
        """测试使用 Mock LLM 生成总结"""
        # 创建测试音频文件
        audio_file = tmp_path / "audio.wav"
        audio_file.write_bytes(b"RIFF" + b"\x00" * 1000)

        # 创建测试转录文档
        transcript_file = tmp_path / "transcript.json"
        transcript_file.write_bytes(b"{}")

        transcript = TranscriptDocument(
            utterances=[{"start": 0.0, "end": 10.0, "text": "测试内容"}],
            audio_path=str(audio_file),
            duration=10.0,
            asr_provider="whisper"
        )

        # 保存转录文档（这样 document_path 才有值）
        transcript.save(str(transcript_file))

        # 创建 mock provider
        provider = MockLLMProvider(
            mock_response="## 测试总结\n这是测试生成的总结。"
        )

        # 生成总结（不保存）
        summary = generate_summary(
            transcript=str(transcript_file),
            template="general",
            llm_provider=provider,
            save=False
        )

        assert summary.template_name == "general"
        assert len(summary.sections) > 0
        assert summary.llm_provider == "mock-provider"

    def test_generate_with_transcript_path(self, tmp_path):
        """测试使用转录文件路径生成"""
        # 创建测试音频文件
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"RIFF" + b"\x00" * 1000)

        # 创建测试转录文件（使用正确的音频路径）
        import json
        transcript_file = tmp_path / "transcript.json"
        transcript_file.write_bytes(
            json.dumps({
                "metadata": {
                    "audio_path": str(audio_file),
                    "duration": 10.0,
                    "asr_provider": "whisper",
                    "created_at": "2024-01-01",
                    "utterance_count": 0
                },
                "utterances": []
            }).encode()
        )

        provider = MockLLMProvider()

        summary = generate_summary(
            transcript=str(transcript_file),
            template="general",
            llm_provider=provider,
            save=False
        )

        assert summary.template_name == "general"

    def test_generate_save_to_file(self, tmp_path):
        """测试生成并保存"""
        # 创建测试音频文件
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"RIFF" + b"\x00" * 1000)

        # 创建测试转录文件（使用正确的音频路径）
        import json
        transcript_file = tmp_path / "transcript.json"
        transcript_file.write_bytes(
            json.dumps({
                "metadata": {
                    "audio_path": str(audio_file),
                    "duration": 10.0,
                    "asr_provider": "whisper",
                    "created_at": "2024-01-01",
                    "utterance_count": 0
                },
                "utterances": []
            }).encode()
        )

        provider = MockLLMProvider()

        summary = generate_summary(
            transcript=str(transcript_file),
            template="general",
            llm_provider=provider,
            save=True,
            output_path=str(tmp_path / "output_summary.json")
        )

        assert Path(tmp_path / "output_summary.json").exists()
