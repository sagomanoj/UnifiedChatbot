import requests
import json

url = "http://127.0.0.1:8000/chat"
payload = {
    "query": "compare food delivery and ecommerce delivery fees",
    "app": "comparison"
}

try:
    print(f"Sending comparison query to {url}...")
    response = requests.post(url, json=payload, timeout=30)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
