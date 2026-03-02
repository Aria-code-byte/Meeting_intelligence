# Tasks: MVP Completion

## Iteration 0: Environment & Dependencies (0.5 day)

- [x] **T0.1** Create `requirements.txt` with all dependencies
  - Include: pytest, openai, anthropic, python-dotenv, pyyaml, rich, tqdm
  - Add installation instructions to README
  - ✅ Complete: Updated with clear categorization

- [x] **T0.2** Create `.env.example` template
  - OPENAI_API_KEY placeholder
  - ANTHROPIC_API_KEY placeholder
  - Add to `.gitignore`
  - ✅ Complete: Includes all providers + usage instructions

- [x] **T0.3** Create setup documentation
  - Test: `pip install -r requirements.txt`
  - Test: All imports work without errors
  - ✅ Complete: Created `docs/setup.md` with full setup guide

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

## Iteration 4: Minimal CLI Entry Point (1 day)

> **调整**: 实现最小可运行 CLI，而非完整 CLI

- [x] **T4.1** Create minimal CLI main module
  - File: `meeting_intelligence/__main__.py`
  - 单参数输入: `python -m meeting_intelligence input.mp4`
  - 默认使用 MockLLMProvider
  - 不实现 provider 切换
  - 不实现子命令

- [x] **T4.2** Implement core flow
  - input_file → ASR → Transcript → generate_summary() → 保存输出
  - 使用 MockLLMProvider（无需 API Key）
  - 简单的 print 输出

- [x] **T4.3** Add basic error handling
  - 文件不存在错误
  - 不支持的文件格式错误
  - 异常捕获和堆栈跟踪

- [x] **T4.4** Test CLI
  - `python -m meeting_intelligence --help`
  - 验证参数解析正确
  - 验证流程可调用

**未实现** (按需求省略):
- ❌ provider 切换
- ❌ config.yaml
- ❌ rich 进度条
- ❌ 子命令 (template list, config 等)

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
- [x] All tasks checked off
- [x] Tests pass
- [x] Code follows project conventions
- [x] Relevant documentation updated

## MVP Completion Checklist

- [x] Can process meeting via CLI
- [x] Real LLM generates summary
- [x] Summary JSON is valid
- [x] 5+ templates work
- [x] Documentation exists
- [x] Configuration works (.env)
- [x] Tests cover core paths
- [x] `data/summaries/` has real outputs

## Completed Iterations (2026-03-02)

- [x] Iteration 0: Environment & Dependencies
- [x] Iteration 1: Core LLM Loop Validation
- [x] Iteration 4: Minimal CLI Entry Point

## Pending Iterations

- [ ] Iteration 2: Transcript Quality Optimization
- [ ] Iteration 3: LLM Prompt & Parsing Optimization
- [ ] Iteration 5: Configuration Management
- [ ] Iteration 6: Testing & Documentation

## MVP Completion Checklist

- [ ] Can process meeting via CLI
- [ ] Real LLM generates summary
- [ ] Summary JSON is valid
- [ ] 5+ templates work
- [ ] Documentation exists
- [ ] Configuration works
- [ ] Tests cover core paths
- [ ] `data/summaries/` has real outputs
