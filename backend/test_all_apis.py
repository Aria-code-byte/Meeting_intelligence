"""
完整 API 功能测试
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000"

print("=" * 60)
print("Jinni Meeting Intelligence - 完整功能测试")
print("=" * 60)

# 测试 1：健康检查
print("\n[测试 1] 健康检查")
print("-" * 60)
try:
    response = requests.get(f"{BASE_URL}/health", timeout=5)
    if response.status_code == 200:
        print("PASS: Backend service is running")
        print(f"Response: {response.json()}")
    else:
        print(f"FAIL: Backend service error, status code: {response.status_code}")
except Exception as e:
    print(f"FAIL: Cannot connect to backend: {str(e)}")
    exit(1)

# 测试 2：模板 API
print("\n[测试 2] 模板管理 API")
print("-" * 60)
try:
    response = requests.get(f"{BASE_URL}/api/templates", timeout=10)
    if response.status_code == 200:
        templates = response.json().get("templates", [])
        print(f"PASS: Got {len(templates)} templates")
        print(f"Templates:")
        for template in templates[:3]:
            print(f"  - {template['name']}")
    else:
        print(f"FAIL: Template API failed, status code: {response.status_code}")
except Exception as e:
    print(f"FAIL: Template API test failed: {str(e)}")

# 测试 3：创建测试会议
print("\n[测试 3] 创建测试会议")
print("-" * 60)
meeting_id = None
try:
    files = {'file': ('test_audio.txt', 'Test audio content', 'text/plain')}
    data = {'title': 'API Test Meeting'}
    response = requests.post(f"{BASE_URL}/api/upload", files=files, data=data, timeout=10)
    if response.status_code == 200:
        result = response.json()
        if result.get("success"):
            meeting_id = result.get("meeting_id")
            print(f"PASS: Test meeting created")
            print(f"Meeting ID: {meeting_id}")
        else:
            print(f"FAIL: Meeting creation failed: {result.get('message')}")
    else:
        print(f"FAIL: Meeting creation failed, status code: {response.status_code}")
except Exception as e:
    print(f"FAIL: Meeting creation test failed: {str(e)}")

if not meeting_id:
    print("\nCannot continue testing - meeting creation failed")
    exit(1)

# 测试 4：启动转录
print("\n[测试 4] 启动转录任务")
print("-" * 60)
try:
    response = requests.post(f"{BASE_URL}/api/meetings/{meeting_id}/transcribe", timeout=10)
    if response.status_code == 200:
        result = response.json()
        if result.get("success"):
            task_id = result.get("task_id")
            print(f"PASS: Transcription task started")
            print(f"Task ID: {task_id}")
            
            # Wait for completion
            print("Waiting for transcription...")
            for i in range(10):
                time.sleep(2)
                status_response = requests.get(f"{BASE_URL}/api/meetings/{meeting_id}/transcription-status", timeout=5)
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    if status_data.get("success"):
                        status = status_data.get("status")
                        progress = status_data.get("progress", 0)
                        if status == "completed":
                            print("PASS: Transcription completed")
                            break
                        elif status == "failed":
                            print("FAIL: Transcription failed")
                            break
                        else:
                            print(f"Transcribing... {progress}%")
        else:
            print(f"FAIL: Transcription task failed: {result.get('message')}")
    else:
        print(f"FAIL: Transcription task failed, status code: {response.status_code}")
except Exception as e:
    print(f"FAIL: Transcription test failed: {str(e)}")

# 测试 5：获取转录结果
print("\n[测试 5] 获取转录结果")
print("-" * 60)
try:
    response = requests.get(f"{BASE_URL}/api/meetings/{meeting_id}/transcript", timeout=10)
    if response.status_code == 200:
        result = response.json()
        if result.get("success"):
            transcript = result.get("transcript", "")
            segments = result.get("segments", [])
            print(f"PASS: Got transcript")
            print(f"Transcript length: {len(transcript)} chars")
            print(f"Segments: {len(segments)}")
            if len(transcript) > 0:
                print(f"Preview: {transcript[:100]}...")
        else:
            print(f"FAIL: Failed to get transcript: {result.get('message')}")
    else:
        print(f"FAIL: Transcript API failed, status code: {response.status_code}")
except Exception as e:
    print(f"FAIL: Transcript test failed: {str(e)}")

# 测试 6：启动总结生成
print("\n[测试 6] 启动总结生成任务")
print("-" * 60)
try:
    summary_data = {"template_id": "general_meeting", "output_format": "markdown"}
    response = requests.post(f"{BASE_URL}/api/meetings/{meeting_id}/summarize", json=summary_data, timeout=10)
    if response.status_code == 200:
        result = response.json()
        if result.get("success"):
            task_id = result.get("task_id")
            print(f"PASS: Summary task started")
            print(f"Task ID: {task_id}")
            print(f"Template: general_meeting")
            
            # Wait for completion
            print("Waiting for summary generation...")
            for i in range(20):
                time.sleep(2)
                status_response = requests.get(f"{BASE_URL}/api/meetings/{meeting_id}/summary-status", timeout=5)
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    if status_data.get("success"):
                        status = status_data.get("status")
                        progress = status_data.get("progress", 0)
                        if status == "completed":
                            print("PASS: Summary generation completed")
                            break
                        elif status == "failed":
                            print("FAIL: Summary generation failed")
                            break
                        else:
                            print(f"Generating... {progress}%")
        else:
            print(f"FAIL: Summary task failed: {result.get('message')}")
    else:
        print(f"FAIL: Summary task failed, status code: {response.status_code}")
except Exception as e:
    print(f"FAIL: Summary test failed: {str(e)}")

# 测试 7：获取总结结果
print("\n[测试 7] 获取总结结果")
print("-" * 60)
try:
    response = requests.get(f"{BASE_URL}/api/meetings/{meeting_id}/summary", timeout=10)
    if response.status_code == 200:
        result = response.json()
        if result.get("success"):
            summary = result.get("summary", "")
            template_id = result.get("template_id", "")
            print(f"PASS: Got summary")
            print(f"Summary length: {len(summary)} chars")
            print(f"Template: {template_id}")
            if len(summary) > 0:
                print(f"Preview:")
                print(f"{summary[:200]}...")
            else:
                print("WARNING: Summary is empty - LLM might not be configured")
        else:
            print(f"FAIL: Failed to get summary: {result.get('message')}")
    else:
        print(f"FAIL: Summary API failed, status code: {response.status_code}")
except Exception as e:
    print(f"FAIL: Summary result test failed: {str(e)}")

print("\n" + "=" * 60)
print("功能测试完成")
print("=" * 60)
print("\n[总结]")
print("如果所有测试都显示 PASS，说明系统功能正常")
print("如果有 FAIL，请检查对应的模块")
print("\n[下一步]")
print("1. 访问前端: http://localhost:8501")
print("2. 运行完整工作流测试")
print("3. 查看后端日志验证 DeepSeek 调用")
print("=" * 60)
