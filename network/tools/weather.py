#!/usr/bin/env python3
"""
tools/weather.py
天气服务工具模块
提供获取天气数据和格式化输出的功能
"""
import logging
import json
import requests
from datetime import datetime, timedelta

# --- 配置常量 ---
WEATHER_API_URL = "https://api.open-meteo.com/v1/forecast"
GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"


class WeatherService:
    """封装天气获取与解析逻辑"""

    @staticmethod
    def get_weather_data(city: str, date_input: str = None) -> str:
        """
        获取天气 JSON 数据
        :param city: 城市名称
        :param date_input: 日期输入，可以是具体日期字符串，或者是相对今天的天数(如 0, 1, -1)
        :return: JSON 字符串
        """
        try:
            # 1. 地理编码
            geo_resp = requests.get(
                GEOCODING_URL,
                params={"name": city, "count": 1, "language": "zh", "format": "json"},
                timeout=5,
            )
            city_info = geo_resp.json().get("results", [{}])[0]
            if not city_info:
                return json.dumps({"error": "City not found"})

            # 2. 日期处理
            if date_input:
                try:
                    offset = int(date_input)
                    date_str = (datetime.now() + timedelta(days=offset)).strftime("%Y-%m-%d")
                except ValueError:
                    date_str = date_input
            else:
                date_str = datetime.now().strftime("%Y-%m-%d")

            # 3. 请求天气数据
            weather_resp = requests.get(
                WEATHER_API_URL,
                params={
                    "latitude": city_info["latitude"],
                    "longitude": city_info["longitude"],
                    "daily": "temperature_2m_max,temperature_2m_min,weather_code,precipitation_sum,wind_speed_10m_max",
                    "timezone": "auto",
                    "start_date": date_str,
                    "end_date": date_str,
                },
                timeout=5,
            )
            data = weather_resp.json()["daily"]
            idx = data["time"].index(date_str)

            return json.dumps({
                "city": city_info.get("name"),
                "date": date_str,
                "temp_max": data["temperature_2m_max"][idx],
                "temp_min": data["temperature_2m_min"][idx],
                "weather_code": data["weather_code"][idx],
                "precipitation": data["precipitation_sum"][idx],
                "wind_max": data["wind_speed_10m_max"][idx],
            }, ensure_ascii=False)

        except Exception as e:
            logging.error(f"Weather Service Error: {e}")
            return json.dumps({"error": str(e)})

    @staticmethod
    def format_weather_text(weather_json: str) -> str:
        """将天气 JSON 转换为自然语言描述"""
        try:
            data = json.loads(weather_json)
            if "error" in data:
                return f"Weather Error: {data['error']}"

            # 完整的天气代码映射表（基于 WMO Weather Interpretation Codes）
            weather_map = {
                # 晴天
                "0": "晴朗",
                "1": "大部晴",
                "2": "多云",
                "3": "阴天",
                # 雾
                "45": "雾天",
                "48": "雾凇",
                # 毛毛雨
                "51": "小毛毛雨",
                "53": "毛毛雨",
                "55": "大毛毛雨",
                "56": "小冻毛毛雨",
                "57": "冻毛毛雨",
                # 雨
                "61": "小雨",
                "63": "中雨",
                "65": "大雨",
                "66": "小冻雨",
                "67": "冻雨",
                # 雪和冰粒
                "71": "小雪",
                "73": "雪",
                "75": "大雪",
                "77": "雪粒",
                # 阵雨
                "80": "小阵雨",
                "81": "阵雨",
                "82": "大阵雨",
                "85": "小阵雪",
                "86": "阵雪",
                # 雷暴
                "95": "雷暴",
                "96": "轻雷暴伴冰雹",
                "99": "雷暴伴冰雹"
            }

            code = str(data.get("weather_code", 0))
            desc = weather_map.get(code, f"未知天气(code:{code})")

            return (
                f"【{data['city']} 天气报告】\n"
                f"日期: {data['date']}\n"
                f"天气: {desc}\n"
                f"温度: {data['temp_min']}°C ~ {data['temp_max']}°C\n"
                f"降水: {data['precipitation']}mm\n"
                f"风速: {data['wind_max']}km/h"
            )
        except Exception as e:
            return "Failed to parse weather data"


# --- 对外暴露的便捷函数 ---
def get_weather_report(city: str, date_input: str = None) -> str:
    """
    便捷接口：直接获取格式化后的天气文本
    类似于 send_result_to_server 的调用方式
    """
    try:
        json_str = WeatherService.get_weather_data(city, date_input)
        # 如果返回的是错误JSON，直接返回错误信息
        if '"error"' in json_str:
            return json_str
        return WeatherService.format_weather_text(json_str)
    except Exception as e:
        logging.error(f"Error in get_weather_report: {e}")
        return f"System Error: {e}"
