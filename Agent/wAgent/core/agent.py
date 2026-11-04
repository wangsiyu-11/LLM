from openai import OpenAI
from config import BASE_URL, API_KEY, MODEL, CONTEXT_WINDOW
from core.tools import TOOLS_SCHEMA, execute_tool
from core.skills import load_skills
from core.mcp import connect_mcp_servers, get_mcp_tools_schema, call_mcp_tool
import json
import os
from datetime import datetime

client = OpenAI(base_url=BASE_URL, api_key=API_KEY)

SESSION_DIR = os.path.join(os.getcwd(), ".agents", "sessions")


class Agent:
    def __init__(self):
        self.messages = []
        self.last_tokens = 0
        self.blocked = False
        self.session_id = datetime.now().strftime("%Y%m%d-%H%M%S")
        self._load_agents_md()
        connect_mcp_servers()
        skills = load_skills()
        skill_list = "\n".join([f"- `{s['name']}`: {s['description']}" for s in skills])
        recall_schema = {
            "type": "function",
            "function": {
                "name": "recallContext",
                "description": "检索之前压缩保存的历史上下文归档。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "text": {"type": "string"},
                        "id": {"type": "string"}
                    },
                    "required": ["text"]
                }
            }
        }
        self.tools = TOOLS_SCHEMA + get_mcp_tools_schema() + [recall_schema]
        self.system_prompt = f"""你是一个文件管理助手。
你有以下技能：
{skill_list}
使用 loadSkill 工具加载技能完整内容。
如果需要查找历史对话中的细节，使用 recallContext 工具检索归档。
"""

    def _load_agents_md(self):
        path = os.path.join(os.getcwd(), "AGENTS.md")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            self.messages.append({"role": "system", "content": f"[AGENTS.md]\n{content}"})

    def _count_tokens(self):
        total = 0
        for m in self.messages:
            content = m.get("content", "") or ""
            total += len(content) // 2
        return len(self.system_prompt) // 2 + len(json.dumps(self.tools)) // 4 + total

    def get_context_info(self):
        tokens = self._count_tokens()
        pct = min(100, tokens * 100 // CONTEXT_WINDOW)
        return tokens, CONTEXT_WINDOW, pct

    def get_mcp_info(self):
        from core.mcp import MCP_TOOLS_MAP
        result = []
        for name in MCP_TOOLS_MAP:
            result.append(name)
        return result

    def chat(self, user_input):
        if user_input.strip().startswith("/"):
            return self._slash(user_input.strip())
        if self.blocked:
            return "上下文已达80%，请输入 /compact。"
        self.messages.append({"role": "user", "content": user_input})
        while True:
            resp = client.chat.completions.create(
                model=MODEL,
                messages=[{"role": "system", "content": self.system_prompt}] + self.messages,
                tools=self.tools,
                tool_choice="auto",
            )
            if resp.usage:
                self.last_tokens = resp.usage.total_tokens
            msg = resp.choices[0].message
            if not msg.tool_calls:
                self.messages.append({"role": "assistant", "content": msg.content})
                break
            self.messages.append({"role": "assistant", "content": msg.content or "", "tool_calls": [
                {"id": tc.id, "type": "function", "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
                for tc in msg.tool_calls
            ]})
            for tc in msg.tool_calls:
                args = json.loads(tc.function.arguments)
                if tc.function.name == "recallContext":
                    result = self._recall(args.get("text", ""), args.get("id"))
                elif "__" in tc.function.name:
                    result = call_mcp_tool(tc.function.name, args)
                else:
                    result = execute_tool(tc.function.name, args)
                self.messages.append({"role": "tool", "tool_call_id": tc.id, "content": str(result)})
        tokens, window, pct = self.get_context_info()
        if pct >= 80:
            self.blocked = True
            return f"{self.messages[-1]['content']}\n\n⚠️ 上下文 {pct}%，请 /compact。"
        return self.messages[-1].get("content", "")

    def _slash(self, cmd):
        if cmd == "/compact":
            return self._compact()
        elif cmd == "/save":
            return self._save()
        elif cmd == "/new":
            self._save()
            self.messages = []
            self.blocked = False
            self.session_id = datetime.now().strftime("%Y%m%d-%H%M%S")
            self._load_agents_md()
            return "新会话已创建。"
        elif cmd == "/quit":
            self._save()
            return "GOODBYE"
        elif cmd == "/help":
            return "/compact 压缩上下文\n/save 保存会话\n/new 新建会话\n/resume 恢复历史会话\n/quit 退出\n/help 帮助"
        elif cmd == "/resume":
            return self._list_sessions()
        return f"未知命令: {cmd}"

    def _save(self):
        os.makedirs(SESSION_DIR, exist_ok=True)
        path = os.path.join(SESSION_DIR, f"{self.session_id}.jsonl")
        with open(path, "w", encoding="utf-8") as f:
            for m in self.messages:
                f.write(json.dumps(m, ensure_ascii=False) + "\n")
        return f"会话已保存: {self.session_id}"

    def _list_sessions(self):
        if not os.path.exists(SESSION_DIR):
            return "没有历史会话。"
        files = sorted(os.listdir(SESSION_DIR), reverse=True)
        return "历史会话:\n" + "\n".join([f"  {f.replace('.jsonl','')}" for f in files[:10]])

    def _recall(self, text, archive_id=None):
        ctx_dir = os.path.join(os.getcwd(), ".agents", "context")
        if not os.path.exists(ctx_dir):
            return "没有归档。"
        results = []
        files = [f for f in os.listdir(ctx_dir) if f.endswith(".jsonl")]
        if archive_id:
            files = [f for f in files if archive_id in f]
        for fname in files:
            with open(os.path.join(ctx_dir, fname), "r", encoding="utf-8") as f:
                for i, line in enumerate(f):
                    if text in line:
                        results.append(f"[{fname}行{i}] {line[:300]}")
                        if len(results) >= 5:
                            break
        return "\n".join(results) if results else f"未找到 '{text}'"

    def _compact(self):
        now = datetime.now()
        archive_id = now.strftime("%Y%m%d-%H%M%S")
        ctx_dir = os.path.join(os.getcwd(), ".agents", "context")
        os.makedirs(ctx_dir, exist_ok=True)
        with open(os.path.join(ctx_dir, f"{archive_id}.jsonl"), "w", encoding="utf-8") as f:
            for m in self.messages:
                f.write(json.dumps(m, ensure_ascii=False) + "\n")
        prompt = f"""你是上下文管理助手。将以下对话压缩为约5000字的Markdown摘要，保留：用户目标、已完成工作、当前状态、关键文件路径/命令/配置、下一步任务。
历史对话：
{json.dumps(self.messages, ensure_ascii=False)}"""
        resp = client.chat.completions.create(model=MODEL, messages=[{"role": "user", "content": prompt}])
        summary = resp.choices[0].message.content
        note = f"\n\n> 上下文已于 {now} 压缩，归档编号 {archive_id}，用 recallContext 检索。"
        self.messages = [{"role": "assistant", "content": summary + note}]
        self.blocked = False
        return f"✅ 压缩完成！归档: {archive_id}"
