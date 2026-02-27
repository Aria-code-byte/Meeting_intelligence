"""
Tests for transcript export module.
"""

import pytest
import json
from pathlib import Path

from transcript.export import export_json, export_text, export_markdown, export_auto
from transcript.types import TranscriptDocument


class TestExportJson:
    """export_json 函数测试"""

    def test_export_json(self, tmp_path):
        """测试导出为 JSON"""
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"data")

        document = TranscriptDocument(
            utterances=[
                {"start": 0.0, "end": 2.5, "text": "大家好"}
            ],
            audio_path=str(audio_file),
            duration=10.0,
            asr_provider="whisper"
        )

        output_path = tmp_path / "output.json"
        result = export_json(document, output_path)

        assert Path(result).exists()

        # 验证内容
        with open(result, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert "metadata" in data
        assert "utterances" in data
        assert data["utterances"][0]["text"] == "大家好"


class TestExportText:
    """export_text 函数测试"""

    def test_export_text(self, tmp_path):
        """测试导出为纯文本"""
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"data")

        document = TranscriptDocument(
            utterances=[
                {"start": 0.0, "end": 2.5, "text": "大家好"},
                {"start": 2.6, "end": 5.0, "text": "今天讨论项目"}
            ],
            audio_path=str(audio_file),
            duration=10.0,
            asr_provider="whisper-local-base",
            created_at="2024-01-01T00:00:00"
        )

        output_path = tmp_path / "output.txt"
        result = export_text(document, output_path)

        assert Path(result).exists()

        # 验证内容
        content = Path(result).read_text(encoding="utf-8")

        assert "原始会议文档" in content
        assert str(audio_file) in content
        assert "[00:00] 大家好" in content
        assert "[00:02] 今天讨论项目" in content

    def test_export_text_empty(self, tmp_path):
        """测试导出空文档为纯文本"""
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"data")

        document = TranscriptDocument(
            utterances=[],
            audio_path=str(audio_file),
            duration=10.0,
            asr_provider="whisper"
        )

        output_path = tmp_path / "output.txt"
        result = export_text(document, output_path)

        assert Path(result).exists()
        content = Path(result).read_text(encoding="utf-8")

        assert "语音片段数: 0" in content


class TestExportMarkdown:
    """export_markdown 函数测试"""

    def test_export_markdown(self, tmp_path):
        """测试导出为 Markdown"""
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"data")

        document = TranscriptDocument(
            utterances=[
                {"start": 0.0, "end": 2.5, "text": "大家好"}
            ],
            audio_path=str(audio_file),
            duration=10.0,
            asr_provider="whisper-local-base",
            created_at="2024-01-01T00:00:00"
        )

        output_path = tmp_path / "output.md"
        result = export_markdown(document, output_path)

        assert Path(result).exists()

        # 验证内容
        content = Path(result).read_text(encoding="utf-8")

        assert "# 原始会议文档" in content
        assert "## 元数据" in content
        assert "## 内容" in content
        assert "---" in content  # YAML frontmatter
        assert "[00:00] - [00:02]" in content
        assert "大家好" in content

    def test_export_markdown_structure(self, tmp_path):
        """测试 Markdown 导出结构"""
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"data")

        document = TranscriptDocument(
            utterances=[
                {"start": 0.0, "end": 2.5, "text": "first"},
                {"start": 3.0, "end": 5.0, "text": "second"}
            ],
            audio_path=str(audio_file),
            duration=10.0,
            asr_provider="whisper",
            created_at="2024-01-01T00:00:00"
        )

        output_path = tmp_path / "output.md"
        export_markdown(document, output_path)

        content = Path(output_path).read_text(encoding="utf-8")

        # 验证 YAML frontmatter
        assert content.startswith("---")
        assert "audio_path:" in content
        assert "duration: 10.0" in content

        # 验证元数据表格
        assert "| 字段 | 值 |" in content

        # 验证内容列表
        assert "- **" in content  # 加粗时间戳


class TestExportAuto:
    """export_auto 函数测试"""

    def test_export_auto_json(self, tmp_path):
        """测试自动导出为 JSON"""
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"data")

        document = TranscriptDocument(
            utterances=[{"start": 0.0, "end": 2.5, "text": "test"}],
            audio_path=str(audio_file),
            duration=10.0,
            asr_provider="whisper"
        )

        output_path = tmp_path / "output.json"
        result = export_auto(document, output_path)

        assert Path(result).exists()
        # 验证是 JSON 格式
        with open(result, "r") as f:
            json.load(f)

    def test_export_auto_txt(self, tmp_path):
        """测试自动导出为 TXT"""
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"data")

        document = TranscriptDocument(
            utterances=[{"start": 0.0, "end": 2.5, "text": "test"}],
            audio_path=str(audio_file),
            duration=10.0,
            asr_provider="whisper"
        )

        output_path = tmp_path / "output.txt"
        result = export_auto(document, output_path)

        assert Path(result).exists()
        content = Path(result).read_text()
        assert "原始会议文档" in content

    def test_export_auto_md(self, tmp_path):
        """测试自动导出为 MD"""
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"data")

        document = TranscriptDocument(
            utterances=[{"start": 0.0, "end": 2.5, "text": "test"}],
            audio_path=str(audio_file),
            duration=10.0,
            asr_provider="whisper"
        )

        output_path = tmp_path / "output.md"
        result = export_auto(document, output_path)

        assert Path(result).exists()
        content = Path(result).read_text()
        assert "# 原始会议文档" in content

    def test_export_auto_unsupported_format(self, tmp_path):
        """测试不支持的导出格式"""
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"data")

        document = TranscriptDocument(
            utterances=[{"start": 0.0, "end": 2.5, "text": "test"}],
            audio_path=str(audio_file),
            duration=10.0,
            asr_provider="whisper"
        )

        output_path = tmp_path / "output.pdf"

        with pytest.raises(ValueError, match="不支持的导出格式"):
            export_auto(document, output_path)
