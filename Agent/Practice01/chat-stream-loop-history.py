import httpx, json, sys

BASE_URL = "https://api.siliconflow.cn/v1"
API_KEY = "sk-igtalceyhffxixsnwpenwhwzligfonizdumwcmxxzenxwnjj"
MODEL = "Qwen/Qwen2.5-72B-Instruct"

messages = [{"role": "system", "content": "你是一个有帮助的助手。"}]

print("=== 对话开始（输入 Ctrl+C 退出）===")

while True:
    try:
        user_input = input("\n你: ").strip()
        if not user_input:
            continue
        messages.append({"role": "user", "content": user_input})
        with httpx.stream(
            "POST",
            f"{BASE_URL}/chat/completions",
            headers={"Authorization": f"Bearer {API_KEY}"},
            json={"model": MODEL, "messages": messages, "stream": True},
            timeout=60,
        ) as resp:
            print("AI: ", end="", flush=True)
            ai_reply = ""
            for line in resp.iter_lines():
                if not line or not line.startswith("data: "):
                    continue
                data = line[6:]
                if data == "[DONE]":
                    break
                chunk = json.loads(data)
                delta = chunk["choices"][0]["delta"].get("content", "")
                if delta:
                    print(delta, end="", flush=True)
                    ai_reply += delta
            print()
            messages.append({"role": "assistant", "content": ai_reply})
    except KeyboardInterrupt:
        print("\n=== 对话结束 ===")
        sys.exit(0)
    except Exception as e:
        print(f"\n出错了: {e}")
