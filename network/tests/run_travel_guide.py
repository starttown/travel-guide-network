#!/usr/bin/env python3
"""
Client Script - Fetches weather and starts a Travel Guide project.
"""
import asyncio
import sys
import requests
import json
from datetime import datetime, timedelta
from openagents.core.client import AgentClient
from openagents.models.event import Event

# --- 天气 API 逻辑 (复用原 weather_connector 的逻辑) ---
GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

def resolve_date(date_input):
    if not date_input: return datetime.now().strftime("%Y-%m-%d")
    try:
        offset = int(date_input)
        return (datetime.now() + timedelta(days=offset)).strftime("%Y-%m-%d")
    except ValueError:
        pass
    return date_input # Assume string YYYY-MM-DD

def get_weather_data(city, date_input):
    """获取天气数据，返回 JSON 字符串"""
    try:
        # 1. Geocoding
        geo_resp = requests.get(GEOCODING_URL, params={"name": city, "count": 1, "language": "zh", "format": "json"}, timeout=5)
        city_info = geo_resp.json().get("results", [{}])[0]
        if not city_info: return None

        # 2. Weather
        date_str = resolve_date(date_input)
        weather_resp = requests.get(FORECAST_URL, params={
            "latitude": city_info["latitude"],
            "longitude": city_info["longitude"],
            "daily": "temperature_2m_max,temperature_2m_min,weather_code,precipitation_sum,wind_speed_10m_max",
            "timezone": "auto",
            "start_date": date_str,
            "end_date": date_str
        }, timeout=5)
        
        data = weather_resp.json()["daily"]
        idx = data["time"].index(date_str)
        
        return json.dumps({
            "city": city_info.get("name"),
            "date": date_str,
            "temp_max": data["temperature_2m_max"][idx],
            "temp_min": data["temperature_2m_min"][idx],
            "weather_code": data["weather_code"][idx],
            "precipitation": data["precipitation_sum"][idx],
            "wind_max": data["wind_speed_10m_max"][idx]
        }, ensure_ascii=False)
    except Exception as e:
        print(f"Error fetching weather: {e}")
        return None

# --- 主程序 ---
async def main():
    if len(sys.argv) < 2:
        print("Usage: python run_travel_guide.py <City> [DateOffset]")
        sys.exit(1)

    city = sys.argv[1]
    date_offset = sys.argv[2] if len(sys.argv) > 2 else None

    print(f"🌤️  正在获取 {city} ({date_offset or '今天'}) 的天气数据...")
    weather_json = get_weather_data(city, date_offset)

    if not weather_json:
        print("❌ 获取天气失败")
        return

    print(f"✅ 天气数据获取成功:\n{weather_json}\n")
    print("🚀 正在连接网络并生成指南...")

    client = AgentClient(agent_id="travel-client")

    try:
        # 修改这里：添加 enforce_transport_type="http"
        if not await client.connect(
            network_host="localhost", 
            network_port=8700, 
            skip_detection=True,
            enforce_transport_type="http"  # <--- 必须加上这一行
            ):
            print("❌ 连接网络失败")
            return

        # 启动项目，将天气数据作为 goal 传入
        start_event = Event(
            event_name="project.start",
            source_id="travel-client",
            destination_id="system",
            payload={
                "template_id": "generate_travel_guide",
                "name": f"Travel Guide for {city}",
                "goal": weather_json # 将 JSON 数据放在这里传给 Coordinator
            }
        )

        response = await client.send_event(start_event)
        if not response or not response.success:
            print(f"❌ 启动项目失败: {response.message if response else 'Unknown'}")
            return

        project_id = response.data.get("project_id")
        print(f"✅ 项目已启动: {project_id}")
        print("⏳ 等待各学院学生生成建议...\n")

        # 轮询结果
        for i in range(60): # 等待 60 秒
            await asyncio.sleep(1)
            
            get_event = Event(
                event_name="project.get",
                source_id="travel-client",
                destination_id="system",
                payload={"project_id": project_id}
            )
            
            status_resp = await client.send_event(get_event)
            project = status_resp.data.get('project', {})
            status = project.get('status')
            messages = project.get('messages', [])

            # 实时打印消息
            if i % 5 == 0: # 每5秒打印一次进度
                 print(f"  [{i}s] Status: {status}")

            if status == 'completed':
                print("\n" + "="*60)
                print("🎉 出行指南生成完毕！")
                print("="*60)
                # 打印所有消息
                for msg in messages:
                    sender = msg.get('sender_id', 'system')
                    text = msg.get('content', {}).get('text', '')
                    if text and "travel-client" not in sender: # 不打印自己的消息
                        print(f"\n[{sender}]:")
                        print(text)
                print("="*60)
                break
        else:
            print("⏰ Timeout")

    finally:
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
