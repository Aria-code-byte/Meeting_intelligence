"""
build_turns word-level speaker 切分测试
======================================
验证修正后的 build_turns 正确处理 word-level speaker 切分
"""
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.whisperx_service import build_turns, DIARIZATION_MERGE_GAP
import services.whisperx_service as ws


# ============================================================
# 测试 1：words 中 speaker 切换必须拆分
# ============================================================

def test_word_level_speaker_split():
    """测试 word-level speaker 切换生成 2 个 turn"""
    print("\n[测试 1] word-level speaker 切换")

    segments = [
        {
            "start": 0.0,
            "end": 1.8,
            "text": "大家好我补充",
            "words": [
                {"word": "大家", "start": 0.0, "end": 0.5, "speaker": "SPEAKER_00"},
                {"word": "好", "start": 0.5, "end": 0.8, "speaker": "SPEAKER_00"},
                {"word": "我", "start": 1.0, "end": 1.2, "speaker": "SPEAKER_01"},
                {"word": "补充", "start": 1.2, "end": 1.8, "speaker": "SPEAKER_01"},
            ]
        }
    ]

    turns = build_turns(segments, diarization_enabled=True)

    print(f"  生成 {len(turns)} 个 turn")

    if len(turns) != 2:
        print(f"  ❌ 期望 2 个 turn，实际 {len(turns)}")
        for i, turn in enumerate(turns):
            print(f"     turn[{i}]: speaker={turn['speaker']}, text={turn['text']}")
        return False

    if turns[0]["speaker"] != "SPEAKER_00":
        print(f"  ❌ turns[0].speaker 期望 SPEAKER_00，实际 {turns[0]['speaker']}")
        return False

    if turns[0]["text"] != "大家好":
        print(f"  ❌ turns[0].text 期望 '大家好'，实际 '{turns[0]['text']}'")
        return False

    if turns[1]["speaker"] != "SPEAKER_01":
        print(f"  ❌ turns[1].speaker 期望 SPEAKER_01，实际 {turns[1]['speaker']}")
        return False

    if turns[1]["text"] != "我补充":
        print(f"  ❌ turns[1].text 期望 '我补充'，实际 '{turns[1]['text']}'")
        return False

    print(f"  ✅ 正确生成 2 个 turn")
    print(f"     turn[0]: speaker={turns[0]['speaker']}, text={turns[0]['text']}")
    print(f"     turn[1]: speaker={turns[1]['speaker']}, text={turns[1]['text']}")
    return True


# ============================================================
# 测试 2：segment 有 speaker 字段时的 fallback
# ============================================================

def test_segment_speaker_fallback():
    """测试 segment.speaker 的 fallback 逻辑"""
    print("\n[测试 2] segment.speaker fallback")

    segments = [
        {
            "speaker": "SPEAKER_02",
            "text": "没有 word 级 speaker 的片段",
            "start": 0.0,
            "end": 2.0,
            "words": []
        }
    ]

    turns = build_turns(segments, diarization_enabled=True)

    if len(turns) != 1:
        print(f"  ❌ 期望 1 个 turn，实际 {len(turns)}")
        return False

    if turns[0]["speaker"] != "SPEAKER_02":
        print(f"  ❌ speaker 期望 SPEAKER_02，实际 {turns[0]['speaker']}")
        return False

    print(f"  ✅ 正确使用 segment.speaker: {turns[0]['speaker']}")
    return True


# ============================================================
# 测试 3：完全无 speaker 时的 UNKNOWN fallback
# ============================================================

def test_unknown_fallback():
    """测试完全无 speaker 时的 UNKNOWN fallback"""
    print("\n[测试 3] UNKNOWN fallback")

    segments = [
        {
            "start": 0.0,
            "end": 2.0,
            "text": "测试文本",
            "words": [
                {"word": "测", "start": 0.0, "end": 0.5},
                {"word": "试", "start": 0.5, "end": 1.0},
                {"word": "文", "start": 1.0, "end": 1.5},
                {"word": "本", "start": 1.5, "end": 2.0},
            ]
        }
    ]

    turns = build_turns(segments, diarization_enabled=True)

    if len(turns) != 1:
        print(f"  ❌ 期望 1 个 turn，实际 {len(turns)}")
        return False

    if turns[0]["speaker"] != "UNKNOWN":
        print(f"  ❌ speaker 期望 UNKNOWN，实际 {turns[0]['speaker']}")
        return False

    print(f"  ✅ 正确使用 UNKNOWN")
    return True


# ============================================================
# 测试 4：merge_gap 合并（同 speaker）
# ============================================================

def test_merge_gap_merge():
    """测试 merge_gap 合并同 speaker"""
    print("\n[测试 4] merge_gap 合并")

    # 临时设置 merge_gap 为 1.0
    original_gap = ws.DIARIZATION_MERGE_GAP
    ws.DIARIZATION_MERGE_GAP = 1.0

    try:
        segments = [
            {
                "start": 0.0,
                "end": 1.0,
                "text": "第一段",
                "words": [
                    {"word": "第", "start": 0.0, "end": 0.3, "speaker": "SPEAKER_00"},
                    {"word": "一", "start": 0.3, "end": 0.6, "speaker": "SPEAKER_00"},
                    {"word": "段", "start": 0.6, "end": 1.0, "speaker": "SPEAKER_00"},
                ]
            },
            {
                "start": 1.5,  # gap = 0.5 < merge_gap (1.0)
                "end": 2.5,
                "text": "第二段",
                "words": [
                    {"word": "第", "start": 1.5, "end": 1.8, "speaker": "SPEAKER_00"},
                    {"word": "二", "start": 1.8, "end": 2.2, "speaker": "SPEAKER_00"},
                    {"word": "段", "start": 2.2, "end": 2.5, "speaker": "SPEAKER_00"},
                ]
            }
        ]

        turns = build_turns(segments, diarization_enabled=True)

        if len(turns) != 1:
            print(f"  ❌ 期望合并为 1 个 turn，实际 {len(turns)}")
            return False

        if "第一段" not in turns[0]["text"] or "第二段" not in turns[0]["text"]:
            print(f"  ❌ 文本未合并: '{turns[0]['text']}'")
            return False

        print(f"  ✅ 正确合并为 1 个 turn: text={turns[0]['text']}")
        return True

    finally:
        ws.DIARIZATION_MERGE_GAP = original_gap


# ============================================================
# 测试 5：merge_gap 不合并（大间隔）
# ============================================================

def test_merge_gap_no_merge():
    """测试 merge_gap 大间隔时不合并"""
    print("\n[测试 5] merge_gap 大间隔不合并")

    # 临时设置 merge_gap 为 1.0
    original_gap = ws.DIARIZATION_MERGE_GAP
    ws.DIARIZATION_MERGE_GAP = 1.0

    try:
        segments = [
            {
                "start": 0.0,
                "end": 1.0,
                "text": "第一段",
                "words": [
                    {"word": "第", "start": 0.0, "end": 0.3, "speaker": "SPEAKER_00"},
                    {"word": "一", "start": 0.3, "end": 0.6, "speaker": "SPEAKER_00"},
                    {"word": "段", "start": 0.6, "end": 1.0, "speaker": "SPEAKER_00"},
                ]
            },
            {
                "start": 3.0,  # gap = 2.0 > merge_gap (1.0)
                "end": 4.0,
                "text": "第二段",
                "words": [
                    {"word": "第", "start": 3.0, "end": 3.3, "speaker": "SPEAKER_00"},
                    {"word": "二", "start": 3.3, "end": 3.6, "speaker": "SPEAKER_00"},
                    {"word": "段", "start": 3.6, "end": 4.0, "speaker": "SPEAKER_00"},
                ]
            }
        ]

        turns = build_turns(segments, diarization_enabled=True)

        if len(turns) != 2:
            print(f"  ❌ 期望 2 个 turn（不合并），实际 {len(turns)}")
            return False

        print(f"  ✅ 正确保留 2 个 turn（gap 过大）")
        return True

    finally:
        ws.DIARIZATION_MERGE_GAP = original_gap


# ============================================================
# 测试 6：多次 speaker 切换
# ============================================================

def test_multiple_speaker_switches():
    """测试多次 speaker 切换"""
    print("\n[测试 6] 多次 speaker 切换")

    segments = [
        {
            "start": 0.0,
            "end": 4.0,
            "text": "你好我也好",
            "words": [
                {"word": "你", "start": 0.0, "end": 0.3, "speaker": "SPEAKER_00"},
                {"word": "好", "start": 0.3, "end": 0.6, "speaker": "SPEAKER_00"},
                {"word": "我", "start": 1.0, "end": 1.3, "speaker": "SPEAKER_01"},
                {"word": "也", "start": 2.0, "end": 2.3, "speaker": "SPEAKER_02"},
                {"word": "好", "start": 3.0, "end": 3.3, "speaker": "SPEAKER_00"},
            ]
        }
    ]

    turns = build_turns(segments, diarization_enabled=True)

    # SPEAKER_00 -> SPEAKER_01 -> SPEAKER_02 -> SPEAKER_00
    # 应该生成 4 个 turn
    if len(turns) != 4:
        print(f"  ❌ 期望 4 个 turn，实际 {len(turns)}")
        for i, turn in enumerate(turns):
            print(f"     turn[{i}]: speaker={turn['speaker']}, text={turn['text']}")
        return False

    expected = ["SPEAKER_00", "SPEAKER_01", "SPEAKER_02", "SPEAKER_00"]
    for i, turn in enumerate(turns):
        if turn["speaker"] != expected[i]:
            print(f"  ❌ turns[{i}].speaker 期望 {expected[i]}，实际 {turn['speaker']}")
            return False

    print(f"  ✅ 正确生成 4 个 turn: {[t['speaker'] for t in turns]}")
    return True


# ============================================================
# 主测试运行器
# ============================================================

def run_all_tests():
    """运行所有测试"""
    print("="*60)
    print("build_turns word-level speaker 切分测试")
    print("="*60)

    tests = [
        ("word-level speaker 切换", test_word_level_speaker_split),
        ("segment.speaker fallback", test_segment_speaker_fallback),
        ("UNKNOWN fallback", test_unknown_fallback),
        ("merge_gap 合并", test_merge_gap_merge),
        ("merge_gap 大间隔不合并", test_merge_gap_no_merge),
        ("多次 speaker 切换", test_multiple_speaker_switches),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"\n❌ {test_name} 测试失败: {e}")
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
