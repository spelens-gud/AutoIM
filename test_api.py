"""测试旺旺RPA Web API 的示例脚本。"""

import requests
import time

# API基础URL
BASE_URL = "http://localhost:5000"


def test_health():
    """测试健康检查接口。"""
    print("\n1. 测试健康检查...")
    response = requests.get(f"{BASE_URL}/api/health")
    print(f"   状态码: {response.status_code}")
    print(f"   响应: {response.json()}")


def test_start_rpa():
    """测试启动RPA系统。"""
    print("\n2. 启动RPA系统...")
    response = requests.post(f"{BASE_URL}/api/rpa/start", json={
        "headless": False
    })
    print(f"   状态码: {response.status_code}")
    print(f"   响应: {response.json()}")
    
    # 等待系统启动
    time.sleep(5)


def test_get_status():
    """测试获取系统状态。"""
    print("\n3. 获取系统状态...")
    response = requests.get(f"{BASE_URL}/api/rpa/status")
    print(f"   状态码: {response.status_code}")
    print(f"   响应: {response.json()}")


def test_send_message():
    """测试发送消息。"""
    print("\n4. 发送消息...")
    response = requests.post(f"{BASE_URL}/api/message/send", json={
        "contact_id": "测试店铺",
        "content": "你好，这是一条测试消息"
    })
    print(f"   状态码: {response.status_code}")
    print(f"   响应: {response.json()}")


def test_check_messages():
    """测试检查新消息。"""
    print("\n5. 检查新消息...")
    response = requests.get(f"{BASE_URL}/api/message/check")
    print(f"   状态码: {response.status_code}")
    print(f"   响应: {response.json()}")


def test_list_sessions():
    """测试获取会话列表。"""
    print("\n6. 获取会话列表...")
    response = requests.get(f"{BASE_URL}/api/session/list")
    print(f"   状态码: {response.status_code}")
    print(f"   响应: {response.json()}")
    
    print("\n7. 获取活跃会话...")
    response = requests.get(f"{BASE_URL}/api/session/list?active_only=true")
    print(f"   状态码: {response.status_code}")
    print(f"   响应: {response.json()}")


def test_auto_reply_rules():
    """测试获取自动回复规则。"""
    print("\n8. 获取自动回复规则...")
    response = requests.get(f"{BASE_URL}/api/auto-reply/rules")
    print(f"   状态码: {response.status_code}")
    data = response.json()
    if data.get('success'):
        print(f"   规则数量: {data['data']['count']}")
        print(f"   前3条规则: {data['data']['rules'][:3]}")
    else:
        print(f"   响应: {data}")


def test_auto_reply_test():
    """测试自动回复匹配。"""
    print("\n9. 测试自动回复匹配...")
    
    test_messages = [
        "这个多少钱？",
        "有货吗？",
        "你好",
        "发货了吗？"
    ]
    
    for msg in test_messages:
        response = requests.post(f"{BASE_URL}/api/auto-reply/test", json={
            "message": msg
        })
        data = response.json()
        if data.get('success'):
            matched = data['data']['matched']
            reply = data['data'].get('reply', '无匹配')
            print(f"   消息: '{msg}' -> 匹配: {matched}, 回复: {reply[:50]}...")
        else:
            print(f"   消息: '{msg}' -> 错误: {data.get('message')}")


def test_stop_rpa():
    """测试停止RPA系统。"""
    print("\n10. 停止RPA系统...")
    response = requests.post(f"{BASE_URL}/api/rpa/stop")
    print(f"   状态码: {response.status_code}")
    print(f"   响应: {response.json()}")


def main():
    """主函数。"""
    print("=" * 60)
    print("旺旺RPA Web API 测试")
    print("=" * 60)
    print("\n请确保 API 服务已启动: python api_server.py")
    print("\n按回车开始测试...")
    input()
    
    try:
        # 1. 健康检查
        test_health()
        
        # 2. 启动RPA（需要手动登录）
        test_start_rpa()
        
        print("\n⚠️  如果浏览器提示需要登录，请手动登录后按回车继续...")
        input()
        
        # 3. 获取状态
        test_get_status()
        
        # 4. 发送消息（可选，需要有真实的联系人）
        # test_send_message()
        
        # 5. 检查消息
        test_check_messages()
        
        # 6. 获取会话列表
        test_list_sessions()
        
        # 7. 获取自动回复规则
        test_auto_reply_rules()
        
        # 8. 测试自动回复
        test_auto_reply_test()
        
        # 9. 停止RPA
        test_stop_rpa()
        
        print("\n" + "=" * 60)
        print("测试完成！")
        print("=" * 60)
        
    except requests.exceptions.ConnectionError:
        print("\n❌ 错误: 无法连接到API服务")
        print("   请确保已启动API服务: python api_server.py")
    except Exception as e:
        print(f"\n❌ 错误: {str(e)}")


if __name__ == "__main__":
    main()
