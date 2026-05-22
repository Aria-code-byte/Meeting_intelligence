"""
测试总结生成 API
"""
import requests
import time

BASE_URL = "http://localhost:8000"

print("=" * 60)
print("测试总结生成 API - DeepSeek")
print("=" * 60)

# 步骤1：上传文件
print("\n[步骤 1] 上传文件")
files = {'file': ('test_meeting.txt', 'Test meeting content', 'text/plain')}
data = {'title': '测试会议'}

response = requests.post(f"{BASE_URL}/api/upload", files=files, data=data)
if response.status_code == 200:
    result = response.json()
    meeting_id = result.get("meeting_id")
    print(f"✓ 文件上传成功")
    print(f"Meeting ID: {meeting_id}")
else:
    print(f"✗ 文件上传失败")
    exit(1)

# 步骤2：启动转录
print("\n[步骤 2] 启动转录")
response = requests.post(f"{BASE_URL}/api/meetings/{meeting_id}/transcribe")
if response.status_code == 200:
    print(f"✓ 转录任务启动成功")

    # 等待转录完成
    for i in range(10):
        time.sleep(2)
        status_response = requests.get(f"{BASE_URL}/api/meetings/{meeting_id}/transcription-status")
        if status_response.status_code == 200:
            status_data = status_response.json()
            if status_data.get("success"):
                status = status_data.get("status")
                if status == "completed":
                    print(f"✓ 转录完成")
                    break
                elif status == "failed":
                    print(f"✗ 转录失败")
                    break
else:
    print(f"✗ 转录启动失败")

# 步骤3：获取转录结果
print("\n[步骤 3] 获取转录结果")
response = requests.get(f"{BASE_URL}/api/meetings/{meeting_id}/transcript")
if response.status_code == 200:
    result = response.json()
    if result.get("success"):
        transcript = result.get("transcript", "")
        print(f"✓ 转录获取成功")
        print(f"Transcript length: {len(transcript)} chars")
else:
    print(f"✗ 转录API失败")

# 步骤4：启动总结生成（使用 DeepSeek）
print("\n[步骤 4] 启动总结生成 - DeepSeek")
summary_data = {
    "template_id": "custom_1778838491",  # 大学生课程模板
    "output_format": "markdown"
}

response = requests.post(
    f"{BASE_URL}/api/meetings/{meeting_id}/summarize",
    json=summary_data
)

if response.status_code == 200:
    result = response.json()
    if result.get("success"):
        task_id = result.get("task_id")
        print(f"✓ 总结任务启动成功")
        print(f"Template: 大学生课程 (custom_1778838491)")

        # 等待总结完成
        for i in range(30):
            time.sleep(2)
            status_response = requests.get(f"{BASE_URL}/api/meetings/{meeting_id}/summary-status")
            if status_response.status_code == 200:
                status_data = status_response.json()
                if status_data.get("success"):
                    status = status_data.get("status")
                    if status == "completed":
                        print(f"✓ 总结生成完成")
                        break
                    elif status == "failed":
                        print(f"✗ 总结生成失败")
                        error = status_data.get("error", "未知错误")
                        print(f"错误: {error}")
                        break
else:
    print(f"✗ 总结任务启动失败: HTTP {response.status_code}")
    print(f"响应: {response.text}")

# 步骤5：获取总结结果
print("\n[步骤 5] 获取总结结果")
response = requests.get(f"{BASE_URL}/api/meetings/{meeting_id}/summary")

if response.status_code == 200:
    result = response.json()
    if result.get("success"):
        summary = result.get("summary", "")
        template_id = result.get("template_id", "")

        print(f"✓ 总结获取成功")
        print(f"Template ID: {template_id}")
        print(f"Summary length: {len(summary)} chars")

        if len(summary) > 0:
            print(f"\n[SUCCESS] 这是真实的 DeepSeek 总结！")
            print(f"\n总结预览:")
            print("=" * 60)
            print(summary[:400] + "...")
            print("=" * 60)
        else:
            print(f"\n[ERROR] 总结为空！")
    else:
        print(f"✗ {result.get('message')}")
else:
    print(f"✗ 总结API失败 - HTTP {response.status_code}")

print("\n" + "=" * 60)
print("测试完成")
print("=" * 60)