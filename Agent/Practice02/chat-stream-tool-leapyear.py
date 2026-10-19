import httpx, json, subprocess, sys

BASE_URL = "https://api.siliconflow.cn/v1"
API_KEY = "sk-igtalceyhffxixsnwpenwhwzligfonizdumwcmxxzenxwnjj"
MODEL = "Qwen/Qwen2.5-72B-Instruct"

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "getDate",
            "description": "获取当前电脑的日期和时间",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "isLeapYear",
            "description": "计算输入的年份是否是闰年",
            "parameters": {
                "type": "object",
                "properties": {
                    "year": {"type": "integer", "description": "要判断的年份，比如 2024"}
                },
                "required": ["year"],
            },
        },
    },
]

def getDate():
    d = subprocess.check_output("date /t", shell=True, text=True).strip()
    t = subprocess.check_output("time /t", shell=True, text=True).strip()
    return f"当前日期: {d}，当前时间: {t}"

def isLeapYear(year):
    if (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0):
        return f"{year} 年是闰年"
    else:
        return f"{year} 年不是闰年"

def ask(messages):
    resp = httpx.post(f"{BASE_URL}/chat/completions",
        headers={"Authorization": f"Bearer {API_KEY}"},
        json={"model": MODEL, "messages": messages, "tools": TOOLS},
        timeout=60)
    return resp.json()["choices"][0]["message"]

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

messages = [{"role":"system","content":"你是一个有帮助的助手。问日期时间调用 getDate，问某年是否闰年调用 isLeapYear。"}]
print("=== 对话开始（Ctrl+C 退出）===")

while True:
    try:
        user = input("\n你: ").strip()
        if not user: continue
        messages.append({"role":"user","content":user})
        msg = ask(messages)
        if msg.get("tool_calls"):
            for tc in msg["tool_calls"]:
                name = tc["function"]["name"]
                args = json.loads(tc["function"]["arguments"]) if tc["function"]["arguments"] else {}
                if name == "getDate":
                    result = getDate()
                elif name == "isLeapYear":
                    result = isLeapYear(args.get("year", 0))
                else:
                    result = "未知工具"
                print(f"[调用工具: {name} {args} -> {result}]")
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
