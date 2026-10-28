import httpx
import json
from config import BASE_URL, API_KEY, MODEL
from core.tools import TOOLS_SCHEMA, execute_tool
from core.skills import load_skills


class LLMClient:
    def __init__(self):
        self.base_url = BASE_URL
        self.api_key = API_KEY
        self.model = MODEL

    def chat(self, messages):
        resp = httpx.post(
            f"{self.base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={"model": self.model, "messages": messages, "tools": TOOLS_SCHEMA},
            timeout=60,
        )
        return resp.json()["choices"][0]["message"]


class Agent:
    def __init__(self):
        self.llm = LLMClient()
        skills = load_skills()
        skill_text = ""
        if skills:
            skill_text = "\n\n你还掌握以下技能：\n"
            for s in skills:
                skill_text += f"- {s['name']}：{s['description']}\n"
        self.messages = [
            {"role": "system", "content": f"你是文件管理助手。用户让你查看、创建、编辑、删除文件或目录时，调用对应工具完成操作。{skill_text}"}
        ]

    def send(self, user_input):
        self.messages.append({"role": "user", "content": user_input})
        msg = self.llm.chat(self.messages)
        while msg.get("tool_calls"):
            for tc in msg["tool_calls"]:
                name = tc["function"]["name"]
                args = json.loads(tc["function"]["arguments"]) if tc["function"]["arguments"] else {}
                result = execute_tool(name, args)
                self.messages.append(msg)
                self.messages.append({"role": "tool", "tool_call_id": tc["id"], "content": result})
            msg = self.llm.chat(self.messages)
        reply = msg.get("content", "")
        self.messages.append({"role": "assistant", "content": reply})
        return reply
