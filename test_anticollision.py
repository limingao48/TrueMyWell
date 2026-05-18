import requests
import json

# 测试防碰扫描接口
url = "http://localhost:8003/anticollision/scan"

# 测试请求数据
data = {
    "trajectoryId": 1,
    "neighborWellIds": [2],
    "anticollisionMethod": "CTC",
    "safeRadius": 10.0,
    "minSafetyFactor": 1.2
}

try:
    response = requests.post(url, json=data)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
