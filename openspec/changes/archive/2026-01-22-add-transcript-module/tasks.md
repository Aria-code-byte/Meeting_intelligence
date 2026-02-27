## 1. Project Setup

- [x] 1.1 Create `transcript/` directory module
- [x] 1.2 Create `transcript/__init__.py` with module exports
- [x] 1.3 Create `data/transcripts/` directory for documents
- [x] 1.4 Create shared types (`transcript/types.py`) with `TranscriptDocument` class

## 2. Transcript Types Implementation

- [x] 2.1 Create `TranscriptDocument` class with metadata fields
- [x] 2.2 Add validation for required metadata (audio_path, duration, asr_provider)
- [x] 2.3 Add `to_dict()` method for serialization
- [x] 2.4 Add validation for empty/invalid content

## 3. Core Transcript Building

- [x] 3.1 Create `transcript/build.py` with `build_transcript()` function
- [x] 3.2 Implement ASR result to transcript conversion
- [x] 3.3 Implement utterance grouping into readable paragraphs
- [x] 3.4 Implement timestamp formatting (human-readable)
- [x] 3.5 Add metadata generation (creation time, source info)
- [x] 3.6 Implement result persistence to `data/transcripts/`

## 4. Document Loading

- [x] 4.1 Create `transcript/load.py` with `load_transcript()` function
- [x] 4.2 Implement JSON document loading
- [x] 4.3 Add validation for corrupted/malformed documents
- [x] 4.4 Add error handling for missing files

## 5. Export Functionality

- [x] 5.1 Create `transcript/export.py` with export functions
- [x] 5.2 Implement JSON export (complete data)
- [x] 5.3 Implement plain text export (readable format)
- [x] 5.4 Implement Markdown export (formatted with timestamps)
- [x] 5.5 Add export path validation

## 6. Integration with ASR

- [x] 6.1 Update `asr/transcribe.py` to optionally trigger transcript build
- [x] 6.2 Add `auto_build_transcript` parameter to transcribe function
- [x] 6.3 Ensure transcript builds after successful ASR completion
- [x] 6.4 Return transcript path in TranscriptionResult (optional field)

## 7. Testing

- [x] 7.1 Add unit tests for TranscriptDocument type
- [x] 7.2 Add unit tests for build_transcript() function
- [x] 7.3 Add tests for paragraph grouping logic
- [x] 7.4 Add tests for document loading (valid, invalid, missing)
- [x] 7.5 Add tests for export formats (JSON, TXT, MD)
- [x] 7.6 Add integration tests for ASR → Transcript flow

## 8. Documentation

- [x] 8.1 Document transcript document structure
- [x] 8.2 Document export format differences
- [x] 8.3 Update README with transcript usage examples
- [x] 8.4 Add examples of generated transcript formats
