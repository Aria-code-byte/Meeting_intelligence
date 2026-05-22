# ASR 语音识别集成指南

**更新日期**: 2026-05-13
**版本**: v1.0

---

## 📋 当前状态

### ✅ 已实现
1. 真实 ASR 转录功能已接入（Whisper）
2. 智能fallback：未安装Whisper时使用mock
3. 支持中英文语音识别
4. 自动后处理（提高识别准确率）
5. 时间戳和发言人分离

### ⚠️ 依赖要求
需要安装 Whisper 才能使用真实 ASR

---

## 🔧 ASR 配置

### 安装 Whisper

#### 方式1：基础安装（推荐）
```bash
pip install openai-whisper
```

#### 方式2：国内镜像加速
```bash
pip install openai-whisper -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 下载 Whisper 模型

#### 自动下载（首次使用时）
首次运行时会自动下载模型到 `~/.cache/whisper/`

#### 手动下载（推荐国内用户）
```bash
# 使用镜像站下载
python scripts/download_whisper_model.py base --mirror

# 或手动下载后放到 data/models/whisper/ 目录
```

**模型选择**：
- `tiny` - 最快，准确率较低（~1GB RAM）
- `base` - 推荐（~1GB RAM）
- `small` - 平衡（~2GB RAM）
- `medium` - 更准确（~5GB RAM）
- `large` - 最准确（~10GB RAM）

---

## 🚀 启动方式

### 未安装 Whisper（Mock 模式）
```bash
# 直接启动，会自动使用 mock 转录
python backend/main.py
```

**后端日志**：
```
[BACKEND] whisper not available, using mock transcription
[BACKEND] using mock transcription (no real ASR)
```

### 已安装 Whisper（真实 ASR）
```bash
# 确认whisper已安装
python -c "import whisper; print(whisper.__version__)"

# 启动后端
python backend/main.py
```

**后端日志**：
```
[BACKEND] whisper available, will use real ASR
[BACKEND] using real ASR for transcription
[BACKEND] calling ASR API...
[BACKEND] transcription completed: 45 segments
[BACKEND] transcription task completed
```

---

## 📊 工作流程

### 完整流程

```
1. 用户上传音频文件
   ↓
2. 后端保存文件到 uploads/
   ↓
3. 用户点击"开始转录"
   ↓
4. 后端检查 Whisper 是否可用
   ├─ 可用 → 使用真实 ASR
   └─ 不可用 → 使用 Mock 转录
   ↓
5. 转录完成后保存文字稿
   ↓
6. 用户选择模板生成总结
   ↓
7. LLM 根据实际文字稿生成总结
```

### 关键代码路径

**上传**（backend/main.py 第529-589行）：
```python
@app.post("/api/upload")
async def upload_meeting_file(file: UploadFile = File(...)):
    # 保存文件
    file_path = UPLOAD_DIR / f"{meeting_id}_{file.filename}"

    # 存储会议信息（包含 audio_path）
    MEETINGS[meeting_id] = {
        "audio_path": str(file_path),  # 供ASR使用
        ...
    }
```

**转录**（backend/main.py 第596-665行）：
```python
@app.post("/api/meetings/{meeting_id}/transcribe")
async def start_transcription(meeting_id: str):
    audio_path = MEETINGS[meeting_id].get("audio_path", "")

    # 检查whisper是否可用
    try:
        import whisper
        use_real_asr = True
    except ImportError:
        use_real_asr = False

    # 选择真实ASR或Mock
    if use_real_asr:
        target_func = real_transcription_task
    else:
        target_func = simulate_transcription_task
```

**真实ASR**（backend/main.py 第118-180行）：
```python
def real_transcription_task(meeting_id: str, task_id: str, audio_path: str):
    # 调用ASR API
    result = transcribe(
        audio_path=audio_path,
        provider="whisper",
        language="zh",
        model_size="base"
    )

    # 格式化转录结果
    for utterance in result.utterances:
        transcript_lines.append(f"[{time_str}] {speaker}：{text}")

    # 保存到会议记录
    MEETINGS[meeting_id]["transcript"] = full_transcript
```

---

## 🔍 日志验证

### Mock 转录日志
```
[BACKEND] transcription called: meeting_id=xxx
[BACKEND] audio_path: uploads/xxx_meeting.mp3
[BACKEND] whisper not available, using mock transcription
[BACKEND] using mock transcription (no real ASR)
[BACKEND] transcription completed (mock): 7 segments
```

**特点**：所有会议的转录内容相同

### 真实 ASR 转录日志
```
[BACKEND] transcription called: meeting_id=xxx
[BACKEND] audio_path: uploads/xxx_meeting.mp3
[BACKEND] whisper available, will use real ASR
[BACKEND] using real ASR for transcription
[BACKEND] calling ASR API...
[BACKEND] transcription completed: 45 segments
[BACKEND] transcription task completed
```

**特点**：不同音频文件转录内容不同

---

## ✅ 验收标准

### 1. 转录真实性
**测试方法**：上传不同的音频文件
- ✅ 不同音频应得到不同转录内容
- ✅ 转录内容应反映音频实际内容
- ❌ 如果所有音频转录都一样，说明仍是mock

### 2. 中文识别准确率
**测试方法**：上传中文会议录音
- ✅ 应能正确识别中文内容
- ✅ 专业术语识别准确率 > 80%
- ✅ 时间戳准确

### 3. 总结内容差异
**测试方法**：不同音频 → 转录 → 总结
- ✅ 不同音频的总结应明显不同
- ✅ 总结应基于实际转录内容
- ❌ 如果总结内容固定，说明链路未打通

---

## 🛠️ 故障排除

### 问题1：转录内容固定不变
**原因**：仍在使用 mock 转录
**解决**：
1. 检查是否安装了 Whisper：`python -c "import whisper"`
2. 查看后端日志是否有 `[BACKEND] using mock transcription`
3. 如果未安装，运行：`pip install openai-whisper`

### 问题2：Whisper 导入失败
**原因**：Whisper 未安装或路径问题
**解决**：
```bash
# 重新安装
pip uninstall openai-whisper
pip install openai-whisper

# 验证安装
python -c "import whisper; print(whisper.__version__)"
```

### 问题3：转录失败
**原因**：音频格式不支持或文件损坏
**解决**：
1. 检查音频格式（支持：mp3, wav, mp4, m4a, webm）
2. 确认文件可以正常播放
3. 查看后端详细错误信息

### 问题4：转录速度慢
**原因**：使用了大模型或硬件性能不足
**解决**：
1. 使用更小的模型（`base` 或 `tiny`）
2. 如果有GPU，Whisper会自动使用
3. 考虑使用 faster-whisper（更快）

---

## 📊 性能对比

### Whisper 模型性能

| 模型 | 速度 | 准确率 | 内存 | 推荐场景 |
|------|------|--------|------|----------|
| tiny | 最快 | 较低 | ~1GB | 快速测试 |
| base | 快 | 良好 | ~1GB | **推荐默认** |
| small | 中等 | 很好 | ~2GB | 生产环境 |
| medium | 慢 | 优秀 | ~5GB | 高准确率要求 |
| large | 最慢 | 最佳 | ~10GB | 最佳质量 |

### 预期处理时间

以 `base` 模型为例：
- 1分钟音频：约 10-15 秒
- 10分钟音频：约 1-2 分钟
- 1小时音频：约 5-10 分钟

---

## 💡 使用建议

### 开发测试
- 使用 `tiny` 或 `base` 模型
- 上传短音频（1-3分钟）
- 快速验证功能

### 生产环境
- 使用 `base` 或 `small` 模型
- 考虑使用 faster-whisper（更快）
- 确保有足够内存和CPU

### GPU 加速
如果有NVIDIA GPU：
```bash
# 安装CUDA版本的Whisper
pip install openai-whisper
# Whisper会自动检测并使用GPU
```

---

## 📖 相关文档

- `LLM_INTEGRATION_GUIDE.md` - LLM总结集成指南
- `asr/transcribe.py` - ASR转录模块
- `asr/providers/whisper.py` - Whisper提供商
- `scripts/download_whisper_model.py` - 模型下载脚本

---

## 🎯 总结

### 当前状态
- **转录流程**：✅ 已打通
- **转录内容**：✅ 已接入真实ASR（安装Whisper时）
- **智能fallback**：✅ 未安装时使用mock
- **日志验证**：✅ 已添加

### 使用方式
1. 安装 Whisper：`pip install openai-whisper`
2. 启动服务：`python backend/main.py`
3. 上传音频文件
4. 开始转录
5. 查看后端日志确认使用真实ASR
6. 验证转录内容基于实际音频

---

**创建时间**: 2026-05-13
**版本**: v1.0
**状态**: ✅ 已完成并测试
