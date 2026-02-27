# Change: Add Audio Processing Module

## Why

Phase 1 实现了会议输入模块，但视频上传时缺少音频提取功能。音频处理模块是连接输入与 ASR 的桥梁，需要：
1. 从视频中提取音轨（完成 `upload_video.py` 的 TODO）
2. 对音频进行预处理，确保 ASR 获得高质量的输入

## What Changes

- **ADDED**: `audio/extract_audio.py` - 使用 ffmpeg 从视频中提取音频
- **ADDED**: `audio/preprocess.py` - 音频预处理（音量归一化、可选静音裁剪）
- **MODIFIED**: `input/upload_video.py` - 集成音频提取功能
- **ADDED**: 统一的 `ProcessedAudio` 接口

## Impact

- **Affected specs**: New capability `audio-processing`
- **Affected code**:
  - Creates new `audio/` module
  - Updates `input/upload_video.py` to use audio extraction
- **Dependencies**: Requires ffmpeg installed on system

## Key Design Decisions

1. **FFmpeg as standard**: 使用 ffmpeg 作为音视频处理工具（行业标准、稳定可靠）
2. **Standardized output**: 所有输出音频统一为 WAV 格式、16kHz 采样率、单声道
3. **Non-destructive**: 原始文件保留，处理后的文件另存
4. **Optional preprocessing**: 静音裁剪默认关闭，避免误删内容

## Technical Requirements

- FFmpeg must be installed on the system
- Output format: WAV, 16kHz, mono, 16-bit PCM
- Supports: mp4, mkv, mov video input
