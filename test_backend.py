import time
import requests
import os

BASE_URL = "http://localhost:8000"

def wait_for_server():
    print("Waiting for server...")
    for _ in range(30):
        try:
            response = requests.get(BASE_URL + "/")
            if response.status_code == 200:
                print("Server is up!")
                return True
        except requests.exceptions.ConnectionError:
            pass
        time.sleep(1)
    return False

def test_upload():
    print("Testing Upload...")
    # Create dummy file
    with open("ZomatoManual.txt", "w") as f:
        f.write("Zomato Refund Policy: Refunds are processed within 5-7 business days. No refunds on delivered food unless spoiled.")
    
    files = {'file': open("ZomatoManual.txt", 'rb')}
    response = requests.post(f"{BASE_URL}/upload/Food Delivery", files=files)
    print(f"Upload Status: {response.status_code}")
    print(f"Upload Response: {response.json()}")
    files['file'].close()
    os.remove("ZomatoManual.txt")

def test_query():
    print("Testing Query...")
    payload = {
        "query": "What is the refund policy?",
        "app": "Food Delivery"
    }
    response = requests.post(f"{BASE_URL}/chat", json=payload)
    print(f"Query Status: {response.status_code}")
    print(f"Query Response: {response.json()}")

def test_cross_app_isolation():
    print("Testing Isolation (Travel app asking about food refunds)...")
    payload = {
        "query": "What is the refund policy?",
        "app": "Travel Booking"
    }
    response = requests.post(f"{BASE_URL}/chat", json=payload)
    print(f"Isolation Query Response: {response.json()}")

if __name__ == "__main__":
    if wait_for_server():
        test_upload()
        time.sleep(2) # Allow ingestion
        test_query()
        test_cross_app_isolation()
    else:
        print("Server failed to start.")
