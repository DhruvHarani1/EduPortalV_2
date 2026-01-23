
import requests
import json

def test_rec():
    url = 'http://localhost:5001/api/student/club-recommendations'
    payload = {'interests': ['tech', 'coding']}
    
    try:
        print(f"Sending POST to {url} with {payload}")
        response = requests.post(url, json=payload)
        print(f"Status Code: {response.status_code}")
        print("Response Body:")
        print(response.text)
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    test_rec()
