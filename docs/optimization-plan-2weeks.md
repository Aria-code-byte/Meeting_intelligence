# AI Meeting Assistant - 两周优化计划

> 目标：将项目优化为开包即用的软件，并添加发言人识别功能
> 时间周期：2周（14天）
> 制定日期：2026-05-08

---

## 📋 项目现状分析

### 已有优势
- ✅ 完整的 ASR 转录模块（Whisper + faster-whisper）
- ✅ LLM 增强和总结功能
- ✅ CLI 和 Web 两种交互模式
- ✅ 模板系统和多 LLM Provider 支持
- ✅ 454 个测试用例覆盖

### 当前痛点
- ❌ 需要手动安装 FFmpeg
- ❌ 需要手动配置环境变量（API Keys）
- ❌ Whisper 模型需要下载
- ❌ 缺少发言人识别功能
- ❌ 没有打包安装方案
- ❌ 缺少内置配置向导

---

## 🎯 优化目标

### 核心目标
1. **开包即用**：用户下载后即可使用，最小化配置步骤
2. **发言人识别**：在转录过程中自动识别和区分不同发言人
3. **一键安装**：提供图形化/命令行安装程序

### 用户体验目标
- 首次使用时间 < 5分钟（包含下载）
- 配置步骤 ≤ 3步
- 无需查看文档即可完成基本操作

---

## 📅 两周详细计划

### 第一周：基础优化 + 安装程序

#### Day 1-2：安装程序开发

**任务清单：**
- [ ] 创建安装脚本 `install.sh` / `install.bat`
- [ ] 创建 Python 打包配置 (`pyproject.toml`)
- [ ] 创建安装向导 CLI (`setup_wizard.py`)
- [ ] 添加依赖检查和自动安装

**技术方案：**
```bash
# 安装脚本功能
1. 检查 Python 版本 (>= 3.10)
2. 自动创建虚拟环境
3. 安装 Python 依赖
4. 下载 Whisper 模型
5. 检测/安装 FFmpeg
6. 启动配置向导
```

**文件结构：**
```
/installer/
├── install.sh          # Linux/macOS 安装脚本
├── install.bat         # Windows 安装脚本
├── setup_wizard.py     # 交互式配置向导
└── check_deps.py       # 依赖检查工具
```

---

#### Day 3-4：配置管理系统重构

**任务清单：**
- [ ] 统一配置管理模块 (`config_manager.py`)
- [ ] 支持多配置文件优先级
- [ ] 添加配置验证
- [ ] 创建默认配置模板

**配置优先级：**
```
命令行参数 > 环境变量 > 用户配置 > 默认配置
```

**新增配置项：**
```yaml
# config.yaml
system:
  auto_download_models: true
  model_cache_dir: ./data/models
  first_run: true

asr:
  provider: faster-whisper
  model: base
  device: auto  # auto/cpu/cuda
  speaker_diarization: true  # 新增

llm:
  provider: deepseek  # 默认国产，网络友好
  model: glm-4-flash
  timeout: 60
```

---

#### Day 5-7：发言人识别模块集成

**任务清单：**
- [ ] 集成 pyannote.audio（Speaker Diarization）
- [ ] 实现 Speaker 嵌入到 Utterance 结构
- [ ] 添加发言人聚类和命名
- [ ] UI 显示发言人标签

**技术选型：**
```python
# 推荐方案：pyannote.audio
优点：
- 成熟稳定的开源方案
- 与 Whisper 配合良好
- 支持预训练模型

替代方案：SpeechRecognition + pyannote
```

**数据结构扩展：**
```python
@dataclass
class Utterance:
    start: float
    end: float
    text: str
    speaker: Optional[str] = None  # 新增
    speaker_confidence: float = 0.0  # 新增
```

**输出格式示例：**
```markdown
## 会议转录

[00:00 - 00:15] **发言人 A**: 大家好，今天我们讨论项目进度

[00:16 - 00:45] **发言人 B**: 我先汇报一下，目前前端开发已经完成了 80%

[00:46 - 01:10] **发言人 A**: 很好，那后端接口什么时候能对接完成？
```

---

### 第二周：产品化 + 用户体验

#### Day 8-9：一键启动脚本

**任务清单：**
- [ ] 创建跨平台启动脚本
- [ ] 添加系统托盘图标（可选）
- [ ] 创建桌面快捷方式生成器
- [ ] 添加自动更新检查

**启动脚本功能：**
```bash
# run.sh / run.bat
1. 检查环境（是否首次运行）
2. 加载配置
3. 检查依赖完整性
4. 启动 CLI/Web 界面
```

---

#### Day 10-11：UI 优化 + 发言人管理

**任务清单：**
- [ ] CLI 中添加发言人编辑功能
- [ ] Web UI 显示发言人统计
- [ ] 支持发言人自定义命名
- [ ] 添加发言时长时间统计

**CLI 新增菜单：**
```
请选择操作：
  1. 上传音视频文件
  2. 生成文字稿（含发言人识别）
  3. 生成会议总结
  4. 发言人管理  # 新增
  5. 模板管理
  6. 退出
```

**发言人管理功能：**
- 查看所有发言人和统计信息
- 重命名发言人（Speaker 1 → 张三）
- 合并发言人（同一人的不同片段）
- 按发言人筛选内容

---

#### Day 12-13：打包分发

**任务清单：**
- [ ] PyPI 打包配置
- [ ] 创建 standalone 可执行文件（PyInstaller）
- [ ] 编写用户文档（快速开始指南）
- [ ] 创建示例视频和配置

**打包方案：**
```
方案 1: pip install (推荐开发者)
- 灵活更新
- 适合 Python 用户

方案 2: PyInstaller (推荐普通用户)
- 无需 Python 环境
- 双击运行
- 包含所有依赖

方案 3: Docker (推荐服务器部署)
- 环境隔离
- 一键部署
```

---

#### Day 14：测试 + 文档完善

**任务清单：**
- [ ] 端到端测试（全新环境）
- [ ] 性能测试（转录速度）
- [ ] 用户测试（找 3-5 人试用）
- [ ] 完善文档和 FAQ

**测试清单：**
- [ ] Windows 10/11 安装测试
- [ ] macOS 安装测试
- [ ] Linux (Ubuntu) 安装测试
- [ ] 发言人识别准确率测试
- [ ] 内存和 CPU 占用测试

---

## 📦 交付物清单

### 核心文件
```
Meeting-Intelligence/
├── installer/
│   ├── install.sh
│   ├── install.bat
│   └── setup_wizard.py
├── meeting_intelligence/
│   ├── speaker/              # 新增：发言人识别模块
│   │   ├── diarization.py
│   │   ├── clustering.py
│   │   └── ui.py
│   └── config_manager.py     # 新增：统一配置管理
├── run.sh                    # 新增：Linux/macOS 启动脚本
├── run.bat                   # 新增：Windows 启动脚本
├── pyproject.toml           # 新增：Python 打包配置
├── QUICKSTART.md            # 新增：5分钟快速开始指南
└── CHANGELOG.md             # 更新日志
```

### 文档
- [ ] 快速开始指南 (QUICKSTART.md)
- [ ] 安装教程 (docs/installation.md)
- [ ] 发言人识别说明 (docs/speaker-diarization.md)
- [ ] FAQ 常见问题
- [ ] 更新日志 (CHANGELOG.md)

---

## 🔧 技术实现细节

### 发言人识别模块架构

```python
# speaker/diarization.py
class SpeakerDiarization:
    def __init__(self, model_name="pyannote/speaker-diarization-3.1"):
        self.pipeline = Pipeline.from_pretrained(model_name)

    def process(self, audio_path: str) -> List[SpeakerSegment]:
        """执行发言人分离"""
        diarization = self.pipeline(audio_path)
        return self._convert_to_segments(diarization)

    def align_with_transcript(
        self,
        speaker_segments: List[SpeakerSegment],
        utterances: List[Utterance]
    ) -> List[Utterance]:
        """对齐发言人和转录结果"""
        # 使用时间窗口匹配算法
        return aligned_utterances
```

### 安装向导流程

```python
# installer/setup_wizard.py
class SetupWizard:
    def run(self):
        # Step 1: 欢迎
        self.show_welcome()

        # Step 2: 选择 LLM Provider
        provider = self.select_llm_provider()

        # Step 3: 输入 API Key（可选）
        api_key = self.input_api_key(provider)

        # Step 4: 下载模型
        self.download_models()

        # Step 5: 完成
        self.show_completion()
```

---

## 📊 关键指标

### 性能目标
| 指标 | 当前 | 目标 |
|-----|-----|-----|
| 安装时间 | - | < 5分钟 |
| 首次配置步骤 | - | ≤ 3步 |
| 转录速度（1小时音频） | ~10分钟 | ~8分钟 |
| 发言人识别准确率 | - | > 85% |

### 用户满意度
- 安装成功率 > 95%
- 首次运行成功率 > 90%
- 文档满意度 > 4.5/5

---

## 🚀 实施优先级

### P0（必须完成）
1. 安装脚本和配置向导
2. 发言人识别功能
3. 基础文档

### P1（重要）
1. 打包分发
2. UI 优化
3. 性能优化

### P2（可选）
1. 系统托盘
2. 自动更新
3. Docker 支持

---

## 📝 风险和挑战

### 技术风险
1. **pyannote.audio 模型下载**
   - 风险：需要 HuggingFace 账号和接受模型协议
   - 缓解：提供镜像下载方案，内置备用模型

2. **跨平台 FFmpeg 依赖**
   - 风险：Windows 用户安装困难
   - 缓解：打包内置 FFmpeg 二进制文件

3. **打包文件体积**
   - 风险：包含模型后文件过大（>2GB）
   - 缓解：模型首次使用时下载

### 时间风险
1. Day 5-7 发言人识别集成复杂度可能超预期
   - 缓解：Day 6 进行中期检查，必要时调整方案

---

## 📅 每日检查点

### Day 3 检查点
- [ ] 安装脚本可用
- [ ] 配置向导基本可用

### Day 7 检查点
- [ ] 发言人识别功能可用
- [ ] 基础测试通过

### Day 11 检查点
- [ ] UI 优化完成
- [ ] 端到端流程可用

### Day 14 最终检查
- [ ] 所有交付物完成
- [ ] 文档齐全
- [ ] 至少 3 人完成测试

---

## 🎯 成功标准

### 最小可行版本 (MVP) 必备功能
- [x] 双击安装脚本即可完成安装
- [x] 配置向导引导完成 API Key 设置
- [x] 自动下载 Whisper 模型
- [x] 转录结果显示发言人标签
- [x] 可以重命名发言人

### 理想版本额外功能
- [ ] 打包为独立可执行文件
- [ ] 发言人识别准确率 > 90%
- [ ] 提供示例视频和完整教程
- [ ] 支持多语言界面

---

## 📞 后续支持

### 第一版发布后计划
1. 收集用户反馈（1-2周）
2. 修复关键 Bug
3. 优化发言人识别准确率
4. 添加更多语言支持

### 第二版规划
1. Web UI 发言人管理
2. 实时转录功能
3. 视频会议集成（Zoom/Teams）
4. 云端存储支持

---

**文档版本**: 1.0
**最后更新**: 2026-05-08
**负责人**: 开发团队
