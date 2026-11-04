from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Input, RichLog, Static, Label
from textual.containers import Horizontal, Vertical
from core.agent import Agent


class ChatTUI(App):
    BINDINGS = [("ctrl+p", "palette", "palette")]

    def __init__(self):
        super().__init__()
        self.agent = Agent()

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal():
            with Vertical(id="sidebar"):
                yield Static("MCP 服务器", classes="sidebar-title")
                self.mcp_status = Static("加载中...")
                yield self.mcp_status
                yield Static("")
                yield Static("技能", classes="sidebar-title")
                self.skill_status = Static("")
                yield self.skill_status
            with Vertical():
                self.status = Static("")
                yield self.status
                self.chat_log = RichLog()
                yield self.chat_log
                yield Input(placeholder="/compact /save /new /resume /quit", id="input")
        yield Footer()

    def on_mount(self):
        self.chat_log.write("=== wAgent ===")
        self._refresh()

    def _refresh(self):
        tokens, window, pct = self.agent.get_context_info()
        self.status.update(f"上下文: {tokens//1000}k/{window//1000}k {pct}%")
        mcp_servers = self.agent.get_mcp_info()
        if mcp_servers:
            self.mcp_status.update("\n".join([f"✅ {s}" for s in mcp_servers]))
        else:
            self.mcp_status.update("无")
        from core.skills import load_skills
        skills = load_skills()
        self.skill_status.update("\n".join([f"- {s['name']}" for s in skills]))

    def on_input_submitted(self, event: Input.Submitted):
        text = event.value.strip()
        if not text:
            return
        self.chat_log.write(f"你: {text}")
        self.query_one("#input", Input).value = ""
        if text == "/quit":
            self.agent.chat(text)
            self.exit()
            return
        try:
            reply = self.agent.chat(text)
            self.chat_log.write(f"AI: {reply}")
        except Exception as e:
            self.chat_log.write(f"出错: {e}")
        self._refresh()


def run():
    ChatTUI().run()
