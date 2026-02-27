## ADDED Requirements

### Requirement: Audio File Upload

The system SHALL allow users to upload audio files and persist them to storage.

#### Scenario: Successful audio upload

- **WHEN** a user uploads a valid audio file (mp3, wav, m4a)
- **THEN** the system validates the file format
- **AND** saves the file to `data/raw_audio/`
- **AND** returns a `MeetingInputResult` with `audio_path` pointing to the saved file
- **AND** `video_path` is `null`

#### Scenario: Invalid audio format

- **WHEN** a user uploads a file with an unsupported format
- **THEN** the system rejects the file
- **AND** returns a clear error message indicating supported formats

#### Scenario: Audio file exceeds size limit

- **WHEN** a user uploads an audio file exceeding the configured size limit
- **THEN** the system rejects the file
- **AND** returns an error message indicating the size limitation

---

### Requirement: Video File Upload with Audio Extraction

The system SHALL allow users to upload video files and extract the audio track.

#### Scenario: Successful video upload with audio extraction

- **WHEN** a user uploads a valid video file (mp4, mkv, mov)
- **THEN** the system validates the video format
- **AND** saves the original video file to `data/raw_audio/`
- **AND** extracts the audio track using ffmpeg
- **AND** saves the extracted audio to `data/raw_audio/`
- **AND** returns a `MeetingInputResult` with both `audio_path` and `video_path` populated

#### Scenario: Invalid video format

- **WHEN** a user uploads a file with an unsupported video format
- **THEN** the system rejects the file
- **AND** returns a clear error message indicating supported formats

#### Scenario: Video file has no audio track

- **WHEN** a user uploads a video file without an audio track
- **THEN** the system detects the missing audio
- **AND** returns an error message indicating the video must contain audio

---

### Requirement: In-App Audio Recording

The system SHALL allow users to record audio directly within the application.

#### Scenario: Start and stop recording

- **WHEN** a user initiates audio recording
- **THEN** the system begins capturing audio from the default microphone
- **AND** when the user stops recording
- **AND** the audio is saved to `data/raw_audio/` with a timestamp-based filename
- **AND** returns a `MeetingInputResult` with `audio_path` pointing to the recorded file

#### Scenario: Recording exceeds maximum duration

- **WHEN** a recording session exceeds the configured maximum duration
- **THEN** the system automatically stops the recording
- **AND** saves the captured audio segment
- **AND** notifies the user of the automatic stop

#### Scenario: Microphone not available

- **WHEN** a user attempts to start recording but no microphone is available
- **THEN** the system returns an error message indicating the microphone is unavailable

---

### Requirement: Unified Input Interface

All input methods SHALL return a consistent `MeetingInputResult` structure.

#### Scenario: Consistent return structure

- **WHEN** any input method completes successfully (audio upload, video upload, or recording)
- **THEN** the system returns a `MeetingInputResult` object
- **AND** the object contains `audio_path` (string, always populated)
- **AND** the object contains `video_path` (string or null, only populated for video uploads)

#### Scenario: File path validation

- **WHEN** a `MeetingInputResult` is returned
- **THEN** all file paths in the result MUST point to existing files
- **AND** paths MUST be absolute or resolvable relative paths
