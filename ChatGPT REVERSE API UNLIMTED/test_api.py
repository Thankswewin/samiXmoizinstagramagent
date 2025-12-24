import requests

url = "http://localhost:6970/conversation"
data = {
    "proxy": "http://test:test@127.0.0.1:8080",
    "message": "Hello from API test"
}

response = requests.post(url, json=data)
print(response.json())