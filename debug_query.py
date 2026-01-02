import requests
import json

url = "http://127.0.0.1:8000/chat"
payload = {
    "query": "how to order food",
    "app": "Food Delivery"
}

try:
    print(f"Sending query to {url}: {payload}")
    response = requests.post(url, json=payload, timeout=30)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
except Exception as e:
    print(f"Error: {e}")
