from openai import OpenAI
from config import BASE_URL, API_KEY, MODEL
from core.tools import TOOLS_SCHEMA, execute_tool
from core.skills import load_skills
from core.mcp import connect_mcp_servers, get_mcp_tools_schema, call_mcp_tool
import json
import os
from datetime import datetime

client = OpenAI(base_url=BASE_URL, api_key=API_KEY)

CONTEXT_WINDOW = 128000


class Agent:
    def __init__(self):
        self.messages = []
        self.last_tokens = 0
        self.blocked = False
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
                        "text": {"type": "string", "description": "要查找的关键词"},
                        "id": {"type": "string", "description": "可选，归档编号"}
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

    def _count_tokens(self):
        total = 0
        for m in self.messages:
            content = m.get("content", "") or ""
            total += len(content) // 2
        sys_len = len(self.system_prompt) // 2
        tool_len = len(json.dumps(self.tools)) // 4
        return sys_len + tool_len + total

    def get_context_info(self):
        tokens = self._count_tokens()
        pct = min(100, tokens * 100 // CONTEXT_WINDOW)
        return tokens, CONTEXT_WINDOW, pct

    def chat(self, user_input):
        if user_input.strip() == "/compact":
            return self._compact()
        if self.blocked:
            return "上下文已达到80%阈值，请先输入 /compact 压缩。"
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
            return f"{self.messages[-1]['content']}\n\n⚠️ 上下文已使用 {pct}%，请输入 /compact 压缩。"
        return self.messages[-1].get("content", "")

    def _recall(self, text, archive_id=None):
        ctx_dir = os.path.join(os.getcwd(), ".agents", "context")
        if not os.path.exists(ctx_dir):
            return "没有历史归档。"
        results = []
        files = [f for f in os.listdir(ctx_dir) if f.endswith(".jsonl")]
        if archive_id:
            files = [f for f in files if archive_id in f]
        for fname in files:
            fpath = os.path.join(ctx_dir, fname)
            with open(fpath, "r", encoding="utf-8") as f:
                for i, line in enumerate(f):
                    if text in line:
                        results.append(f"[{fname} 行{i}] {line[:300]}")
                        if len(results) >= 5:
                            break
        if not results:
            return f"未找到包含 '{text}' 的归档。"
        return "\n---\n".join(results)

    def _compact(self):
        now = datetime.now()
        archive_id = now.strftime("%Y%m%d-%H%M%S")
        ctx_dir = os.path.join(os.getcwd(), ".agents", "context")
        os.makedirs(ctx_dir, exist_ok=True)
        archive_path = os.path.join(ctx_dir, f"{archive_id}.jsonl")
        with open(archive_path, "w", encoding="utf-8") as f:
            for m in self.messages:
                f.write(json.dumps(m, ensure_ascii=False) + "\n")
        compress_prompt = f"""你是一名 AI Agent 的上下文管理助手。当前会话即将达到上下文窗口限制，需要将历史对话压缩为一份高质量的工作摘要。
请认真阅读提供的历史上下文，提取对后续工作仍然有价值的信息，生成一份约5000 Tokens的Markdown摘要。
重点保留：用户目标、已完成工作、当前状态、关键技术信息（文件路径/函数名/配置/命令）、关键决策、下一步任务。
删除寒暄、重复、过时内容。不要把计划写成已完成。

历史对话：
{json.dumps(self.messages, ensure_ascii=False, indent=2)}"""
        resp = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": compress_prompt}],
        )
        summary = resp.choices[0].message.content
        note = f"\n\n> 此前上下文已于 {now.strftime('%Y-%m-%d %H:%M:%S')} 完成压缩，原始上下文保存在编号为 {archive_id} 的归档文件中。如需查找历史信息，请使用 recallContext 工具。"
        self.messages = [{"role": "assistant", "content": summary + note}]
        self.blocked = False
        return f"✅ 上下文压缩完成！归档编号: {archive_id}\n摘要已生成，继续对话吧。"
