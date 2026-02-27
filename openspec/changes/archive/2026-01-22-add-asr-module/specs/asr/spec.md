## ADDED Requirements

### Requirement: Audio Speech Recognition

The system SHALL convert audio files to text with timestamps using an ASR service.

#### Scenario: Successful transcription of Chinese audio

- **WHEN** a valid Chinese audio file is provided
- **THEN** the system processes the audio with ASR
- **AND** returns text content in Chinese
- **AND** each utterance includes start and end timestamps
- **AND** timestamps are monotonically increasing
- **AND** saves the result to `data/transcripts/`

#### Scenario: Successful transcription of English audio

- **WHEN** a valid English audio file is provided
- **THEN** the system processes the audio with ASR
- **AND** returns text content in English
- **AND** each utterance includes start and end timestamps
- **AND** saves the result to storage

#### Scenario: Successful transcription of mixed Chinese-English audio

- **WHEN** an audio file with mixed Chinese and English is provided
- **THEN** the system correctly transcribes both languages
- **AND** maintains language consistency within utterances
- **AND** preserves timestamps accurately

#### Scenario: Empty or silent audio file

- **WHEN** an audio file contains no speech
- **THEN** the system returns an empty transcription result
- **AND** the result contains an empty utterance array
- **AND** no error is raised

#### Scenario: Unsupported audio format

- **WHEN** an audio file with incorrect format is provided
- **THEN** the system returns a clear error message
- **AND** indicates the required format (WAV, 16kHz, mono)

#### Scenario: ASR service unavailable

- **WHEN** the ASR service is unreachable or returns an error
- **THEN** the system returns a clear error message
- **AND** preserves the original audio file for retry

---

### Requirement: Timestamp Accuracy

The system SHALL provide accurate timestamps for each transcribed utterance.

#### Scenario: Timestamp monotonicity

- **WHEN** audio is transcribed
- **THEN** each utterance's start time is greater than or equal to the previous utterance's start time
- **AND** each utterance's end time is greater than its start time
- **AND** there are no overlapping timestamps

#### Scenario: Timestamp precision

- **WHEN** audio is transcribed
- **THEN** timestamps are provided with at least 0.1 second precision
- **AND** the first utterance starts at or near 0.0
- **AND** the last utterance ends near the total audio duration

#### Scenario: Long audio handling

- **WHEN** a long audio file (> 30 minutes) is transcribed
- **THEN** timestamps remain accurate throughout
- **AND** no timestamp drift occurs
- **AND** the total duration matches the audio length

---

### Requirement: ASR Result Persistence

The system SHALL save transcription results to disk for later use.

#### Scenario: Result file creation

- **WHEN** transcription completes successfully
- **THEN** the system creates a JSON file in `data/transcripts/`
- **AND** the filename includes a timestamp
- **AND** the file contains the complete transcription data

#### Scenario: Result file format

- **WHEN** a transcription result is saved
- **THEN** the JSON file contains an array of utterances
- **AND** each utterance has `start`, `end`, and `text` fields
- **AND** the file is valid JSON (parseable)

#### Scenario: Result file metadata

- **WHEN** a transcription result is saved
- **THEN** the result includes metadata
- **AND** metadata contains: audio_path, duration, timestamp, asr_provider

---

### Requirement: Transcription Result Interface

The system SHALL return a consistent `TranscriptionResult` structure.

#### Scenario: Successful transcription result

- **WHEN** transcription completes successfully
- **THEN** the system returns a `TranscriptionResult` object
- **AND** the object contains `utterances` (array of {start, end, text})
- **AND** the object contains `audio_path` (source audio file)
- **AND** the object contains `duration` (total audio duration in seconds)
- **AND** the object contains `output_path` (saved JSON file path)

#### Scenario: Empty transcription result

- **WHEN** audio contains no speech
- **THEN** the system returns a `TranscriptionResult` with empty utterances
- **AND** other fields (audio_path, duration, output_path) are still populated

#### Scenario: Result validation

- **WHEN** a `TranscriptionResult` is returned
- **THEN** all file paths point to existing files
- **AND** duration is greater than 0
- **AND** utterances array is properly formatted

---

### Requirement: ASR Provider Abstraction

The system SHALL support multiple ASR providers through a unified interface.

#### Scenario: Default provider (Whisper)

- **WHEN** no provider is specified
- **THEN** the system uses the default Whisper provider
- **AND** Whisper runs in local or API mode based on configuration

#### Scenario: Provider switching

- **WHEN** a different provider is specified
- **THEN** the system uses the specified provider
- **AND** returns results in the same format as the default provider

#### Scenario: Provider unavailable fallback

- **WHEN** the primary provider fails
- **THEN** the system attempts fallback to alternative providers (if configured)
- **OR** returns a clear error if no fallback is available
