## 1. Project Setup

- [x] 1.1 Create `audio/` directory module
- [x] 1.2 Create `audio/__init__.py` with module exports
- [x] 1.3 Create shared types (`audio/types.py`) with `ProcessedAudio` class

## 2. Audio Extraction Implementation

- [x] 2.1 Create `audio/extract_audio.py` with `extract_audio()` function
- [x] 2.2 Implement ffmpeg availability check
- [x] 2.3 Implement audio extraction from video (mp4, mkv, mov)
- [x] 2.4 Implement output format standardization (WAV, 16kHz, mono, 16-bit)
- [x] 2.5 Implement duration calculation using ffprobe or file analysis
- [x] 2.6 Add error handling for corrupted videos and missing audio tracks
- [x] 2.7 Add unit tests for extraction (valid videos, no audio, ffmpeg unavailable)

## 3. Audio Preprocessing Implementation

- [x] 3.1 Create `audio/preprocess.py` with `preprocess_audio()` function
- [x] 3.2 Implement volume normalization using ffmpeg
- [x] 3.3 Implement optional silence trimming (disabled by default)
- [x] 3.4 Implement skip preprocessing option (pass-through)
- [x] 3.5 Add unit tests for preprocessing (normalization, trimming, skip)

## 4. Integration with Video Upload

- [x] 4.1 Update `input/upload_video.py` to import and use `audio.extract_audio()`
- [x] 4.2 Remove TODO comment and implement audio extraction call
- [x] 4.3 Update `MeetingInputResult` to include extracted audio path
- [x] 4.4 Update unit tests to reflect audio extraction integration

## 5. Validation and Testing

- [x] 5.1 Verify ffmpeg is installed (add check/setup instructions)
- [x] 5.2 Test all video formats (mp4, mkv, mov) produce consistent output
- [x] 5.3 Verify output format consistency (16kHz, mono, WAV)
- [x] 5.4 Add integration tests for full video upload → audio extraction flow
- [x] 5.5 Test error handling (ffmpeg unavailable, corrupted files)

## 6. Documentation

- [x] 6.1 Add ffmpeg installation instructions to README
- [x] 6.2 Document audio output format specifications
- [x] 6.3 Document preprocessing options and defaults
