import requests

url = "http://localhost:8002/generate"
payload = {
    "text": "넌 어떤 모델이니?",  # 여기에 질문!!
    "user_id": "test_user",
    "use_rag": False,
    "use_memory": False
}

response = requests.post(url, json=payload)
print(response.status_code)
print(response.json())
