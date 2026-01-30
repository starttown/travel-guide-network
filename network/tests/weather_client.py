import requests
import json
import sys

def send_weather_request(server_url, city, date=None):
    """
    发送天气请求到 weather_connector
    
    Args:
        server_url: weather_connector 的地址 (例如: http://192.168.1.100:8888/generate)
        city: 城市名称
        date: 可选，日期偏移量(如 "0" 表示今天，"1" 表示明天)
    """
    payload = {"city": city}
    if date is not None:
        payload["date"] = date
    
    try:
        print(f"正在发送请求到 {server_url}...")
        print(f"参数: 城市={city}, 日期={date if date else '默认'}")
        print("-" * 50)
        
        response = requests.post(server_url, json=payload, timeout=10)
        
        print(f"HTTP 状态码: {response.status_code}")
        print("服务器响应:")
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
        
    except requests.exceptions.ConnectionError:
        print("❌ 连接失败：无法连接到 weather_connector 服务")
        print("   请确认：")
        print("   1. weather_connector 是否已启动")
        print("   2. 地址和端口是否正确")
    except requests.exceptions.Timeout:
        print("❌ 请求超时")
    except Exception as e:
        print(f"❌ 发生错误: {e}")

if __name__ == "__main__":
    # 配置 weather_connector 的地址
    # 注意：如果是局域网使用，请替换为实际的服务器IP地址
    CONNECTOR_URL = "http://localhost:8888/generate"
    
    # 示例用法
    if len(sys.argv) > 1:
        city = sys.argv[1]
        date = sys.argv[2] if len(sys.argv) > 2 else None
    else:
        # 交互式输入
        city = input("请输入城市名称: ").strip()
        date_input = input("请输入日期偏移量（可选，直接回车跳过）: ").strip()
        date = date_input if date_input else None
    
    if not city:
        print("城市名称不能为空")
        sys.exit(1)
    
    send_weather_request(CONNECTOR_URL, city, date)
