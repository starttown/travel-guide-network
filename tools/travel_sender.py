"""
MIT License

Copyright (c) 2026 starttown

Permission is hereby granted, free of charge, to any person obtaining a copy

"""

#!/usr/bin/env python3
"""
Travel Sender - Sends city and date to Weather Connector.
"""

import requests
import json
import sys

# 配置 Connector 的 HTTP 地址
CONNECTOR_URL = "http://localhost:8889/guide"

def send_travel_request(city_name: str, date_input: str = None):
    """Send travel guide request."""
    payload = {"city": city_name}
    if date_input:
        payload["date"] = date_input
    
    try:
        print(f"✈️ 正在发送出行指南请求: 城市={city_name}, 日期/Offset={date_input or '今天'} ...")
        resp = requests.post(CONNECTOR_URL, json=payload, timeout=5)
        
        if resp.status_code == 202:
            print(f"✅ 请求已接受，AI 正在生成指南，请查看频道输出...")
            print(f"   服务器响应: {resp.json()}")
        else:
            print(f"❌ 发送失败: {resp.status_code} - {resp.text}")
            
    except requests.exceptions.ConnectionError:
        print(f"❌ 无法连接到服务器 ({CONNECTOR_URL})，请确保 Weather Connector 已启动。")
    except Exception as e:
        print(f"❌ 网络错误: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python travel_sender.py <城市名> [日期/Offset]")
        print("示例:")
        print("  python travel_sender.py Beijing       # 今天")
        print("  python travel_sender.py Beijing 1      # 明天")
        print("  python travel_sender.py Shanghai 2     # 后天")
        print("  python travel_sender.py Tokyo 2026-01-20")
        sys.exit(1)

    target_city = sys.argv[1]
    date_input = sys.argv[2] if len(sys.argv) > 2 else None
    send_travel_request(target_city, date_input)
