# Change: Add Meeting Input Module

## Why

The AI Meeting Assistant V1 requires a unified interface to acquire meeting content from multiple sources (audio upload, video upload, and in-app recording). This is the foundational module that enables all downstream processing (ASR, transcript generation, summarization).

## What Changes

- **ADDED**: Audio file upload functionality (mp3, wav, m4a)
- **ADDED**: Video file upload functionality (mp4, mkv, mov) with automatic audio extraction
- **ADDED**: In-app audio recording functionality (local microphone capture)
- **ADDED**: Unified `MeetingInputResult` interface for all input methods
- **ADDED**: File validation and persistence to `data/raw_audio/`

## Impact

- **Affected specs**: New capability `meeting-input`
- **Affected code**: Creates new `input/` module with three files:
  - `input/upload_audio.py`
  - `input/upload_video.py`
  - `input/record_audio.py`
- **Dependencies**: Requires `audio/` module (to be implemented in Phase 2) for audio extraction from video

## Key Design Decisions

1. **Interface-First**: All three input methods return the same `MeetingInputResult` structure for consistency
2. **Persistence First**: All uploaded/recorded files are immediately saved to disk (not kept in memory)
3. **Validation**: File format and size validation before processing
4. **V2 Preparation**: Video files are preserved in full (not deleted after audio extraction) for future PPT analysis
