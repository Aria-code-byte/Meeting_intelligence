#!/usr/bin/env python3
"""
导出转录结果 JSON
==================
从后端 API 获取指定的转录任务结果并保存为 JSON 文件

使用方法：
    python export_recent_result.py <job_id>

如果不提供 job_id，将尝试获取最近的任务
"""

import json
import sys
from pathlib import Path

def export_job_result(job_id: str = None):
    """导出指定任务的结果"""

    try:
        import requests
    except ImportError:
        print("正在安装 requests...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "requests", "-q"])
        import requests

    base_url = "http://localhost:8000/api/v1"

    # 如果没有提供 job_id，需要想办法获取
    if not job_id:
        print("未提供 job_id")
        print("\n使用方法：")
        print("  python export_recent_result.py <job_id>")
        print("\n从浏览器开发者工具的 Network 标签中可以找到 job_id")
        return None

    print(f"正在获取任务: {job_id}")

    try:
        # 获取任务详情
        response = requests.get(f"{base_url}/transcriptions/jobs/{job_id}", timeout=10)

        if response.status_code == 404:
            print(f"❌ 任务不存在: {job_id}")
            print("\n任务可能已过期（默认1小时 TTL）")
            return None

        response.raise_for_status()
        data = response.json()

        # 检查任务状态
        status = data.get("status")
        if status != "completed":
            print(f"⚠️  任务未完成: {status}")
            print(f"阶段: {data.get('stage')}")
            print(f"进度: {data.get('progress')}%")
            return None

        # 获取结果
        result = data.get("result")
        if not result:
            print("❌ 任务没有结果数据")
            return None

        # 创建导出目录
        export_dir = Path("/mnt/d/projects/Meeting_intelligence/exports")
        export_dir.mkdir(exist_ok=True)

        # 保存完整响应
        output_file = export_dir / f"transcription_{job_id}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"\n✅ 完整任务数据已导出到: {output_file}")

        # 单独保存转录结果
        result_file = export_dir / f"result_{job_id}.json"
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        print(f"✅ 转录结果已导出到: {result_file}")

        # 保存可读转录文本（如果存在）
        if result.get("readableTranscript"):
            transcript_file = export_dir / f"readable_{job_id}.md"
            with open(transcript_file, 'w', encoding='utf-8') as f:
                f.write(result["readableTranscript"])
            print(f"✅ 可读转录文本已导出到: {transcript_file}")

        # 打印摘要
        print(f"\n📊 转录摘要:")
        print(f"- 语言: {result.get('language')}")
        print(f"- 模型: {result.get('model')}")
        print(f"- 说话人分离: {'启用' if result.get('diarizationEnabled') else '禁用'}")
        print(f"- 对齐状态: {result.get('alignmentStatus')}")

        raw = result.get('raw', {})
        print(f"- 音频时长: {raw.get('audioDuration', 0):.1f}秒")
        print(f"- 发言轮次: {raw.get('turnsCount', 0)}")
        print(f"- 说话人数量: {len(raw.get('speakerStats', {}))}")

        return str(output_file)

    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到后端服务 (http://localhost:8000)")
        print("请确保后端服务正在运行")
        return None
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    if len(sys.argv) > 1:
        job_id = sys.argv[1]
    else:
        job_id = None

    export_job_result(job_id)
