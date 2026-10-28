import os
import shutil
import json
import subprocess
import httpx
import trafilatura
import glob
from config import BAIDU_QIANFAN_API_KEY
from core.skills import load_skills, get_skill_content

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
    {"type": "function", "function": {"name": "searchWeb", "description": "通过百度千帆搜索互联网，获取最新信息。", "parameters": {"type": "object", "properties": {"query": {"type": "string", "description": "搜索关键词"}}, "required": ["query"]}}},
    {"type": "function", "function": {"name": "fetchWeb", "description": "获取指定网页URL的主要内容。", "parameters": {"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]}}},
    {"type": "function", "function": {"name": "RunCli", "description": "执行本地命令行程序。", "parameters": {"type": "object", "properties": {"command": {"type": "string"}, "args": {"type": "array", "items": {"type": "string"}}}}, "required": ["command", "args"]}},
    {"type": "function", "function": {"name": "loadSkill", "description": "加载指定技能的完整说明文档。", "parameters": {"type": "object", "properties": {"name": {"type": "string", "description": "技能名称"}, "filename": {"type": "string", "description": "可选，附加文件路径或名称"}}, "required": ["name"]}},
]


def search_web(query):
    if not BAIDU_QIANFAN_API_KEY:
        return "错误：未配置百度千帆 API Key。"
    try:
        resp = httpx.post("https://qianfan.baidubce.com/v2/ai_search/web_search",
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {BAIDU_QIANFAN_API_KEY}"},
            json={"messages": [{"role": "user", "content": query}], "search_source": "baidu_search_v2", "resource_type_filter": [{"type": "web", "top_k": 5}]}, timeout=30)
        if resp.status_code != 200:
            return f"搜索API错误: HTTP {resp.status_code}"
        data = resp.json()
        refs = data.get("references") or data.get("search_results") or []
        lines = [f"搜索: {query}\n"]
        for i, r in enumerate(refs, 1):
            lines.append(f"{i}. {r.get('title','')}\n   {r.get('url','')}\n   {r.get('snippet','') or r.get('abstract','')}\n")
        return "\n".join(lines)
    except Exception as e:
        return f"搜索失败: {e}"


def fetch_web(url):
    try:
        result = subprocess.run(["curl", "-sL", "--max-time", "20", url], capture_output=True, timeout=25)
        html = result.stdout.decode("utf-8", errors="ignore")
        text = trafilatura.extract(html, output_format="markdown", include_links=True)
        if not text:
            return "无法提取正文内容。"
        if len(text) > 8000:
            text = text[:8000] + "\n...(已截断)"
        return f"网页: {url}\n\n{text}"
    except Exception as e:
        return f"获取网页失败: {e}"


def run_cli(command, args):
    try:
        result = subprocess.run([command] + args, capture_output=True, timeout=30, shell=False)
        stdout = result.stdout.decode("utf-8", errors="ignore")
        stderr = result.stderr.decode("utf-8", errors="ignore")
        if len(stdout) > 4000:
            stdout = stdout[:4000] + "\n...(已截断)"
        return f"退出码: {result.returncode}\n输出:\n{stdout}\n错误:\n{stderr}"
    except Exception as e:
        return f"命令执行失败: {e}"


def load_skill(name, filename=None):
    skills = load_skills()
    for s in skills:
        if s["name"] == name:
            if filename:
                skill_dir = os.path.dirname(s["path"])
                matches = glob.glob(os.path.join(skill_dir, "**", filename), recursive=True)
                if len(matches) == 1:
                    with open(matches[0], "r", encoding="utf-8") as f:
                        return f.read()
                elif len(matches) > 1:
                    return f"找到多个文件: {matches}，请指定完整路径。"
                return f"未找到文件: {filename}"
            return get_skill_content(s["path"])
    return f"未找到技能: {name}，可用: {[s['name'] for s in skills]}"


def execute_tool(name, args):
    dispatch = {
        "getcwd": lambda a: f"当前目录: {os.getcwd()}",
        "listdir": lambda a: "\n".join(os.listdir(a.get("path", "."))),
        "filetype": lambda a: "目录" if os.path.isdir(a.get("path","")) else "文件",
        "readfile": lambda a: open(a.get("path", ""), "r", encoding="utf-8").read(),
        "createfile": lambda a: (open(a.get("path", ""), "w", encoding="utf-8").write(a.get("content", "")), f"已创建: {a.get('path','')}")[1],
        "editfile": lambda a: (open(a.get("path", ""), "w", encoding="utf-8").write(a.get("content", "")), f"已更新: {a.get('path','')}")[1],
        "mkdir": lambda a: (os.makedirs(a.get("path", ""), exist_ok=True), f"已创建目录: {a.get('path','')}")[1],
        "rmdir": lambda a: (shutil.rmtree(a.get("path", "")), f"已删除: {a.get('path','')}")[1],
        "rmfile": lambda a: (os.remove(a.get("path", "")), f"已删除: {a.get('path','')}")[1],
        "rename": lambda a: (os.rename(a.get("old", ""), a.get("new", "")), "已重命名")[1],
        "searchWeb": lambda a: search_web(a.get("query", "")),
        "fetchWeb": lambda a: fetch_web(a.get("url", "")),
        "RunCli": lambda a: run_cli(a.get("command", ""), a.get("args", [])),
        "loadSkill": lambda a: load_skill(a.get("name", ""), a.get("filename")),
    }
    if name not in dispatch:
        return "未知工具"
    try:
        return dispatch[name](args)
    except Exception as e:
        return f"出错: {e}"
