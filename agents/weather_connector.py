
import asyncio
import json
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import requests

# Add parent directories to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent))

from openagents.agents.worker_agent import WorkerAgent

# --- Constants & Config ---
GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
MAX_FORECAST_DAYS = 15

class WeatherRequestHandler(BaseHTTPRequestHandler):
    """HTTP request handler for receiving weather guide requests."""

    def log_message(self, format, *args):
        pass

    def do_POST(self):
        """Handle POST requests containing city and date info."""
        if self.path == '/guide':
            try:
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))

                city = data.get('city', '').strip()
                date_input = data.get('date', '')  # Could be offset (int) or date string

                if not city:
                    raise ValueError("City name is required")

                print(f"📨 收到出行指南请求: {city} (Date/Offset: {date_input})")

                # Push to asyncio queue
                future = asyncio.run_coroutine_threadsafe(
                    self.server.agent_queue.put({
                        'type': 'guide_request',
                        'city': city,
                        'date_input': date_input
                    }),
                    self.server.loop
                )
                future.result(timeout=1.0)

                response = {'status': 'accepted', 'message': 'Processing guide request...'}
                self.send_response(202)  # 202 Accepted
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(response).encode('utf-8'))

            except Exception as e:
                print(f"❌ 处理请求错误: {e}")
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'status': 'ok', 'agent': 'weather-connector'}).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

class WeatherConnector(WorkerAgent):
    """
    Connector that fetches weather data and posts it to the travel guide channel.
    """

    default_agent_id = "weather-connector"

    def __init__(self, http_port: int = 8889, **kwargs):
        super().__init__(**kwargs)
        self.http_port = http_port
        self.http_server = None
        self._http_thread = None
        self._message_processor_task = None
        self.message_queue = None
        self.loop = None

    async def on_startup(self):
        print(f"🚀 Weather Connector connected! Starting HTTP server on port {self.http_port}")
        self.loop = asyncio.get_running_loop()
        self.message_queue = asyncio.Queue()

        def run_server():
            server = HTTPServer(('localhost', self.http_port), self._make_handler_class())
            server.agent_queue = self.message_queue
            server.loop = self.loop
            server.serve_forever()

        self._http_thread = Thread(target=run_server, daemon=True)
        self._http_thread.start()
        print(f"📡 HTTP 服务器运行在 http://localhost:{self.http_port}")
        print(f"✈️ POST /guide 发送城市和日期")
        self._message_processor_task = asyncio.create_task(self._process_requests())

    def _make_handler_class(self):
        class Handler(WeatherRequestHandler):
            pass
        return Handler

    async def on_shutdown(self):
        if self._message_processor_task:
            self._message_processor_task.cancel()
        print("👋 Weather Connector disconnected.")

    async def _process_requests(self):
        while True:
            try:
                request_data = await self.message_queue.get()
                await self._handle_guide_request(request_data)
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"❌ 处理请求错误: {e}")

    # --- Weather Logic (Integrated from Demo) ---
    
    def _resolve_date(self, date_input: Any) -> str:
        """Resolve offset or date string to YYYY-MM-DD."""
        if not date_input:
            return datetime.now().strftime("%Y-%m-%d") # Default today
        
        # Try parsing as offset (int)
        try:
            offset = int(date_input)
            if abs(offset) > MAX_FORECAST_DAYS:
                raise ValueError(f"Offset exceeds limit ({MAX_FORECAST_DAYS})")
            target_date = datetime.now() + timedelta(days=offset)
            return target_date.strftime("%Y-%m-%d")
        except ValueError:
            pass # Not an int, try as date string

        # Try parsing as date string
        try:
            # Try common formats
            for fmt in ("%Y-%m-%d", "%Y/%m/%d"):
                try:
                    dt = datetime.strptime(date_input, fmt)
                    return dt.strftime("%Y-%m-%d")
                except ValueError:
                    continue
            
            # Try ISO format or similar
            cleaned = str(date_input).replace("/", "-")
            dt = datetime.fromisoformat(cleaned)
            return dt.strftime("%Y-%m-%d")
        except Exception:
            raise ValueError(f"Invalid date format: {date_input}")

    async def _fetch_weather_data(self, city: str, target_date_str: str) -> Dict[str, Any]:
        """Async wrapper to fetch weather."""
        loop = asyncio.get_running_loop()
        
        # 1. Geocoding
        def sync_geocode():
            params = {"name": city, "count": 1, "language": "zh", "format": "json"}
            resp = requests.get(GEOCODING_URL, params=params, timeout=5)
            resp.raise_for_status()
            results = resp.json().get("results", [])
            return results[0] if results else None

        city_info = await loop.run_in_executor(None, sync_geocode)
        if not city_info:
            return {"error": "City not found"}

        # 2. Fetch Weather
        def sync_weather():
            params = {
                "latitude": city_info["latitude"],
                "longitude": city_info["longitude"],
                "daily": "temperature_2m_max,temperature_2m_min,weather_code,precipitation_sum,wind_speed_10m_max",
                "timezone": "auto",
                "start_date": target_date_str,
                "end_date": target_date_str
            }
            resp = requests.get(FORECAST_URL, params=params, timeout=5)
            resp.raise_for_status()
            return resp.json()

        weather_data = await loop.run_in_executor(None, sync_weather)
        
        # 3. Extract relevant daily info
        daily = weather_data.get("daily", {})
        times = daily.get("time", [])
        
        # Find index for target date
        try:
            idx = times.index(target_date_str)
        except ValueError:
            return {"error": "Weather data not available for this date"}

        return {
            "city": city_info.get("name"),
            "country": city_info.get("country"),
            "date": target_date_str,
            "temp_max": daily["temperature_2m_max"][idx],
            "temp_min": daily["temperature_2m_min"][idx],
            "weather_code": daily["weather_code"][idx],
            "precipitation": daily["precipitation_sum"][idx],
            "wind_max": daily["wind_speed_10m_max"][idx]
        }

    async def _handle_guide_request(self, request_data: dict):
        city = request_data.get('city')
        date_input = request_data.get('date_input')

        try:
            target_date_str = self._resolve_date(date_input)
            weather_info = await self._fetch_weather_data(city, target_date_str)

            if "error" in weather_info:
                print(f"❌ {weather_info['error']}")
                return

            formatted_message = json.dumps({
                "request_type": "travel_guide",
                "data": weather_info
            }, ensure_ascii=False)

            # 使用 WorkerAgent 的 workspace 接口
            ws = self.workspace()
            await ws.channel("travel-guide-stream").post(formatted_message)

            print(f"✅ 已发送天气数据到频道: {city} @ {target_date_str}")

        except Exception as e:
            print(f"❌ 生成指南失败: {e}")


































async def main():
    import argparse
    parser = argparse.ArgumentParser(description="Weather Connector - HTTP Listener for Travel Guides")
    parser.add_argument("--host", default="localhost", help="Network host")
    parser.add_argument("--port", type=int, default=8700, help="Network port")
    parser.add_argument("--http-port", type=int, default=8889, help="HTTP server port")
    args = parser.parse_args()

    agent = WeatherConnector(http_port=args.http_port)
    try:
        await agent.async_start(network_host=args.host, network_port=args.port)
        print(f"🎯 Weather Connector running.")
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 正在关闭...")
    finally:
        await agent.async_stop()

if __name__ == "__main__":
    asyncio.run(main())
