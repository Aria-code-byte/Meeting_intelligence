#!/usr/bin/env python3
"""
发言人识别模块测试脚本

测试发言人分离和对齐功能。
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "meeting_intelligence"))


def test_mock_diarization():
    """测试模拟发言人分离"""
    print("=" * 60)
    print("  测试模拟发言人分离")
    print("=" * 60)
    print()

    from meeting_intelligence.speaker.diarization import MockSpeakerDiarization

    # 创建模拟引擎
    engine = MockSpeakerDiarization(num_speakers=3)

    # 模拟一个音频文件（使用项目中的示例）
    # 这里我们只测试 API，不实际处理音频
    print("✓ MockSpeakerDiarization 初始化成功")

    # 测试结果结构
    from meeting_intelligence.speaker.types import DiarizationResult

    result = DiarizationResult(
        audio_path="/fake/path.wav",
        duration=300.0,
        model="mock"
    )

    # 添加一些测试片段
    from meeting_intelligence.speaker.types import SpeakerSegment

    result.add_segment(SpeakerSegment(0.0, 30.0, "SPEAKER_00", 0.9))
    result.add_segment(SpeakerSegment(30.0, 60.0, "SPEAKER_01", 0.85))
    result.add_segment(SpeakerSegment(60.0, 90.0, "SPEAKER_00", 0.92))

    print(f"✓ 创建了 {len(result.segments)} 个测试片段")
    print(f"✓ 识别到 {len(result.speakers)} 位发言人")

    # 测试统计
    dominant = result.get_dominant_speaker()
    print(f"✓ 主要发言人: {dominant}")

    print()
    print("测试通过！")
    return True


def test_speaker_manager():
    """测试发言人管理器"""
    print()
    print("=" * 60)
    print("  测试发言人管理器")
    print("=" * 60)
    print()

    from meeting_intelligence.speaker.ui import SpeakerManager
    from meeting_intelligence.speaker.types import DiarizationResult, SpeakerSegment

    # 创建管理器
    manager = SpeakerManager()

    # 设置自定义名称
    manager.set_display_name("SPEAKER_00", "张三")
    manager.set_display_name("SPEAKER_01", "李四")

    print("✓ 设置发言人名称")

    # 测试名称获取
    assert manager.get_display_name("SPEAKER_00") == "张三"
    assert manager.get_display_name("SPEAKER_01") == "李四"
    assert "发言人" in manager.get_display_name("SPEAKER_02")  # 默认名称

    print("✓ 发言人名称获取正确")

    # 测试颜色
    manager.set_color("SPEAKER_00", "#FF5733")
    assert manager.get_color("SPEAKER_00") == "#FF5733"

    print("✓ 发言人颜色设置正确")

    # 测试合并
    manager.merge_speakers("SPEAKER_02", "SPEAKER_00")
    assert manager.get_resolved_speaker("SPEAKER_02") == "SPEAKER_00"

    print("✓ 发言人合并功能正常")

    # 测试统计显示
    result = DiarizationResult(duration=300.0)

    result.add_segment(SpeakerSegment(0.0, 100.0, "SPEAKER_00", 0.9))
    result.add_segment(SpeakerSegment(100.0, 200.0, "SPEAKER_01", 0.85))
    result.add_segment(SpeakerSegment(200.0, 300.0, "SPEAKER_00", 0.92))

    speaker_list = manager.list_speakers(result)

    assert len(speaker_list) == 2
    assert speaker_list[0]["display_name"] == "张三"
    assert speaker_list[1]["display_name"] == "李四"

    print("✓ 发言人统计功能正常")

    # 打印格式化输出
    formatted = manager.format_speaker_list(result)
    print("\n示例输出：")
    print(formatted)

    print()
    print("测试通过！")
    return True


def test_alignment():
    """测试转录对齐"""
    print()
    print("=" * 60)
    print("  测试转录对齐")
    print("=" * 60)
    print()

    from meeting_intelligence.speaker.types import DiarizationResult, SpeakerSegment
    from asr.types import Utterance
    from meeting_intelligence.speaker.diarization import MockSpeakerDiarization

    # 创建模拟分离结果
    result = DiarizationResult(duration=60.0)

    result.add_segment(SpeakerSegment(0.0, 15.0, "SPEAKER_00", 0.9))
    result.add_segment(SpeakerSegment(15.0, 30.0, "SPEAKER_01", 0.85))
    result.add_segment(SpeakerSegment(30.0, 45.0, "SPEAKER_00", 0.92))
    result.add_segment(SpeakerSegment(45.0, 60.0, "SPEAKER_01", 0.88))

    # 创建模拟转录
    utterances = [
        Utterance(0.0, 15.0, "大家好，欢迎参加会议"),
        Utterance(15.0, 30.0, "今天我们讨论项目进度"),
        Utterance(30.0, 45.0, "我这边前端已经完成"),
        Utterance(45.0, 60.0, "后端接口还需要两天"),
    ]

    # 对齐
    engine = MockSpeakerDiarization()
    aligned = engine.align_with_transcript(result, utterances)

    # 验证
    assert aligned[0].speaker == "SPEAKER_00"
    assert aligned[1].speaker == "SPEAKER_01"
    assert aligned[2].speaker == "SPEAKER_00"
    assert aligned[3].speaker == "SPEAKER_01"

    print("✓ 转录对齐功能正常")

    # 测试格式化输出
    from meeting_intelligence.speaker.ui import format_transcript_with_speakers

    formatted = format_transcript_with_speakers(aligned)

    print("\n示例输出：")
    print(formatted)

    print()
    print("测试通过！")
    return True


def main():
    """运行所有测试"""
    print()
    print("🧪 发言人识别模块测试")
    print()

    tests = [
        ("模拟发言人分离", test_mock_diarization),
        ("发言人管理器", test_speaker_manager),
        ("转录对齐", test_alignment),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
                print(f"❌ {name} 测试失败")
        except Exception as e:
            failed += 1
            print(f"❌ {name} 测试异常: {e}")
            import traceback
            traceback.print_exc()

    print()
    print("=" * 60)
    print(f"  测试结果: {passed} 通过, {failed} 失败")
    print("=" * 60)
    print()

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
