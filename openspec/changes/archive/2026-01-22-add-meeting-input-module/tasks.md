## 1. Project Setup

- [x] 1.1 Create `input/` directory module
- [x] 1.2 Create `data/raw_audio/` directory for persistence
- [x] 1.3 Create shared types module (`types.py`) with `MeetingInputResult` class

## 2. Audio Upload Implementation

- [x] 2.1 Create `input/upload_audio.py` with `upload_audio()` function
- [x] 2.2 Implement file format validation (mp3, wav, m4a)
- [x] 2.3 Implement file size validation (configurable limit)
- [x] 2.4 Implement file persistence to `data/raw_audio/`
- [x] 2.5 Add unit tests for audio upload (valid file, invalid format, oversized file)

## 3. Video Upload Implementation

- [x] 3.1 Create `input/upload_video.py` with `upload_video()` function
- [x] 3.2 Implement file format validation (mp4, mkv, mov)
- [x] 3.3 Implement video file preservation (save original to `data/raw_audio/`)
- [x] 3.4 Add stub for `audio.extract_audio()` integration (to be implemented in Phase 2)
- [x] 3.5 Implement `MeetingInputResult` return with both paths populated
- [x] 3.6 Add unit tests for video upload (valid file, invalid format, no audio track)

## 4. Audio Recording Implementation

- [x] 4.1 Create `input/record_audio.py` with `start_recording()` and `stop_recording()` functions
- [x] 4.2 Implement microphone capture using platform-appropriate audio library
- [x] 4.3 Implement segmented audio saving (prevent memory issues for long recordings)
- [x] 4.4 Implement timestamp-based filename generation
- [x] 4.5 Add maximum duration enforcement (configurable, default 2 hours)
- [x] 4.6 Add unit tests for recording (start/stop, max duration, no microphone)

## 5. Integration and Validation

- [x] 5.1 Verify all three methods return consistent `MeetingInputResult` structure
- [x] 5.2 Add integration tests for end-to-end input workflows
- [x] 5.3 Verify file path correctness in all returned results
- [x] 5.4 Test error handling and error messages for all failure modes
