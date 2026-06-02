# 转录结果导出指南

## 如何导出转录结果 JSON

### 方法 1：使用导出脚本（推荐）

```bash
# 激活虚拟环境
source /mnt/d/projects/Meeting_intelligence/.venv/bin/activate

# 运行导出脚本（需要提供 job_id）
python export_recent_result.py <job_id>
```

**如何获取 job_id：**

1. 打开浏览器开发者工具 (F12)
2. 切换到 Network 标签
3. 在 Web UI 中上传文件并开始转录
4. 查找 `transcriptions/jobs` 相关的请求
5. 从 URL 或响应中复制 `jobId`

### 方法 2：直接使用 curl

```bash
# 获取任务结果
curl http://localhost:8000/api/v1/transcriptions/jobs/<job_id> | python3 -m json.tool

# 保存到文件
curl http://localhost:8000/api/v1/transcriptions/jobs/<job_id> > exports/result.json
```

### 方法 3：在浏览器中直接访问

```
http://localhost:8000/api/v1/transcriptions/jobs/<job_id>
```

然后使用浏览器保存为 JSON 文件。

## 导出文件说明

导出脚本会生成以下文件：

| 文件 | 内容 |
|------|------|
| `transcription_<job_id>.json` | 完整任务数据（包含状态、时间等） |
| `result_<job_id>.json` | 仅转录结果（segments、turns 等） |
| `readable_<job_id>.md` | 可读转录文本（带时间戳和角色） |

## 任务存储说明

- 转录任务默认 **TTL 为 1 小时**
- 超时后任务会被自动清理
- 如需长期保存，请及时导出结果

## 示例：转录结果 JSON 结构

```json
{
  "text": "完整文字稿纯文本...",
  "readableTranscript": "# 会议转录\n\n[00:00:00] **主持人**: ...",
  "language": "zh",
  "model": "large-v3-turbo",
  "turns": [
    {
      "speaker": "SPEAKER_00",
      "role": "主持人",
      "start": 0.0,
      "end": 12.34,
      "text": "喂，能听到吗？"
    }
  ],
  "diarizationEnabled": true,
  "raw": {
    "audioDuration": 345.67,
    "turnsCount": 45,
    "speakerStats": {
      "SPEAKER_00": 12,
      "SPEAKER_01": 28
    }
  }
}
```

## 注意事项

1. **任务过期**：任务会在完成后 1 小时自动清理
2. **并发限制**：最多 100 个并发任务
3. **文件大小**：默认最大 3GB
4. **导出目录**：所有导出文件保存在 `exports/` 目录
