# Project Context

## Purpose

**AI Meeting Assistant V1** - A standalone intelligent module that converts meetings into structured records with role-perspective summaries.

**Core Value Proposition**: Transform meetings into *complete original records + role-perspective summaries*, solving the problem of "no time to attend / can't finish listening / summary doesn't match my needs."

**Product Positioning**: Not just "helping you remember meetings," but "making meetings happen again from your role's perspective."

**Long-term Vision**: This will serve as a persistent sub-module/intelligent module within an "AI Super Personal Assistant" ecosystem. It must be standalone, callable, and UI-agnostic.

## Tech Stack

**Backend/Core**:
- Python 3.10+
- FFmpeg for audio extraction
- ASR service (provider TBD - Whisper, Google Speech-to-Text, or similar)

**LLM/AI**:
- LLM API for template-based summarization (OpenAI, Anthropic, or local models)

**Storage**:
- File-based persistence for all intermediate data
- Structured directories: `data/raw_audio/`, `data/transcripts/`, `data/summaries/`

**Frontend/UI**:
- Academic + Business style
- Dark theme: deep gray/graphite backgrounds
- Accent colors: dark purple/indigo/deep teal
- Card-based layout with generous whitespace

**Formats Supported**:
- Video: mp4, mkv, mov
- Audio: mp3, wav, m4a

## Project Conventions

### Code Style

**Naming Conventions**:
- Files: `snake_case.py` (e.g., `upload_video.py`, `build_transcript.py`)
- Functions: `snake_case` (e.g., `extract_audio()`, `transcribe()`)
- Classes: `PascalCase` (e.g., `MeetingInputResult`, `ProcessedAudio`)
- Constants: `UPPER_SNAKE_CASE`

**Module Structure**:
- Each module must be independently testable
- Clear interfaces between modules (no cross-dependencies)
- All intermediate results MUST be persisted to disk

**Documentation**:
- Chinese comments for business logic
- English for technical implementation details
- Docstrings for all public interfaces

### Architecture Patterns

**Core Principles**:
1. **Modular Independence**: Each module can run standalone
2. **Interface-First**: Modules communicate through defined interfaces
3. **Data Persistence**: All intermediate data saved to disk
4. **V2 Preparation**: Interfaces reserved for future features, not implemented

**Data Flow**:
```
Input → Audio Extraction → ASR → Raw Transcript → Template Engine → Summary
```

**Module Categories**:
- `input/` - Meeting acquisition (upload/record)
- `audio/` - Audio processing
- `asr/` - Speech-to-text conversion
- `transcript/` - Raw document generation
- `template/` - User template system
- `summarizer/` - LLM summarization engine
- `future/` - V2 feature placeholders (video analysis, PPT extraction)

### Testing Strategy

**Test Coverage Requirements**:
- Unit tests for each module
- Integration tests for data flow
- Edge case handling (long files, empty inputs, format variations)

**Test Points Per Module**:
- **Input**: File upload limits, path validation, format consistency
- **Audio**: Format conversion accuracy, duration correctness
- **ASR**: Timestamp monotonicity, text completeness, long meeting handling
- **Transcript**: Content completeness, time information preservation
- **Template**: Empty template handling, default template loading
- **Summarizer**: Output differentiation by template, core discussion coverage

### Git Workflow

**Branching Strategy**:
- `main` - Stable, production-ready code
- `develop` - Integration branch for features
- `feature/<name>` - Feature development
- `fix/<name>` - Bug fixes

**Commit Conventions**:
- Use OpenSpec change proposals for significant features
- Commit format: `[type] brief description`
- Types: `feat`, `fix`, `refactor`, `test`, `docs`

## Domain Context

**Core Concepts**:

1. **Raw Transcript (原始会议文档)**: The "meeting body" - complete, unmodified, structured record with timestamps. Not a summary, but the meeting itself.

2. **Template (模板)**: The product's "soul module" - defines how the meeting is re-experienced:
   - **Role (角色定位)**: Who is the user? Determines what information is important
   - **Angle (总结角度)**:偏向结论/偏向过程/偏向决策
   - **Focus (重点关注内容)**: What to watch for

3. **Structured Summary (结构化总结)**: LLM-generated output based on the raw transcript and user template. Structure is model-generated, not hardcoded.

**V1 Scope Boundary**:
- **In Scope**: Audio/video input, ASR with timestamps, raw transcript, template-based summaries
- **Out of Scope (V2)**: PPT detection, screenshot capture, slide alignment, vector knowledge base

## Important Constraints

**Technical Constraints**:
- Must be standalone runnable
- Must have clear, reusable interfaces
- Must not depend on specific UI form
- Must assume future integration with other systems

**Development Constraints**:
- Implement in phases - do not build all features at once
- Prioritize data flow stability over intelligence optimization
- Prioritize engineering correctness over feature completeness
- All intermediate data must be traceable

**Design Constraints**:
- Avoid over-engineering - default to <100 lines of new code
- Single-file implementations until proven insufficient
- Choose boring, proven patterns

## External Dependencies

**Audio Processing**:
- FFmpeg (for audio extraction from video)
- Audio preprocessing libraries

**ASR Service**:
- Speech-to-text API with timestamp support
- Must return: `{start, end, text}` per utterance

**LLM API**:
- For template-based summarization
- Must handle Chinese language input/output

**Future (V2) Reserved**:
- Video analysis APIs (for PPT detection)
- OCR services (for slide text extraction)

## Data Directory Structure

```
data/
├── raw_audio/      # Extracted/uploaded audio files
├── transcripts/    # Raw meeting transcript documents
└── summaries/      # Template-based summary outputs
```

## V2 Feature Interfaces (Reserved, Not Implemented)

```python
# Video analysis placeholder
def analyze_video(video_path):
    pass

# PPT extraction placeholder
def extract_ppt_slides(video_path):
    pass

# Slide-transcript alignment placeholder
def align_slide_with_transcript(slides, transcript):
    pass
```
