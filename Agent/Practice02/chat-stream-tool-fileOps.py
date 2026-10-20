import httpx, json, os, shutil, sys

BASE_URL = "https://api.siliconflow.cn/v1"
API_KEY = "sk-igtalceyhffxixsnwpenwhwzligfonizdumwcmxxzenxwnjj"
MODEL = "Qwen/Qwen2.5-72B-Instruct"

TOOLS = [
    {"type": "function", "function": {"name": "getcwd", "description": "获取当前工作目录", "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "listdir", "description": "列出指定目录下所有文件和子目录", "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "filetype", "description": "获取指定文件的类型", "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "readfile", "description": "读取纯文本文件的内容", "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "createfile", "description": "创建新文件", "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "editfile", "description": "编辑纯文本文件内容", "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}, "required": ["path", "content"]}}},
    {"type": "function", "function": {"name": "mkdir", "description": "创建新目录", "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "rmdir", "description": "删除非空目录", "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "rmfile", "description": "删除文件", "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "rename", "description": "重命名文件或目录", "parameters": {"type": "object", "properties": {"old": {"type": "string"}, "new": {"type": "string"}}, "required": ["old", "new"]}}},
]

def getcwd(): return f"当前工作目录: {os.getcwd()}"
def listdir(path): return f"目录 {path} 下有:\n" + "\n".join(os.listdir(path))
def filetype(path):
    if os.path.isdir(path): return f"{path} 是目录"
    elif os.path.isfile(path): return f"{path} 是文件，扩展名: {os.path.splitext(path)[1]}"
    else: return f"{path} 不存在"
def readfile(path):
    with open(path, "r", encoding="utf-8") as f: return f"文件内容:\n{f.read()}"
def createfile(path, content=""):
    with open(path, "w", encoding="utf-8") as f: f.write(content)
    return f"已创建文件: {path}"
def editfile(path, content):
    with open(path, "w", encoding="utf-8") as f: f.write(content)
    return f"已更新文件: {path}"
def mkdir(path):
    os.makedirs(path, exist_ok=True); return f"已创建目录: {path}"
def rmdir(path):
    shutil.rmtree(path); return f"已删除目录: {path}"
def rmfile(path):
    os.remove(path); return f"已删除文件: {path}"
def rename(old, new):
    os.rename(old, new); return f"已将 {old} 重命名为 {new}"

def execute_tool(name, args):
    fns = {"getcwd": getcwd, "listdir": listdir, "filetype": filetype, "readfile": readfile,
           "createfile": createfile, "editfile": editfile, "mkdir": mkdir, "rmdir": rmdir,
           "rmfile": rmfile, "rename": rename}
    if name not in fns: return "未知工具"
    if name == "getcwd": return getcwd()
    if name == "rename": return rename(args.get("old",""), args.get("new",""))
    if name == "createfile": return createfile(args.get("path",""), args.get("content",""))
    if name == "editfile": return editfile(args.get("path",""), args.get("content",""))
    return fns[name](args.get("path",""))

def ask(messages):
    resp = httpx.post(f"{BASE_URL}/chat/completions",
        headers={"Authorization": f"Bearer {API_KEY}"},
        json={"model": MODEL, "messages": messages, "tools": TOOLS}, timeout=60)
    return resp.json()["choices"][0]["message"]

def ask_stream(messages):
    with httpx.stream("POST", f"{BASE_URL}/chat/completions",
        headers={"Authorization": f"Bearer {API_KEY}"},
        json={"model": MODEL, "messages": messages, "stream": True}, timeout=60) as resp:
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

messages = [{"role":"system","content":"你是文件管理助手。用户让你查看、创建、编辑、删除文件或目录时，调用对应工具。"}]
print("=== 文件管理助手（Ctrl+C 退出）===")

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
                result = execute_tool(name, args)
                print(f"[工具: {name} {args} -> {result}]")
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
