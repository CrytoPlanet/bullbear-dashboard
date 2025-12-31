#!/usr/bin/env python3
"""
简单的测试脚本，用于验证前后端连接
"""

import requests
import sys

BACKEND_URL = "http://localhost:8000"

def test_backend():
    """测试后端API"""
    print("🔍 测试后端连接...")
    
    # 测试健康检查
    try:
        response = requests.get(f"{BACKEND_URL}/api/health", timeout=5)
        if response.status_code == 200:
            print("✅ 健康检查通过")
            print(f"   响应: {response.json()}")
        else:
            print(f"❌ 健康检查失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 无法连接到后端: {e}")
        print(f"   请确保后端服务运行在 {BACKEND_URL}")
        return False
    
    # 测试获取所有数据
    try:
        response = requests.get(f"{BACKEND_URL}/api/data", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✅ 数据获取成功")
            if data.get("ok") and "data" in data:
                print(f"   数据项数量: {len(data['data'])}")
                for key, value in data["data"].items():
                    print(f"   - {key}: {value.get('value', 'N/A')}")
        else:
            print(f"❌ 数据获取失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 数据获取错误: {e}")
        return False
    
    # 测试状态机
    try:
        response = requests.get(f"{BACKEND_URL}/api/state", timeout=5)
        if response.status_code == 200:
            state = response.json()
            print("✅ 状态机评估成功")
            if state.get("ok"):
                print(f"   当前状态: {state.get('state', 'N/A')}")
                print(f"   趋势: {state.get('trend', 'N/A')}")
                print(f"   资金姿态: {state.get('funding', 'N/A')}")
                print(f"   风险等级: {state.get('risk_level', 'N/A')}")
                print(f"   置信度: {state.get('confidence', 0):.1%}")
        else:
            print(f"❌ 状态机评估失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 状态机评估错误: {e}")
        return False
    
    print("\n🎉 所有测试通过！前后端连接正常。")
    return True

if __name__ == "__main__":
    success = test_backend()
    sys.exit(0 if success else 1)

