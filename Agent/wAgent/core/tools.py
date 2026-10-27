import os
import shutil
import json
import subprocess
import httpx
import trafilatura
from config import BAIDU_QIANFAN_API_KEY

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
    {"type": "function", "function": {"name": "searchWeb", "description": "通过百度千帆搜索互联网，获取最新信息。当用户提问涉及实时新闻、最新事件、最新数据或你不知道的信息时使用此工具。", "parameters": {"type": "object", "properties": {"query": {"type": "string", "description": "搜索关键词或问题"}}, "required": ["query"]}}},
    {"type": "function", "function": {"name": "fetchWeb", "description": "获取指定网页URL的主要内容，提取正文并转为Markdown格式。当需要阅读某个具体网页的详细内容时使用。", "parameters": {"type": "object", "properties": {"url": {"type": "string", "description": "网页完整URL地址"}}, "required": ["url"]}}},
    {"type": "function", "function": {"name": "RunCli", "description": "执行本地命令行程序（CLI）。接收程序名command和参数列表args，返回标准输出、标准错误和退出码。例如执行python脚本、git命令等。", "parameters": {"type": "object", "properties": {"command": {"type": "string", "description": "要执行的程序名，如 python、git 等"}, "args": {"type": "array", "items": {"type": "string"}, "description": "参数列表，每个参数是一个字符串"}}, "required": ["command", "args"]}}},
]


def search_web(query):
    if not BAIDU_QIANFAN_API_KEY:
        return "错误：未配置百度千帆 API Key，请在 config.ini 的 [search] 小节中填写 baidu_qianfan_api_key。"
    try:
        resp = httpx.post(
            "https://qianfan.baidubce.com/v2/ai_search/web_search",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {BAIDU_QIANFAN_API_KEY}",
            },
            json={
                "messages": [{"role": "user", "content": query}],
                "search_source": "baidu_search_v2",
                "resource_type_filter": [{"type": "web", "top_k": 5}],
            },
            timeout=30,
        )
        if resp.status_code != 200:
            return f"搜索API返回错误: HTTP {resp.status_code} - {resp.text[:200]}"
        data = resp.json()
        refs = (data.get("references")
                or data.get("search_info", {}).get("search_results")
                or data.get("search_results")
                or data.get("results")
                or [])
        if not refs:
            return "搜索完成，但没有找到相关结果。"
        lines = [f"搜索关键词: {query}\n"]
        for i, r in enumerate(refs, 1):
            title = r.get("title", "")
            url = r.get("url") or r.get("link", "")
            snippet = r.get("snippet") or r.get("content") or r.get("abstract", "")
            lines.append(f"{i}. {title}")
            lines.append(f"   URL: {url}")
            lines.append(f"   摘要: {snippet}\n")
        answer = data.get("content", [{}])[0].get("content") or data.get("answer") or data.get("summary")
        if answer:
            lines.append(f"AI总结: {answer}")
        return "\n".join(lines)
    except httpx.TimeoutException:
        return "搜索超时，请稍后重试。"
    except Exception as e:
        return f"搜索失败: {e}"


def fetch_web(url):
    try:
        result = subprocess.run(
            ["curl", "-sL", "--max-time", "20", url],
            capture_output=True, timeout=25,
        )
        if result.returncode != 0:
            return f"网页访问失败: curl返回码 {result.returncode}"
        html = result.stdout.decode("utf-8", errors="ignore")
        if not html.strip():
            return "网页内容为空。"
        text = trafilatura.extract(html, output_format="markdown", include_links=True, include_images=False)
        if not text:
            return "无法从该网页提取正文内容（可能是需要登录或JavaScript渲染的页面）。"
        if len(text) > 8000:
            text = text[:8000] + "\n...(内容过长，已截断)"
        return f"网页: {url}\n\n{text}"
    except subprocess.TimeoutExpired:
        return "网页访问超时（25秒）。"
    except Exception as e:
        return f"获取网页失败: {e}"


def run_cli(command, args):
    try:
        result = subprocess.run(
            [command] + args,
            capture_output=True, timeout=30,
            shell=False,
        )
        stdout = result.stdout.decode("utf-8", errors="ignore")
        stderr = result.stderr.decode("utf-8", errors="ignore")
        if len(stdout) > 4000:
            stdout = stdout[:4000] + "\n...(stdout过长，已截断)"
        if len(stderr) > 2000:
            stderr = stderr[:2000] + "\n...(stderr过长，已截断)"
        return f"退出码: {result.returncode}\n标准输出:\n{stdout}\n标准错误:\n{stderr}"
    except subprocess.TimeoutExpired:
        return "命令执行超时（30秒）。"
    except FileNotFoundError:
        return f"错误：找不到程序 '{command}'，请确认已安装。"
    except Exception as e:
        return f"命令执行失败: {e}"


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
        "searchWeb": lambda a: search_web(a.get("query", "")),
        "fetchWeb": lambda a: fetch_web(a.get("url", "")),
        "RunCli": lambda a: run_cli(a.get("command", ""), a.get("args", [])),
    }
    if name not in dispatch:
        return "未知工具"
    try:
        return dispatch[name](args)
    except Exception as e:
        return f"工具执行出错: {e}"
