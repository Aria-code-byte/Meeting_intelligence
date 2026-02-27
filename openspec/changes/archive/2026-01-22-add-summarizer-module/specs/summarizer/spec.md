## ADDED Requirements

### Requirement: Summary Generation

The system SHALL generate structured summaries from transcripts using user templates.

#### Scenario: Successful summary generation

- **WHEN** a valid transcript document and user template are provided
- **THEN** the system generates a structured summary
- **AND** the summary follows the template's section structure
- **AND** each section contains relevant content from the transcript
- **AND** the summary is saved to `data/summaries/`
- **AND** metadata includes source transcript, template used, generation time

#### Scenario: Summary with empty transcript

- **WHEN** a transcript with no utterances is provided
- **THEN** the system generates an empty summary
- **AND** all sections contain placeholder content indicating no transcript available

#### Scenario: Summary generation with LLM error

- **WHEN** the LLM provider returns an error
- **THEN** the system retries with exponential backoff
- **AND** after max retries, returns a clear error
- **AND** preserves the transcript for retry

#### Scenario: Summary with custom template

- **WHEN** a custom user template is provided
- **THEN** the system uses the custom template's structure
- **AND** generates sections according to the template definition
- **AND** respects the template's focus areas and summary angle

---

### Requirement: LLM Provider Abstraction

The system SHALL support multiple LLM providers through a unified interface.

#### Scenario: Default provider (OpenAI)

- **WHEN** no provider is specified
- **THEN** the system uses the OpenAI provider by default
- **AND** uses GPT-4 or GPT-3.5-turbo model based on configuration

#### Scenario: Anthropic provider

- **WHEN** the Anthropic provider is specified
- **THEN** the system uses Claude API
- **AND** supports Claude 3 Opus, Sonnet, Haiku models

#### Scenario: Provider switching

- **WHEN** a different provider is specified
- **THEN** the system uses the specified provider
- **AND** returns results in the same format as other providers

#### Scenario: Provider unavailable fallback

- **WHEN** the primary provider fails
- **THEN** the system attempts fallback to alternative providers (if configured)
- **OR** returns a clear error if no fallback is available

---

### Requirement: Summary Result Structure

The system SHALL provide a consistent summary result structure.

#### Scenario: Summary result metadata

- **WHEN** a summary is generated
- **THEN** it includes the following metadata:
  - `transcript_path`: source transcript file path
  - `template_name`: template used for generation
  - `template_role`: user role from template
  - `llm_provider`: LLM provider used
  - `llm_model`: model name
  - `created_at`: generation timestamp
  - `processing_time`: time taken to generate

#### Scenario: Summary section content

- **WHEN** a summary contains sections
- **THEN** each section includes:
  - `id`: section identifier matching template
  - `title`: section title
  - `content`: generated text content
  - `format`: output format (bullet-points, paragraph, etc.)

#### Scenario: Summary serialization

- **WHEN** a summary is serialized to dict/JSON
- **THEN** all fields are properly serialized
- **AND** the output is valid JSON
- **AND** the summary can be reconstructed from the serialized form

---

### Requirement: Summary Persistence

The system SHALL save summary results to disk for later use.

#### Scenario: Summary file creation

- **WHEN** a summary is successfully generated
- **THEN** the system creates a JSON file in `data/summaries/`
- **AND** the filename includes timestamp and template name
- **AND** the file contains the complete summary data

#### Scenario: Summary file format

- **WHEN** a summary is saved
- **THEN** the JSON file contains:
  - `metadata`: object with all summary metadata
  - `sections`: array of section objects
  - `full_text`: complete summary as plain text
- **AND** the file is valid JSON (parseable)

#### Scenario: Summary file naming

- **WHEN** multiple summaries are created
- **THEN** each has a unique filename based on timestamp and template
- **AND** filenames follow the pattern: `summary_{template}_{timestamp}.json`
- **AND** no two summaries overwrite each other

---

### Requirement: Summary Loading

The system SHALL support loading existing summary documents.

#### Scenario: Loading existing summary

- **WHEN** a valid summary JSON file is loaded
- **THEN** the system returns a SummaryResult object
- **AND** all metadata and content is preserved
- **AND** the document is validated for consistency

#### Scenario: Loading missing file

- **WHEN** a non-existent summary file is requested
- **THEN** the system raises FileNotFoundError
- **AND** provides a clear error message

#### Scenario: Loading corrupted document

- **WHEN** a malformed or incomplete JSON file is loaded
- **THEN** the system raises a clear error
- **AND** indicates the nature of the corruption

---

### Requirement: Summary Export Formats

The system SHALL support exporting summaries to multiple formats.

#### Scenario: JSON export

- **WHEN** a summary is exported to JSON
- **THEN** the output is the original saved document format
- **AND** all metadata and sections are included
- **AND** the output is valid JSON

#### Scenario: Plain text export

- **WHEN** a summary is exported to plain text (.txt)
- **THEN** the output is human-readable
- **AND** each section is clearly separated
- **AND** metadata is included at the top

#### Scenario: Markdown export

- **WHEN** a summary is exported to Markdown (.md)
- **THEN** the output is formatted with Markdown syntax
- **AND** sections use Markdown headers (##, ###)
- **AND** bullet points are properly formatted

---

### Requirement: End-to-End Pipeline

The system SHALL provide a complete pipeline from audio/video to summary.

#### Scenario: Audio to summary pipeline

- **WHEN** an audio file is provided with a template
- **THEN** the system:
  1. Validates the audio file
  2. Transcribes to transcript (ASR)
  3. Builds transcript document
  4. Generates summary using template
  5. Returns the final summary

#### Scenario: Video to summary pipeline

- **WHEN** a video file is provided with a template
- **THEN** the system:
  1. Extracts audio from video
  2. Transcribes to transcript (ASR)
  3. Builds transcript document
  4. Generates summary using template
  5. Returns the final summary

#### Scenario: Pipeline progress tracking

- **WHEN** a pipeline function is called with a progress callback
- **THEN** the system reports progress at each stage
- **AND** includes stage name and completion percentage
