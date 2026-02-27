# Tasks: MVP Completion

## Iteration 0: Environment & Dependencies (0.5 day)

- [ ] **T0.1** Create `requirements.txt` with all dependencies
  - Include: pytest, openai, anthropic, python-dotenv, pyyaml, rich, tqdm
  - Add installation instructions to README

- [ ] **T0.2** Create `.env.example` template
  - OPENAI_API_KEY placeholder
  - ANTHROPIC_API_KEY placeholder
  - Add to `.gitignore`

- [ ] **T0.3** Verify fresh install works
  - Test: `pip install -r requirements.txt`
  - Test: All imports work without errors

---

## Iteration 1: Core LLM Loop Validation (1 day)

- [ ] **T1.1** Replace OpenAI provider implementation
  - File: `summarizer/llm/openai.py`
  - Use official `openai` SDK
  - Implement retry logic
  - Add timeout handling

- [ ] **T1.2** Update Anthropic provider (if needed)
  - File: `summarizer/llm/anthropic.py`
  - Use official `anthropic` SDK
  - Match OpenAI provider interface

- [ ] **T1.3** Create end-to-end test script
  - File: `test_e2e_real.py`
  - Test with real API key
  - Generate actual summary JSON
  - Verify output structure

- [ ] **T1.4** Run validation test
  - Use a short audio file (< 2 min)
  - Verify `data/summaries/` has output
  - Check JSON is valid
  - Review summary quality

---

## Iteration 2: Transcript Quality Optimization (1.5 days)

- [ ] **T2.1** Create post-processing module
  - File: `asr/postprocess.py`
  - Implement `TranscriptPostProcessor` class
  - Add common error correction dictionary
  - Add proper noun handling

- [ ] **T2.2** Integrate post-processing into ASR pipeline
  - File: `asr/transcribe.py`
  - Add `enable_postprocess` parameter
  - Call postprocess after ASR

- [ ] **T2.3** Add Whisper model configuration
  - Make model size configurable
  - Add model comparison documentation
  - Set default to `small` (balance quality/speed)

- [ ] **T2.4** Create proper nouns configuration
  - File: `data/proper_nouns.yaml`
  - Add common tech terms
  - Add loading function in postprocess.py
  - Document customization

- [ ] **T2.5** Test transcript quality
  - Compare before/after postprocessing
  - Verify proper nouns are corrected
  - Check for common errors fixed

---

## Iteration 3: LLM Prompt & Parsing Optimization (1.5 days)

- [ ] **T3.1** Create enhanced prompt module
  - File: `template/prompt_v2.py`
  - Add angle-specific instructions
  - Add few-shot examples
  - Add format constraints

- [ ] **T3.2** Enhance response parsing
  - File: `summarizer/generate.py`
  - Support multiple heading formats
  - Add fallback strategies
  - Add template-based matching

- [ ] **T3.3** Add parsing tests
  - Test various LLM output formats
  - Test edge cases (empty sections, missing headings)
  - Verify fallback works

- [ ] **T3.4** Compare prompt versions
  - Run same transcript with v1 and v2 prompts
  - Evaluate output quality difference
  - Decide which to use as default

---

## Iteration 4: CLI Entry Point (1 day)

- [ ] **T4.1** Create CLI main module
  - File: `meeting_intelligence/__main__.py`
  - Implement `process` command
  - Implement `template list` command
  - Implement `template show` command

- [ ] **T4.2** Add progress display
  - Integrate `rich` library
  - Show progress for ASR stage
  - Show progress for LLM generation

- [ ] **T4.3** Add error handling
  - File not found errors
  - API key missing errors
  - API failure errors
  - Unsupported format errors

- [ ] **T4.4** Test CLI commands
  - `python -m meeting_intelligence --help`
  - `python -m meeting_intelligence template list`
  - `python -m meeting_intelligence process test.mp3`
  - Verify all options work

---

## Iteration 5: Configuration Management (0.5 day)

- [ ] **T5.1** Create configuration module
  - File: `meeting_intelligence/config.py`
  - Define `Config` dataclass
  - Add YAML save/load

- [ ] **T5.2** Add config init command
  - `python -m meeting_intelligence config init`
  - Create default config file
  - Print helpful message

- [ ] **T5.3** Integrate config into CLI
  - Load config at startup
  - Allow CLI args to override config
  - Support environment variables

- [ ] **T5.4** Document configuration
  - Comment default config.yaml
  - Add configuration section to USAGE.md

---

## Iteration 6: Testing & Documentation (1 day)

- [ ] **T6.1** Add end-to-end tests
  - File: `tests/test_e2e.py`
  - Test with real LLM (skipped if no API key)
  - Test postprocessing
  - Test CLI commands

- [ ] **T6.2** Write user documentation
  - File: `docs/USAGE.md`
  - Installation instructions
  - Configuration guide
  - Usage examples
  - Troubleshooting section

- [ ] **T6.3** Update README
  - Add CLI usage examples
  - Update feature list
  - Add quick start guide

- [ ] **T6.4** Final testing
  - Run full test suite
  - Test with real meeting file
  - Verify all acceptance criteria met

---

## Definition of Done

Each iteration is complete when:
- [ ] All tasks checked off
- [ ] Tests pass
- [ ] Code follows project conventions
- [ ] Relevant documentation updated

## MVP Completion Checklist

- [ ] Can process meeting via CLI
- [ ] Real LLM generates summary
- [ ] Summary JSON is valid
- [ ] 5+ templates work
- [ ] Documentation exists
- [ ] Configuration works
- [ ] Tests cover core paths
- [ ] `data/summaries/` has real outputs
