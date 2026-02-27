#!/usr/bin/env python3
"""
端到端测试脚本：处理腾讯会议视频
直接使用 Whisper Python API
"""

from pathlib import Path
from input.upload_video import upload_video
from audio.preprocess import preprocess_audio
import whisper
import json

# Windows 路径转 WSL 路径
VIDEO_PATH = "/mnt/c/Users/15666/Documents/TencentMeeting/2026-02-06 13.07.22.298/meeting_01.mp4"

def main():
    print("=" * 60)
    print("AI Meeting Assistant - 端到端测试 (Direct Whisper API)")
    print("=" * 60)

    # Step 1: 视频上传 + 音频提取
    print("\n[1/4] 视频上传 + 音频提取...")
    result = upload_video(VIDEO_PATH, extract_audio=True)
    print(f"  视频路径: {result.video_path}")
    print(f"  音频路径: {result.audio_path}")

    # Step 2: 音频预处理
    print("\n[2/4] 音频预处理（标准化）...")
    processed = preprocess_audio(result.audio_path)
    print(f"  处理后音频: {processed.path}")
    print(f"  音频时长: {processed.duration:.1f} 秒 ({processed.duration/60:.1f} 分钟)")

    # Step 3: ASR 转写（直接使用 Whisper API）
    print("\n[3/4] 语音转文字（ASR）...")
    print("  正在加载 Whisper 模型...")
    model = whisper.load_model("base")
    print("  开始转写，这可能需要几分钟...")

    # 转写
    transcribe_result = model.transcribe(
        processed.path,
        language="zh",  # 中文
        task="transcribe",
        word_timestamps=True
    )

    utterances = []
    for segment in transcribe_result["segments"]:
        utterances.append({
            "start": segment["start"],
            "end": segment["end"],
            "text": segment["text"].strip()
        })

    print(f"  识别到 {len(utterances)} 条语句")

    # Step 4: 保存转写结果
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    transcript_path = f"data/transcripts/transcript_{timestamp}.json"

    transcript_data = {
        "metadata": {
            "audio_path": processed.path,
            "duration": processed.duration,
            "utterance_count": len(utterances),
            "asr_provider": "whisper-local-base",
            "timestamp": datetime.now().isoformat()
        },
        "utterances": utterances
    }

    Path(transcript_path).parent.mkdir(parents=True, exist_ok=True)
    with open(transcript_path, "w", encoding="utf-8") as f:
        json.dump(transcript_data, f, ensure_ascii=False, indent=2)

    print(f"  转写文档: {transcript_path}")

    # Step 5: 展示结果
    print("\n[4/4] 转写结果预览:")
    print("-" * 60)

    # 显示前 15 条语句
    print(f"\n前 15 条语句:")
    for i, u in enumerate(utterances[:15], 1):
        print(f"  {i:2d}. [{u['start']:6.1f}s] {u['text']}")

    if len(utterances) > 15:
        print(f"  ... 还有 {len(utterances) - 15} 条语句")

    # 显示统计信息
    full_text = "".join(u["text"] for u in utterances)
    word_count = len(full_text)
    wpm = word_count / (processed.duration / 60) if processed.duration > 0 else 0

    print("\n" + "=" * 60)
    print("统计信息:")
    print(f"  会议时长: {processed.duration / 60:.1f} 分钟")
    print(f"  语句数量: {len(utterances)} 条")
    print(f"  总字数: {word_count} 字")
    print(f"  语速: {wpm:.0f} 字/分钟")
    print(f"  转写文档: {transcript_path}")
    print("=" * 60)

    # 导出 Markdown
    export_path = "data/output/meeting_transcript.md"
    Path("data/output").mkdir(exist_ok=True)

    with open(export_path, "w", encoding="utf-8") as f:
        f.write("# 会议转写\n\n")
        f.write(f"**会议时长**: {processed.duration / 60:.1f} 分钟  \n")
        f.write(f"**语句数量**: {len(utterances)} 条  \n")
        f.write(f"**总字数**: {word_count} 字  \n\n")
        f.write("---\n\n")

        for i, u in enumerate(utterances, 1):
            mins = int(u["start"] // 60)
            secs = int(u["start"] % 60)
            f.write(f"## [{mins:02d}:{secs:02d}] {u['text']}\n\n")

    print(f"\n已导出 Markdown: {export_path}")

    return transcript_path

if __name__ == "__main__":
    main()
