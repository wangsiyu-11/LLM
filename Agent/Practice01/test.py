import httpx, json

BASE_URL = "https://api.siliconflow.cn/v1"
API_KEY = "sk-igtalceyhffxixsnwpenwhwzligfonizdumwcmxxzenxwnjj"
MODEL = "Qwen/Qwen2.5-72B-Instruct"

resp = httpx.post(
    f"{BASE_URL}/chat/completions",
    headers={"Authorization": f"Bearer {API_KEY}"},
    json={"model": MODEL, "messages": [{"role":"user","content":"你好"}], "stream": False},
    timeout=30,
)
print(resp.status_code)
print(resp.text[:500])
