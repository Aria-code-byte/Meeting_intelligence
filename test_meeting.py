#!/usr/bin/env python3
"""
端到端测试脚本：处理腾讯会议视频
"""

from pathlib import Path
from input.upload_video import upload_video
from audio.preprocess import preprocess_audio
from asr import transcribe
from transcript import load_transcript, export_markdown

# Windows 路径转 WSL 路径
VIDEO_PATH = "/mnt/c/Users/15666/Documents/TencentMeeting/2026-02-06 13.07.22.298/meeting_01.mp4"

def main():
    print("=" * 60)
    print("AI Meeting Assistant - 端到端测试")
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

    # Step 3: ASR 转写
    print("\n[3/4] 语音转文字（ASR）...")
    print("  这可能需要几分钟，请耐心等待...")
    transcription = transcribe(processed.path, auto_build_transcript=True)
    print(f"  识别到 {len(transcription.utterances)} 条语句")
    print(f"  转写文档: {transcription.transcript_path}")

    # Step 4: 展示结果
    print("\n[4/4] 转写结果预览:")
    print("-" * 60)

    doc = load_transcript(transcription.transcript_path)

    # 显示前 10 条语句
    print(f"\n前 10 条语句:")
    for i, u in enumerate(doc.utterances[:10], 1):
        print(f"  {i:2d}. [{u.start:6.1f}s] {u.text}")

    if len(doc.utterances) > 10:
        print(f"  ... 还有 {len(doc.utterances) - 10} 条语句")

    # 显示统计信息
    full_text = doc.get_full_text()
    word_count = len(full_text)
    wpm = word_count / (doc.metadata.duration / 60) if doc.metadata.duration > 0 else 0

    print("\n" + "=" * 60)
    print("统计信息:")
    print(f"  会议时长: {doc.metadata.duration / 60:.1f} 分钟")
    print(f"  语句数量: {len(doc.utterances)} 条")
    print(f"  总字数: {word_count} 字")
    print(f"  语速: {wpm:.0f} 字/分钟")
    print(f"  转写文档: {transcription.transcript_path}")
    print("=" * 60)

    # 导出 Markdown
    export_path = "data/output/meeting_transcript.md"
    Path("data/output").mkdir(exist_ok=True)
    export_markdown(doc, export_path)
    print(f"\n已导出 Markdown: {export_path}")

    return transcription

if __name__ == "__main__":
    main()
