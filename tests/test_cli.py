#!/usr/bin/env python3
"""
CLI 工具测试脚本

测试 MeetingAssistantCLI 的核心功能。
"""

import sys
import os
from pathlib import Path
from io import StringIO
from unittest.mock import patch

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from meeting_intelligence.cli import (
    Template,
    TemplateStorage,
    PromptBuilder,
    LLMService,
    MeetingAssistantCLI,
)


def test_template_dataclass():
    """测试 Template 数据类"""
    print("测试 Template 数据类...", end=" ")

    template = Template(
        name="测试模板",
        description="这是一个测试模板"
    )

    assert template.name == "测试模板"
    assert template.description == "这是一个测试模板"

    # 测试 to_dict
    data = template.to_dict()
    assert data["name"] == "测试模板"
    assert data["description"] == "这是一个测试模板"

    # 测试 from_dict
    template2 = Template.from_dict(data)
    assert template2.name == template.name
    assert template2.description == template.description

    print("✓ 通过")


def test_template_storage():
    """测试 TemplateStorage"""
    print("测试 TemplateStorage...", end=" ")

    # 使用临时文件
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        temp_path = Path(f.name)

    try:
        storage = TemplateStorage(storage_path=temp_path)

        # 检查默认模板
        templates = storage.list_templates()
        assert len(templates) >= 2
        assert any(t.name == "通用总结" for t in templates)
        assert any(t.name == "大学生视角" for t in templates)

        # 测试添加模板
        new_template = Template(
            name="临时测试模板",
            description="测试用"
        )
        result = storage.add_template(new_template)
        assert result is True

        # 测试重复添加
        result = storage.add_template(new_template)
        assert result is False

        # 测试获取模板
        retrieved = storage.get_template("临时测试模板")
        assert retrieved is not None
        assert retrieved.name == "临时测试模板"

        # 测试删除模板
        result = storage.delete_template("临时测试模板")
        assert result is True

        # 测试重复删除
        result = storage.delete_template("临时测试模板")
        assert result is False

        # 测试 template_exists
        assert storage.template_exists("通用总结") is True
        assert storage.template_exists("不存在的模板") is False

        print("✓ 通过")

    finally:
        # 清理临时文件
        if temp_path.exists():
            temp_path.unlink()


def test_prompt_builder():
    """测试 PromptBuilder"""
    print("测试 PromptBuilder...", end=" ")

    template = Template(
        name="产品经理视角",
        description="关注产品需求和决策"
    )

    transcript = "会议内容测试文本"

    prompt = PromptBuilder.build_prompt(transcript, template)

    assert "产品经理视角" in prompt
    assert "关注产品需求和决策" in prompt
    assert "会议内容测试文本" in prompt
    assert "你是一名专业会议分析助手" in prompt

    print("✓ 通过")


def test_llm_service():
    """测试 LLMService"""
    print("测试 LLMService...", end=" ")

    service = LLMService(provider="mock")

    prompt = "测试 prompt"
    summary = service.generate_summary(prompt)

    assert isinstance(summary, str)
    assert len(summary) > 0
    assert "会议总结" in summary

    print("✓ 通过")


def test_meeting_assistant_cli():
    """测试 MeetingAssistantCLI"""
    print("测试 MeetingAssistantCLI...", end=" ")

    cli = MeetingAssistantCLI()

    # 检查初始化
    assert cli.storage is not None
    assert cli.current_transcript is None
    assert cli.llm_service is not None
    assert cli.running is True

    # 检查默认模板已加载
    templates = cli.storage.list_templates()
    assert len(templates) >= 2

    print("✓ 通过")


def test_sample_transcript():
    """测试示例转录文本"""
    print("测试示例转录文本...", end=" ")

    cli = MeetingAssistantCLI()

    # 模拟生成文字稿
    cli.current_transcript = cli.SAMPLE_TRANSCRIPT

    assert cli.current_transcript is not None
    assert "主持人" in cli.current_transcript
    assert "张三" in cli.current_transcript
    assert "李四" in cli.current_transcript
    assert "王五" in cli.current_transcript
    assert "赵六" in cli.current_transcript

    print("✓ 通过")


def test_json_error_handling():
    """测试 JSON 错误处理"""
    print("测试 JSON 错误处理...", end=" ")

    import tempfile
    import json

    # 创建包含无效 JSON 的文件
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        temp_path = Path(f.name)
        f.write("{invalid json content")

    try:
        # 应该回退到默认模板
        storage = TemplateStorage(storage_path=temp_path)

        # 验证默认模板存在
        assert storage.template_exists("通用总结")
        assert storage.template_exists("大学生视角")

        print("✓ 通过")

    finally:
        if temp_path.exists():
            temp_path.unlink()


def test_empty_json_handling():
    """测试空文件处理"""
    print("测试空文件处理...", end=" ")

    import tempfile

    # 创建空文件
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        temp_path = Path(f.name)

    try:
        # 应该初始化默认模板
        storage = TemplateStorage(storage_path=temp_path)

        # 验证默认模板存在
        assert storage.template_exists("通用总结")
        assert storage.template_exists("大学生视角")

        print("✓ 通过")

    finally:
        if temp_path.exists():
            temp_path.unlink()


def test_update_template():
    """测试更新模板"""
    print("测试更新模板...", end=" ")

    import tempfile

    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        temp_path = Path(f.name)

    try:
        storage = TemplateStorage(storage_path=temp_path)

        # 添加测试模板
        template = Template(name="测试模板", description="原始描述")
        storage.add_template(template)

        # 测试仅更新描述
        result = storage.update_template("测试模板", new_description="新描述")
        assert result is True
        updated = storage.get_template("测试模板")
        assert updated.description == "新描述"

        # 测试更新名称
        result = storage.update_template("测试模板", new_name="重命名后")
        assert result is True
        assert not storage.template_exists("测试模板")
        assert storage.template_exists("重命名后")

        # 测试同时更新
        result = storage.update_template("重命名后", new_name="最终名称", new_description="最终描述")
        assert result is True
        final = storage.get_template("最终名称")
        assert final.description == "最终描述"

        # 测试名称冲突
        storage.add_template(Template(name="另一个模板", description="xxx"))
        result = storage.update_template("最终名称", new_name="另一个模板")
        assert result is False

        # 测试更新不存在的模板
        result = storage.update_template("不存在", new_description="xxx")
        assert result is False

        print("✓ 通过")

    finally:
        if temp_path.exists():
            temp_path.unlink()


def test_input_with_retry():
    """测试输入重试方法"""
    print("测试输入重试方法...", end=" ")

    cli = MeetingAssistantCLI()

    # 检查方法存在
    assert hasattr(cli, '_get_clean_input')

    # 检查方法签名
    import inspect
    sig = inspect.signature(cli._get_clean_input)
    assert 'prompt' in sig.parameters
    assert 'allow_empty' in sig.parameters

    print("✓ 通过")


def run_all_tests():
    """运行所有测试"""
    print("=" * 50)
    print("  CLI 工具测试套件")
    print("=" * 50)
    print()

    tests = [
        test_template_dataclass,
        test_template_storage,
        test_prompt_builder,
        test_llm_service,
        test_meeting_assistant_cli,
        test_sample_transcript,
        test_json_error_handling,
        test_empty_json_handling,
        test_update_template,
        test_input_with_retry,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"✗ 失败: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ 错误: {e}")
            failed += 1

    print()
    print("=" * 50)
    print(f"测试结果: {passed} 通过, {failed} 失败")
    print("=" * 50)

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
