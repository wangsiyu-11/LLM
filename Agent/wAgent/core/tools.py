import os
import shutil

TOOLS_SCHEMA = [
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

def execute_tool(name, args):
    dispatch = {
        "getcwd": lambda a: f"当前工作目录: {os.getcwd()}",
        "listdir": lambda a: f"目录 {a.get('path','.')} 下有:\n" + "\n".join(os.listdir(a.get("path", "."))),
        "filetype": lambda a: (
            f"{a.get('path','')} 是目录" if os.path.isdir(a.get("path", ""))
            else f"{a.get('path','')} 是文件，扩展名: {os.path.splitext(a.get('path',''))[1]}"
            if os.path.isfile(a.get("path", ""))
            else f"{a.get('path','')} 不存在"
        ),
        "readfile": lambda a: open(a.get("path", ""), "r", encoding="utf-8").read(),
        "createfile": lambda a: (open(a.get("path", ""), "w", encoding="utf-8").write(a.get("content", "")), f"已创建文件: {a.get('path','')}")[1],
        "editfile": lambda a: (open(a.get("path", ""), "w", encoding="utf-8").write(a.get("content", "")), f"已更新文件: {a.get('path','')}")[1],
        "mkdir": lambda a: (os.makedirs(a.get("path", ""), exist_ok=True), f"已创建目录: {a.get('path','')}")[1],
        "rmdir": lambda a: (shutil.rmtree(a.get("path", "")), f"已删除目录: {a.get('path','')}")[1],
        "rmfile": lambda a: (os.remove(a.get("path", "")), f"已删除文件: {a.get('path','')}")[1],
        "rename": lambda a: (os.rename(a.get("old", ""), a.get("new", "")), f"已将 {a.get('old','')} 重命名为 {a.get('new','')}")[1],
    }
    if name not in dispatch:
        return "未知工具"
    try:
        return dispatch[name](args)
    except Exception as e:
        return f"工具执行出错: {e}"
