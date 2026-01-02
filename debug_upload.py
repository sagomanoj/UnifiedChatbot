import requests

try:
    with open("debug_test.txt", "w") as f:
        f.write("Test content")

    files = {'file': open("debug_test.txt", 'rb')}
    print("Sending request...")
    response = requests.post("http://127.0.0.1:8000/upload/Food%20Delivery", files=files, timeout=10)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")

except Exception as e:
    print(f"Request failed: {e}")
