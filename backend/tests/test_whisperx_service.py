"""
WhisperX Service 单元测试
==========================
验证 build_turns 核心逻辑、HF_TOKEN 处理、JSON 序列化等
"""
import json
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.whisperx_service import (
    clean_text,
    join_words,
    speaker_for_segment,
    add_turn,
    build_turns,
    _get_env,
    DIARIZATION_MERGE_GAP,
)


# ============================================================
# 测试辅助函数
# ============================================================

def test_clean_text():
    """测试文本清理"""
    print("\n[测试] clean_text")

    # 正常文本
    assert clean_text("  hello world  ") == "hello world"
    print("  ✅ 正常文本清理")

    # 多余空格
    assert clean_text("hello    world") == "hello world"
    print("  ✅ 多余空格清理")

    # 空文本
    assert clean_text("") == ""
    assert clean_text(None) == ""
    print("  ✅ 空文本处理")


def test_join_words():
    """测试词拼接"""
    print("\n[测试] join_words")

    words = [
        {"word": "hello"},
        {"word": "world"},
    ]
    assert join_words(words) == "hello world"
    print("  ✅ 基本拼接")

    # 自定义分隔符
    assert join_words(words, separator="_") == "hello_world"
    print("  ✅ 自定义分隔符")

    # 空列表
    assert join_words([]) == ""
    print("  ✅ 空列表")


def test_speaker_for_segment():
    """测试说话人识别"""
    print("\n[测试] speaker_for_segment")

    # 单一说话人
    words = [
        {"word": "hello", "speaker": "SPEAKER_00"},
        {"word": "world", "speaker": "SPEAKER_00"},
    ]
    assert speaker_for_segment(words) == "SPEAKER_00"
    print("  ✅ 单一说话人")

    # 多说话人，返回词数最多的
    words = [
        {"word": "a", "speaker": "SPEAKER_00"},
        {"word": "b", "speaker": "SPEAKER_00"},
        {"word": "c", "speaker": "SPEAKER_01"},
    ]
    assert speaker_for_segment(words) == "SPEAKER_00"
    print("  ✅ 多说话人 - 返回词数最多的")

    # 无说话人信息
    assert speaker_for_segment([]) is None
    assert speaker_for_segment([{"word": "hello"}]) is None
    print("  ✅ 无说话人信息")


# ============================================================
# 测试 add_turn
# ============================================================

def test_add_turn():
    """测试添加轮次"""
    print("\n[测试] add_turn")

    turns = []

    # 添加第一个轮次
    add_turn(turns, "SPEAKER_00", 0.0, 2.0, "Hello")
    assert len(turns) == 1
    assert turns[0]["speaker"] == "SPEAKER_00"
    assert turns[0]["text"] == "Hello"
    print("  ✅ 添加第一个轮次")

    # 添加不同说话人的轮次
    add_turn(turns, "SPEAKER_01", 2.5, 4.0, "World")
    assert len(turns) == 2
    assert turns[1]["speaker"] == "SPEAKER_01"
    print("  ✅ 添加不同说话人的轮次")

    # 相同说话人，小间隔，应该合并
    add_turn(turns, "SPEAKER_01", 4.2, 6.0, "Again")
    assert len(turns) == 2  # 没有新增
    assert turns[1]["end"] == 6.0
    assert "Again" in turns[1]["text"]
    print("  ✅ 相同说话人小间隔 - 合并")

    # 相同说话人，大间隔，应该新增
    turns2 = []
    add_turn(turns2, "SPEAKER_00", 0.0, 1.0, "Hello")
    add_turn(turns2, "SPEAKER_00", 5.0, 6.0, "World")  # gap = 4.0 > merge_gap
    assert len(turns2) == 2
    print("  ✅ 相同说话人大间隔 - 新增")

    # 空文本不应该生成轮次
    add_turn(turns, "SPEAKER_02", 10.0, 11.0, "")
    assert len(turns) == 2
    add_turn(turns, "SPEAKER_02", 10.0, 11.0, "   ")
    assert len(turns) == 2
    print("  ✅ 空文本不生成轮次")


# ============================================================
# 测试 build_turns - 核心场景
# ============================================================

def test_build_turns_scenario_1():
    """场景 1: 同一 speaker 连续 words"""
    print("\n[测试场景 1] 同一 speaker 连续 words")

    segments = [
        {
            "start": 0.0,
            "end": 0.8,
            "text": "大家好",
            "words": [
                {"word": "大家", "start": 0.0, "end": 0.5, "speaker": "SPEAKER_00"},
                {"word": "好", "start": 0.5, "end": 0.8, "speaker": "SPEAKER_00"}
            ]
        }
    ]

    turns = build_turns(segments, diarization_enabled=True)

    assert len(turns) == 1, f"期望 1 个 turn，实际 {len(turns)}"
    assert turns[0]["speaker"] == "SPEAKER_00"
    assert turns[0]["text"] == "大家好"
    print(f"  ✅ 生成 1 个 turn: speaker={turns[0]['speaker']}, text={turns[0]['text']}")


def test_build_turns_scenario_2():
    """场景 2: words 中 speaker 切换"""
    print("\n[测试场景 2] words 中 speaker 切换")

    segments = [
        {
            "start": 0.0,
            "end": 1.0,
            "text": "你好世界",
            "words": [
                {"word": "你好", "start": 0.0, "end": 0.5, "speaker": "SPEAKER_00"},
                {"word": "世界", "start": 0.5, "end": 1.0, "speaker": "SPEAKER_01"}
            ]
        }
    ]

    turns = build_turns(segments, diarization_enabled=True)

    # speaker_for_segment 返回词数最多的说话人
    # 这里两个词各一个，应该返回第一个
    assert len(turns) >= 1
    # 由于 segment 中两个说话人词数相同，speaker_for_segment 会返回第一个
    # 所以整个 segment 被分配给 SPEAKER_00
    print(f"  ℹ️  segment 中多说话人: 主要说话人={turns[0]['speaker']}, text={turns[0]['text']}")
    print("  ℹ️  这是正常行为 - speaker_for_segment 基于 segment 内的多数词")


def test_build_turns_scenario_3():
    """场景 3: 相邻同 speaker 且 gap <= merge_gap"""
    print("\n[测试场景 3] 相邻同 speaker 且 gap <= merge_gap")

    # 修改 merge_gap 为 2.0 秒以方便测试
    import services.whisperx_service as ws
    original_gap = ws.DIARIZATION_MERGE_GAP
    ws.DIARIZATION_MERGE_GAP = 2.0

    segments = [
        {
            "start": 0.0,
            "end": 1.0,
            "text": "你好",
            "words": [{"word": "你好", "start": 0.0, "end": 1.0, "speaker": "SPEAKER_00"}]
        },
        {
            "start": 1.5,  # gap = 0.5 < merge_gap (2.0)
            "end": 2.5,
            "text": "世界",
            "words": [{"word": "世界", "start": 1.5, "end": 2.5, "speaker": "SPEAKER_00"}]
        }
    ]

    turns = build_turns(segments, diarization_enabled=True)

    assert len(turns) == 1, f"期望合并为 1 个 turn，实际 {len(turns)}"
    assert turns[0]["speaker"] == "SPEAKER_00"
    assert "你好" in turns[0]["text"]
    assert "世界" in turns[0]["text"]
    print(f"  ✅ 合并为 1 个 turn: text={turns[0]['text']}")

    # 恢复原始 gap
    ws.DIARIZATION_MERGE_GAP = original_gap


def test_build_turns_scenario_4():
    """场景 4: 没有 speaker"""
    print("\n[测试场景 4] 没有 speaker")

    segments = [
        {
            "start": 0.0,
            "end": 1.0,
            "text": "你好",
            "words": [{"word": "你好", "start": 0.0, "end": 1.0}]  # 无 speaker
        }
    ]

    turns = build_turns(segments, diarization_enabled=True)

    assert len(turns) == 1
    assert turns[0]["speaker"] == "UNKNOWN"
    print(f"  ✅ 无 speaker 时使用 UNKNOWN: {turns[0]['speaker']}")


def test_build_turns_no_diarization():
    """不启用说话人分离"""
    print("\n[测试] 不启用说话人分离")

    segments = [
        {
            "start": 0.0,
            "end": 1.0,
            "text": "你好",
            "words": [{"word": "你好", "start": 0.0, "end": 1.0, "speaker": "SPEAKER_00"}]
        }
    ]

    turns = build_turns(segments, diarization_enabled=False)

    assert len(turns) == 1
    assert turns[0]["speaker"] == "SPEAKER"
    print(f"  ✅ 不启用 diarization 时使用 SPEAKER: {turns[0]['speaker']}")


# ============================================================
# JSON 序列化测试
# ============================================================

def test_json_serialization():
    """测试返回结构可 JSON 序列化"""
    print("\n[测试] JSON 序列化")

    # 模拟 transcribe_with_whisperx 返回结构
    result = {
        "text": "测试文本",
        "language": "zh",
        "provider": "whisperx",
        "model": "large-v3-turbo",
        "segments": [
            {
                "start": 0.0,
                "end": 1.0,
                "text": "你好",
                "words": [{"word": "你好", "start": 0.0, "end": 1.0}]
            }
        ],
        "turns": [
            {"speaker": "SPEAKER_00", "start": 0.0, "end": 1.0, "text": "你好"}
        ],
        "diarizationEnabled": True,
        "diarizationProvider": "pyannote",
        "diarizationModel": "pyannote/speaker-diarization-community-1",
        "raw": {
            "processingTimeSeconds": 1.5,
            "audioPath": "/path/to/audio.wav",
            "languageDetected": "zh",
        }
    }

    try:
        json_str = json.dumps(result, ensure_ascii=False)
        parsed = json.loads(json_str)
        assert parsed["text"] == "测试文本"
        print("  ✅ JSON 序列化成功")
    except Exception as e:
        print(f"  ❌ JSON 序列化失败: {e}")
        raise


# ============================================================
# 主测试运行器
# ============================================================

def run_all_tests():
    """运行所有测试"""
    print("="*60)
    print("WhisperX Service 单元测试")
    print("="*60)

    tests = [
        ("辅助函数", [test_clean_text, test_join_words, test_speaker_for_segment]),
        ("add_turn", [test_add_turn]),
        ("build_turns 场景 1", [test_build_turns_scenario_1]),
        ("build_turns 场景 2", [test_build_turns_scenario_2]),
        ("build_turns 场景 3", [test_build_turns_scenario_3]),
        ("build_turns 场景 4", [test_build_turns_scenario_4]),
        ("build_turns 无 diarization", [test_build_turns_no_diarization]),
        ("JSON 序列化", [test_json_serialization]),
    ]

    passed = 0
    failed = 0

    for group_name, group_tests in tests:
        try:
            for test in group_tests:
                test()
            passed += len(group_tests)
        except AssertionError as e:
            print(f"  ❌ 断言失败: {e}")
            failed += 1
        except Exception as e:
            print(f"  ❌ 测试失败: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print("\n" + "="*60)
    print(f"测试结果: {passed} 通过, {failed} 失败")
    print("="*60)

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
