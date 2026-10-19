import httpx, json, subprocess, sys

BASE_URL = "https://api.siliconflow.cn/v1"
API_KEY = "sk-igtalceyhffxixsnwpenwhwzligfonizdumwcmxxzenxwnjj"
MODEL = "Qwen/Qwen2.5-72B-Instruct"

TOOLS = [{
    "type": "function",
    "function": {
        "name": "getDate",
        "description": "获取当前电脑的日期和时间",
        "parameters": {"type": "object", "properties": {}},
    },
}]

def getDate():
    d = subprocess.check_output("date /t", shell=True, text=True).strip()
    t = subprocess.check_output("time /t", shell=True, text=True).strip()
    return f"当前日期: {d}，当前时间: {t}"

def ask(messages):
    resp = httpx.post(f"{BASE_URL}/chat/completions",
        headers={"Authorization": f"Bearer {API_KEY}"},
        json={"model": MODEL, "messages": messages, "tools": TOOLS},
        timeout=60)
    data = resp.json()
    msg = data["choices"][0]["message"]
    return msg

def ask_stream(messages):
    with httpx.stream("POST", f"{BASE_URL}/chat/completions",
        headers={"Authorization": f"Bearer {API_KEY}"},
        json={"model": MODEL, "messages": messages, "stream": True},
        timeout=60) as resp:
        ai = ""
        print("AI: ", end="", flush=True)
        for line in resp.iter_lines():
            if not line or not line.startswith("data: "): continue
            data = line[6:]
            if data == "[DONE]": break
            chunk = json.loads(data)
            d = chunk["choices"][0]["delta"].get("content","")
            if d: print(d, end="", flush=True); ai += d
        print()
        return ai

messages = [{"role":"system","content":"你是一个有帮助的助手。当用户问日期或时间时，必须调用 getDate 工具。"}]
print("=== 对话开始（Ctrl+C 退出）===")

while True:
    try:
        user = input("\n你: ").strip()
        if not user: continue
        messages.append({"role":"user","content":user})
        msg = ask(messages)
        if msg.get("tool_calls"):
            for tc in msg["tool_calls"]:
                result = getDate()
                print(f"[调用工具: {tc['function']['name']} -> {result}]")
                messages.append(msg)
                messages.append({"role":"tool","tool_call_id":tc["id"],"content":result})
            ai = ask_stream(messages)
            messages.append({"role":"assistant","content":ai})
        else:
            ai = msg.get("content","")
            print(f"AI: {ai}")
            messages.append({"role":"assistant","content":ai})
    except KeyboardInterrupt:
        print("\n=== 结束 ==="); sys.exit(0)
    except Exception as e:
        print(f"\n出错了: {e}")
