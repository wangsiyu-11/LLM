from openai import OpenAI
from config import BASE_URL, API_KEY, MODEL
from core.tools import TOOLS_SCHEMA, execute_tool
from core.skills import load_skills
from core.mcp import connect_mcp_servers, get_mcp_tools_schema, call_mcp_tool
import json

client = OpenAI(base_url=BASE_URL, api_key=API_KEY)


class Agent:
    def __init__(self):
        self.messages = []
        connect_mcp_servers()
        skills = load_skills()
        skill_list = "\n".join([f"- `{s['name']}`: {s['description']}" for s in skills])
        self.tools = TOOLS_SCHEMA + get_mcp_tools_schema()
        self.system_prompt = f"""你是一个文件管理助手。
你有以下技能：
{skill_list}
使用 loadSkill 工具加载技能完整内容。
"""

    def chat(self, user_input):
        self.messages.append({"role": "user", "content": user_input})
        while True:
            resp = client.chat.completions.create(
                model=MODEL,
                messages=[{"role": "system", "content": self.system_prompt}] + self.messages,
                tools=self.tools,
                tool_choice="auto",
            )
            msg = resp.choices[0].message
            if not msg.tool_calls:
                self.messages.append({"role": "assistant", "content": msg.content})
                return msg.content
            self.messages.append({"role": "assistant", "content": msg.content or "", "tool_calls": [
                {"id": tc.id, "type": "function", "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
                for tc in msg.tool_calls
            ]})
            for tc in msg.tool_calls:
                args = json.loads(tc.function.arguments)
                if "__" in tc.function.name:
                    result = call_mcp_tool(tc.function.name, args)
                else:
                    result = execute_tool(tc.function.name, args)
                self.messages.append({"role": "tool", "tool_call_id": tc.id, "content": str(result)})
