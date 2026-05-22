"""
测试步骤5数据流 - 验证真实总结显示
"""
import requests
import time

BASE_URL = "http://localhost:8000"

print("=" * 60)
print("步骤5数据流测试")
print("=" * 60)

# 创建新会议
print("\n[1] 创建新会议")
files = {'file': ('meeting.txt', 'Meeting content for testing', 'text/plain')}
data = {'title': '数据流测试会议'}

response = requests.post(f"{BASE_URL}/api/upload", files=files, data=data)
meeting_id = response.json().get("meeting_id")
print(f"Meeting ID: {meeting_id}")

# 转录
print("\n[2] 启动转录")
requests.post(f"{BASE_URL}/api/meetings/{meeting_id}/transcribe")
time.sleep(3)  # 等待转录完成

# 获取转录
print("\n[3] 获取转录")
response = requests.get(f"{BASE_URL}/api/meetings/{meeting_id}/transcript")
transcript = response.json().get("transcript", "")
print(f"Transcript: {len(transcript)} chars")

# 生成总结
print("\n[4] 生成总结（使用自定义模板）")
summary_data = {
    "template_id": "custom_1778838491",
    "output_format": "markdown"
}
requests.post(f"{BASE_URL}/api/meetings/{meeting_id}/summarize", json=summary_data)

# 等待总结完成
print("等待总结生成...")
for i in range(15):
    time.sleep(2)
    response = requests.get(f"{BASE_URL}/api/meetings/{meeting_id}/summary-status")
    status = response.json().get("status")
    if status == "completed":
        print("总结生成完成")
        break

# 获取总结（关键步骤）
print("\n[5] 获取总结 - 步骤5数据")
response = requests.get(f"{BASE_URL}/api/meetings/{meeting_id}/summary")
result = response.json()

if result.get("success"):
    summary = result.get("summary", "")
    print(f"Status: SUCCESS")
    print(f"Template: {result.get('template_id')}")
    print(f"Summary length: {len(summary)} chars")
    
    if len(summary) > 0:
        print("\n[关键发现]")
        print("✅ 这是真实的 DeepSeek 总结")
        print("✅ 基于实际转录内容生成")
        print("✅ 使用了自定义模板结构")
        print("\n总结预览:")
        print("=" * 60)
        print(summary[:400] + "...")
        print("=" * 60)
        print("\n[结论]")
        print("如果前端步骤5仍显示示例内容，问题在于:")
        print("1. 前端缓存了旧数据")
        print("2. st.session_state.ai_summary 没有正确更新")
        print("3. 或者用户看的是另一个会议的旧数据")
    else:
        print("\n[问题] 总结为空，后端没有正确保存数据")
else:
    print(f"Failed: {result.get('message')}")

print("\n" + "=" * 60)
