"""
Tests for template.recorder module
"""

import pytest
from template.recorder import (
    TimeBlock,
    build_recorder_system_prompt,
    build_recorder_user_prompt,
    get_recorder_prompts,
    format_time_blocks,
    ms_to_mmss
)


class TestTimeBlock:
    """测试 TimeBlock 数据类"""

    def test_time_block_creation(self):
        """测试创建时间块"""
        block = TimeBlock(start_ms=0, end_ms=60000, text="测试文本")
        assert block.start_ms == 0
        assert block.end_ms == 60000
        assert block.text == "测试文本"

    def test_duration_seconds(self):
        """测试时长计算"""
        block = TimeBlock(start_ms=0, end_ms=90000, text="测试")
        assert block.duration_seconds == 90.0

    def test_format_time_range(self):
        """测试时间范围格式化"""
        block = TimeBlock(start_ms=0, end_ms=125000, text="测试")
        result = block.format_time_range()
        assert result == "[00:00 - 02:05]"

    def test_format_time_range_single_minute(self):
        """测试单分钟时间范围格式化"""
        block = TimeBlock(start_ms=30000, end_ms=90000, text="测试")
        result = block.format_time_range()
        assert result == "[00:30 - 01:30]"

    def test_format_time_range_hour(self):
        """测试小时级时间范围格式化"""
        block = TimeBlock(start_ms=0, end_ms=3665000, text="测试")
        result = block.format_time_range()
        assert result == "[00:00 - 61:05]"  # 简单格式，超过60分钟继续累加


class TestRecorderPrompts:
    """测试录音整理员提示词"""

    def test_build_recorder_system_prompt(self):
        """测试系统提示词生成"""
        prompt = build_recorder_system_prompt()
        assert "专业录音整理员" in prompt
        assert "只纠错，不改为书面语" in prompt
        assert "蓝哥舞" in prompt  # 检查错别字对照表
        assert "车带" in prompt
        assert "骗案" in prompt

    def test_build_recorder_user_prompt(self):
        """测试用户提示词生成"""
        prompt = build_recorder_user_prompt("这是一段测试文本")
        assert "这是一段测试文本" in prompt
        assert "同音错别字对照表" in prompt
        assert "保持口语化风格" in prompt

    def test_get_recorder_prompts(self):
        """测试获取完整提示词"""
        prompts = get_recorder_prompts("测试文本")
        assert "system_prompt" in prompts
        assert "user_prompt" in prompts
        assert prompts["system_prompt"]
        assert prompts["user_prompt"]
        assert "测试文本" in prompts["user_prompt"]


class TestFormatTimeBlocks:
    """测试时间块格式化"""

    def test_format_single_block(self):
        """测试格式化单个时间块"""
        blocks = [TimeBlock(start_ms=0, end_ms=60000, text="这是第一段文本")]
        refined_texts = ["这是整理后的文本"]

        result = format_time_blocks(blocks, refined_texts)
        assert "[00:00 - 01:00]" in result
        assert "这是整理后的文本" in result

    def test_format_multiple_blocks(self):
        """测试格式化多个时间块"""
        blocks = [
            TimeBlock(start_ms=0, end_ms=60000, text="第一段"),
            TimeBlock(start_ms=60000, end_ms=120000, text="第二段")
        ]
        refined_texts = ["整理后的第一段", "整理后的第二段"]

        result = format_time_blocks(blocks, refined_texts)
        assert "[00:00 - 01:00]" in result
        assert "[01:00 - 02:00]" in result
        assert "整理后的第一段" in result
        assert "整理后的第二段" in result
        assert result.count("\n\n") == 1  # 块之间有一个空行

    def test_format_mismatched_counts(self):
        """测试块数量与文本数量不匹配"""
        blocks = [TimeBlock(start_ms=0, end_ms=60000, text="第一段")]
        refined_texts = ["文本1", "文本2"]  # 多一个文本

        with pytest.raises(ValueError, match="块数量.*与文本数量.*不匹配"):
            format_time_blocks(blocks, refined_texts)


class TestMsToMmss:
    """测试毫秒转 MM:SS 格式"""

    def test_zero_seconds(self):
        """测试 0 秒"""
        assert ms_to_mmss(0) == "00:00"

    def test_seconds_only(self):
        """测试只有秒数"""
        assert ms_to_mmss(45000) == "00:45"
        assert ms_to_mmss(59000) == "00:59"

    def test_single_minute(self):
        """测试单分钟"""
        assert ms_to_mmss(60000) == "01:00"
        assert ms_to_mmss(125000) == "02:05"

    def test_multiple_minutes(self):
        """测试多分钟"""
        assert ms_to_mmss(180000) == "03:00"
        assert ms_to_mmss(3665000) == "61:05"
