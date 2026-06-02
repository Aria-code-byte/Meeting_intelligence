#!/usr/bin/env python3
"""
导出最近转录结果的 JSON 文件
"""
import json
import requests
import sys
from pathlib import Path

def export_recent_transcription():
    """导出最近的转录结果"""

    # 后端 API 地址
    base_url = "http://localhost:8000"

    try:
        # 获取所有任务
        response = requests.get(f"{base_url}/api/v1/transcription/jobs", timeout=10)
        response.raise_for_status()

        jobs = response.json()
        jobs_list = jobs.get("jobs", [])

        if not jobs_list:
            print("没有找到任何转录任务")
            return

        # 按创建时间排序，获取最新的
        jobs_list.sort(key=lambda x: x.get("createdAt", ""), reverse=True)
        latest_job = jobs_list[0]

        job_id = latest_job.get("jobId")
        print(f"找到最新任务: {job_id}")
        print(f"状态: {latest_job.get('status')}")
        print(f"创建时间: {latest_job.get('createdAt')}")

        # 获取任务详情
        detail_response = requests.get(f"{base_url}/api/v1/transcription/jobs/{job_id}", timeout=10)
        detail_response.raise_for_status()

        job_detail = detail_response.json()

        # 保存到文件
        output_dir = Path("/mnt/d/projects/Meeting_intelligence/exports")
        output_dir.mkdir(exist_ok=True)

        output_file = output_dir / f"transcription_{job_id}.json"

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(job_detail, f, ensure_ascii=False, indent=2)

        print(f"\n✅ 结果已导出到: {output_file}")

        # 打印摘要
        result = job_detail.get("result", {})
        if result:
            print(f"\n转录摘要:")
            print(f"- 语言: {result.get('language')}")
            print(f"- 模型: {result.get('model')}")
            print(f"- 说话人分离: {'启用' if result.get('diarizationEnabled') else '禁用'}")
            print(f"- 发言轮次: {result.get('raw', {}).get('turnsCount', 0)}")

        return str(output_file)

    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到后端服务 (http://localhost:8000)")
        print("请确保后端服务正在运行")
        return None
    except requests.exceptions.HTTPError as e:
        print(f"❌ HTTP 错误: {e}")
        return None
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    export_recent_transcription()
