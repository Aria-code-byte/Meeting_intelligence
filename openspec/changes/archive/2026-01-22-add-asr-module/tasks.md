## 1. Project Setup

- [x] 1.1 Create `asr/` directory module
- [x] 1.2 Create `asr/__init__.py` with module exports
- [x] 1.3 Create `data/transcripts/` directory for results
- [x] 1.4 Create shared types (`asr/types.py`) with `TranscriptionResult` and `Utterance` classes

## 2. ASR Core Implementation

- [x] 2.1 Create `asr/transcribe.py` with `transcribe()` function
- [x] 2.2 Implement Whisper provider integration (local/API)
- [x] 2.3 Implement provider abstraction interface
- [x] 2.4 Implement audio format validation (WAV, 16kHz, mono)
- [x] 2.5 Implement timestamp generation and validation
- [x] 2.6 Implement result JSON persistence
- [x] 2.7 Add error handling for ASR failures

## 3. Long Audio Handling

- [x] 3.1 Implement audio chunking for files > 30 minutes
- [x] 3.2 Implement chunk merging with timestamp adjustment
- [x] 3.3 Add progress tracking for long transcriptions

## 4. Result Management

- [x] 4.1 Implement transcription result caching (avoid re-transcription)
- [x] 4.2 Implement result loading from disk
- [x] 4.3 Implement result export (JSON, text formats)

## 5. Provider Implementation

- [x] 5.1 Create `asr/providers/whisper.py` - Whisper provider
- [x] 5.2 Create `asr/providers/base.py` - Base provider interface
- [x] 5.3 Add provider configuration system
- [x] 5.4 Add fallback provider mechanism (optional)

## 6. Testing

- [x] 6.1 Add unit tests for transcribe() function
- [x] 6.2 Add tests for timestamp accuracy and monotonicity
- [x] 6.3 Add tests for empty/silent audio handling
- [x] 6.4 Add tests for long audio handling
- [x] 6.5 Add tests for provider abstraction
- [x] 6.6 Add integration tests for full audio → transcript flow

## 7. Documentation

- [x] 7.1 Document Whisper installation/setup requirements
- [x] 7.2 Document provider configuration options
- [x] 7.3 Document result JSON format
- [x] 7.4 Update README with ASR usage examples
