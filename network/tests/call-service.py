#!/usr/bin/env python3
import requests
import sys
import json

SERVICE_URL = "http://localhost:8888/generate"

if len(sys.argv) < 2:
    print("Usage: python call_service.py <City>")
    sys.exit(1)

city = sys.argv[1]
payload = {"city": city}

try:
    resp = requests.post(SERVICE_URL, json=payload)
    print(f"Response: {resp.status_code} {resp.text}")
except Exception as e:
    print(f"Error: {e}")
