# Change: MVP Completion - End-to-End Validation

## Why

The AI Meeting Assistant V1 has completed its core module development (input, audio processing, ASR, transcript, template system), but the **most critical value proposition has not been validated**:

1. **Real LLM summary generation has never been tested** - only Mock implementations exist
2. **No end-to-end execution record** - `data/summaries/` directory is empty
3. **No user-accessible entry point** - code can only be called by other Python code
4. **Transcript quality issues** - ASR errors affect summary quality
5. **Fragile LLM response parsing** - relies on simple markdown heading splitting

Without validating the core loop (real meeting → real LLM → structured summary), we have a beautiful skeleton but no heartbeat.

## What Changes

### Iteration 0: Environment & Dependencies (0.5 day)
- **ADDED**: `requirements.txt` with all dependencies
- **ADDED**: `.env.example` template for API key configuration
- **ADDED**: Environment variable loading support

### Iteration 1: Core LLM Loop Validation (1 day)
- **MODIFIED**: `summarizer/llm/openai.py` - Replace curl-based implementation with official OpenAI SDK
- **ADDED**: Real LLM API integration tests
- **ADDED**: End-to-end validation script `test_e2e_real.py`

### Iteration 2: Transcript Quality Optimization (1.5 days)
- **ADDED**: `asr/postprocess.py` - Post-processing correction module
- **MODIFIED**: `asr/transcribe.py` - Integrate post-processing into pipeline
- **ADDED**: Configurable Whisper model sizes (tiny/base/small/medium/large)
- **ADDED**: `data/proper_nouns.yaml` - Custom vocabulary configuration

### Iteration 3: LLM Prompt & Parsing Optimization (1.5 days)
- **ADDED**: `template/prompt_v2.py` - Enhanced prompt engineering
  - Few-shot examples
  - Structured output instructions
  - Format constraints
- **MODIFIED**: `summarizer/generate.py` - Robust response parsing
  - Support multiple heading formats
  - Fallback parsing strategies
  - Template-based matching

### Iteration 4: CLI Entry Point (1 day)
- **ADDED**: `meeting_intelligence/__main__.py` - Main CLI module
  - `process` command - Process audio/video files
  - `template list` command - List available templates
  - `template show` command - Show template details
- **ADDED**: Progress display with `rich` library
- **ADDED**: Error handling and user-friendly messages

### Iteration 5: Configuration Management (0.5 day)
- **ADDED**: `meeting_intelligence/config.py` - Configuration module
- **ADDED**: `config.yaml` support for user settings
- **ADDED**: `config init` command for initialization

### Iteration 6: Testing & Documentation (1 day)
- **ADDED**: `tests/test_e2e.py` - End-to-end integration tests
- **ADDED**: `docs/USAGE.md` - User documentation
- **UPDATED**: `README.md` with usage examples

## Impact

- **Affected specs**: New capability `mvp-validation`, `cli-interface`, `config-management`
- **Affected code**:
  - Creates: `meeting_intelligence/__main__.py`, `meeting_intelligence/config.py`, `asr/postprocess.py`, `template/prompt_v2.py`
  - Modifies: `summarizer/llm/openai.py`, `summarizer/generate.py`, `asr/transcribe.py`
  - Adds: `requirements.txt`, `.env.example`, `docs/USAGE.md`
- **Dependencies**: OpenAI/Anthropic SDKs, `rich` for CLI, `pyyaml` for config

## Key Design Decisions

1. **Validate Core Value First**: Prioritize running real LLM over adding new features
2. **File-Based Configuration**: Simple YAML config instead of database (can migrate later if needed)
3. **CLI Before UI**: Command-line interface is sufficient for MVP; Web UI is a distraction
4. **SDK Over Curl**: Use official OpenAI/Anthropic SDKs for reliability and retry logic
5. **Progressive Enhancement**: Start with simple prompts, optimize based on real results

## Success Criteria

MVP is complete when:
1. ✅ User can process a meeting file via CLI
2. ✅ Real LLM generates structured summary
3. ✅ Output JSON summary file is valid
4. ✅ At least 5 role templates work correctly
5. ✅ Basic user documentation exists
6. ✅ Configuration file support works
7. ✅ Core functions have test coverage

## Estimated Timeline

7 days total (assuming single developer, part-time)

| Iteration | Duration | Priority |
|-----------|----------|----------|
| 0: Environment | 0.5 day | P0 |
| 1: LLM Validation | 1 day | P0 |
| 2: Transcript Opt | 1.5 days | P0 |
| 3: Prompt Opt | 1.5 days | P1 |
| 4: CLI | 1 day | P1 |
| 5: Config | 0.5 day | P2 |
| 6: Test & Docs | 1 day | P2 |

## Out of Scope (Explicitly NOT doing)

- ❌ Web UI / Frontend interface
- ❌ Database migration (file storage is sufficient)
- ❌ Concurrent processing / task queues
- ❌ V2 features (PPT detection, video analysis)
- ❌ Real-time streaming processing
