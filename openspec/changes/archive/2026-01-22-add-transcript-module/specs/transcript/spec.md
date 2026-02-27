## ADDED Requirements

### Requirement: Transcript Document Generation

The system SHALL generate structured transcript documents from ASR results.

#### Scenario: Successful transcript generation from ASR result

- **WHEN** a valid ASR TranscriptionResult is provided
- **THEN** the system generates a TranscriptDocument
- **AND** the document contains all utterances in chronological order
- **AND** each utterance includes start time, end time, and text
- **AND** the document includes metadata (source audio, duration, ASR provider)
- **AND** the document is saved to `data/transcripts/`

#### Scenario: Empty ASR result handling

- **WHEN** an ASR result with no utterances is provided
- **THEN** the system generates an empty transcript document
- **AND** the document contains valid metadata but no content
- **AND** no error is raised

#### Scenario: Invalid ASR result handling

- **WHEN** an invalid ASR result (missing required fields) is provided
- **THEN** the system raises a clear error
- **AND** indicates which field is missing or invalid

---

### Requirement: Transcript Document Structure

The system SHALL provide a consistent transcript document structure.

#### Scenario: Document metadata

- **WHEN** a transcript document is created
- **THEN** it includes the following metadata:
  - `audio_path`: source audio file path
  - `duration`: total audio duration in seconds
  - `asr_provider`: ASR service used (e.g., "whisper-local-base")
  - `created_at`: document creation timestamp
  - `utterance_count`: number of utterances in the transcript

#### Scenario: Document content structure

- **WHEN** a transcript document contains content
- **THEN** the content is organized as an array of utterances
- **AND** each utterance has `start` (seconds), `end` (seconds), and `text`
- **AND** utterances are sorted chronologically by start time
- **AND** timestamps are monotonically increasing

#### Scenario: Document serialization

- **WHEN** a transcript document is serialized to dict/JSON
- **THEN** all fields are properly serialized
- **AND** the output is valid JSON
- **AND** the document can be reconstructed from the serialized form

---

### Requirement: Transcript Document Persistence

The system SHALL save transcript documents to disk for later use.

#### Scenario: Document file creation

- **WHEN** a transcript is successfully built
- **THEN** the system creates a JSON file in `data/transcripts/`
- **AND** the filename includes a timestamp for uniqueness
- **AND** the file contains the complete transcript data

#### Scenario: Document file format

- **WHEN** a transcript document is saved
- **THEN** the JSON file contains:
  - `metadata`: object with document metadata
  - `utterances`: array of {start, end, text} objects
- **AND** the file is valid JSON (parseable)
- **AND** UTF-8 encoding is used for text content

#### Scenario: Document file naming

- **WHEN** multiple transcript documents are created
- **THEN** each has a unique filename based on timestamp
- **AND** filenames follow the pattern: `transcript_YYYYMMDD_HHMMSS.json`
- **AND** no two documents overwrite each other

---

### Requirement: Transcript Document Loading

The system SHALL support loading existing transcript documents.

#### Scenario: Loading existing document

- **WHEN** a valid transcript JSON file is loaded
- **THEN** the system returns a TranscriptDocument object
- **AND** all metadata and content is preserved
- **AND** the document is validated for consistency

#### Scenario: Loading missing file

- **WHEN** a non-existent transcript file is requested
- **THEN** the system raises FileNotFoundError
- **AND** provides a clear error message

#### Scenario: Loading corrupted document

- **WHEN** a malformed or incomplete JSON file is loaded
- **THEN** the system raises a clear error
- **AND** indicates the nature of the corruption (missing field, invalid type)

---

### Requirement: Transcript Export Formats

The system SHALL support exporting transcripts to multiple formats.

#### Scenario: JSON export

- **WHEN** a transcript is exported to JSON
- **THEN** the output is the original saved document format
- **AND** all metadata and utterances are included
- **AND** the output is valid JSON

#### Scenario: Plain text export

- **WHEN** a transcript is exported to plain text (.txt)
- **THEN** the output is human-readable
- **AND** each utterance is on a new line
- **AND** timestamps are shown in `[MM:SS]` format before each utterance
- **AND** metadata is included at the top of the file

#### Scenario: Markdown export

- **WHEN** a transcript is exported to Markdown (.md)
- **THEN** the output is formatted with Markdown syntax
- **AND** metadata is shown as a YAML frontmatter block
- **AND** utterances are formatted as bullet points with timestamps
- **AND** timestamps are clickable links (if supported) or clearly visible

---

### Requirement: ASR to Transcript Integration

The system SHALL support automatic transcript generation after ASR.

#### Scenario: Auto-build transcript enabled

- **WHEN** ASR transcription completes with `auto_build_transcript=True`
- **THEN** the system automatically builds a transcript document
- **AND** the transcript is saved to `data/transcripts/`
- **AND** the transcript path is returned in the result

#### Scenario: Auto-build transcript disabled (default)

- **WHEN** ASR transcription completes with `auto_build_transcript=False` or not specified
- **THEN** the system returns the ASR result only
- **AND** no transcript document is automatically created
- **AND** the user can manually build transcript later
