# Spec: MVP Completion

## Overview

Complete the AI Meeting Assistant V1 MVP by validating the core end-to-end loop and providing user-accessible interfaces.

## Requirements

### REQ-1: Real LLM Integration

The system must generate summaries using real LLM APIs (OpenAI or Anthropic), not mock implementations.

**Acceptance Criteria**:
- [ ] OpenAI SDK implementation replaces curl-based approach
- [ ] Anthropic SDK implementation follows same pattern
- [ ] API calls include proper error handling and retry logic
- [ ] `data/summaries/` directory contains valid JSON outputs
- [ ] Summary structure matches template definition

### REQ-2: Transcript Quality Improvement

The system must improve ASR transcript quality before sending to LLM.

**Acceptance Criteria**:
- [ ] Post-processing module corrects common ASR errors
- [ ] Proper noun dictionary is configurable via YAML
- [ ] Whisper model size is configurable
- [ ] At least 20 common error patterns are corrected
- [ ] Custom vocabulary can be added without code changes

### REQ-3: Robust LLM Response Parsing

The system must reliably parse LLM responses even when format varies.

**Acceptance Criteria**:
- [ ] Supports multiple heading formats (##, ###, **bold**, 1.)
- [ ] Has fallback parsing when primary method fails
- [ ] Never crashes due to unexpected LLM output
- [ ] Template-based matching for section identification
- [ ] Graceful degradation with useful error messages

### REQ-4: Command-Line Interface

The system must be usable via CLI without writing Python code.

**Acceptance Criteria**:
- [ ] `python -m meeting_intelligence process <file>` works
- [ ] `--template` option selects template
- [ ] `--model` option selects LLM model
- [ ] `python -m meeting_intelligence template list` works
- [ ] `python -m meeting_intelligence template show <name>` works
- [ ] Progress feedback during processing
- [ ] Clear error messages for common issues

### REQ-5: Configuration Management

The system must support configuration files for user customization.

**Acceptance Criteria**:
- [ ] `config.yaml` file with all settings
- [ ] `config init` command creates default config
- [ ] Environment variables override config file
- [ ] LLM provider and model are configurable
- [ ] ASR model size is configurable
- [ ] Output directory is configurable

### REQ-6: Dependency Management

The project must have standardized dependency management.

**Acceptance Criteria**:
- [ ] `requirements.txt` with all dependencies
- [ ] `.env.example` template for API keys
- [ ] Installation instructions in README
- [ ] No missing dependencies after fresh install

## Non-Functional Requirements

### NFR-1: Performance
- End-to-end processing for 1-hour meeting should complete in < 10 minutes (excluding ASR time)

### NFR-2: Reliability
- System should not crash on unexpected LLM output
- API failures should have clear error messages

### NFR-3: Usability
- CLI should show progress for long-running operations
- Error messages should be actionable

### NFR-4: Maintainability
- All new code should have corresponding tests
- Configuration should be documented

## API Changes

### CLI API

```bash
# Process a meeting file
python -m meeting_intelligence process <input> [options]

# Template management
python -m meeting_intelligence template list
python -m meeting_intelligence template show <name>

# Configuration
python -m meeting_intelligence config init
```

### Configuration API

```python
# Load configuration
from meeting_intelligence.config import get_config
config = get_config()

# Access settings
llm_model = config.llm.model
asr_size = config.asr.model_size
```

## File Structure

```
meeting_intelligence/
├── __main__.py              # CLI entry point (NEW)
├── config.py                # Configuration module (NEW)
├── requirements.txt         # Dependencies (NEW)
├── .env.example            # Environment template (NEW)
├── asr/
│   ├── postprocess.py      # Post-processing module (NEW)
│   └── transcribe.py       # Modified to integrate postprocess
├── summarizer/
│   ├── llm/
│   │   └── openai.py       # Modified to use SDK
│   └── generate.py         # Enhanced parsing logic
├── template/
│   └── prompt_v2.py        # Enhanced prompts (NEW)
├── data/
│   └── proper_nouns.yaml   # Custom vocabulary (NEW)
└── docs/
    └── USAGE.md            # User documentation (NEW)
```

## Testing Strategy

### Unit Tests
- Post-processing corrections
- LLM response parsing variations
- Configuration loading

### Integration Tests
- End-to-end with real LLM API (requires API key)
- CLI command execution
- Configuration override behavior

### Manual Testing
- Process a variety of meeting lengths
- Test with different templates
- Verify output JSON structure

## Rollout Plan

1. **Phase 1** (Days 1-2): Environment + LLM validation
   - Setup dependencies
   - Verify real LLM integration works

2. **Phase 2** (Days 3-4): Quality improvements
   - Transcript post-processing
   - Prompt optimization

3. **Phase 3** (Days 5-6): User-facing features
   - CLI implementation
   - Configuration management

4. **Phase 4** (Day 7): Documentation and testing
   - User docs
   - Final testing

## Backwards Compatibility

- All existing module interfaces remain unchanged
- New features are additive
- Default behavior preserved when config is absent
