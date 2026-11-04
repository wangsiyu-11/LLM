from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Input, RichLog, Static, SelectionList
from textual.containers import Horizontal, Vertical
from core.agent import Agent

COMMANDS = ["/compact", "/save", "/new", "/resume", "/quit", "/help"]


class ChatTUI(App):
    CSS = """
    Screen { background: #1e1e2e; }
    #sidebar { width: 24; background: #181825; padding: 1 1; }
    #sidebar .title { color: #6c7086; text-style: bold; margin-bottom: 1; }
    #sidebar .item { color: #cdd6f4; }
    #main { padding: 0 1; }
    #statusbar { color: #6c7086; padding: 0 1; }
    RichLog { background: #1e1e2e; color: #cdd6f4; }
    Input { background: #313244; color: #cdd6f4; }
    #cmdlist { display: none; background: #313244; height: auto; max-height: 6; }
    """

    BINDINGS = [("ctrl+p", "palette", "palette")]

    def __init__(self):
        super().__init__()
        self.agent = Agent()

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal():
            with Vertical(id="sidebar"):
                yield Static("wAgent", classes="title")
                self.mcp_status = Static("", classes="item")
                yield self.mcp_status
                yield Static("")
                yield Static("技能", classes="title")
                self.skill_status = Static("", classes="item")
                yield self.skill_status
            with Vertical(id="main"):
                self.status = Static("", id="statusbar")
                yield self.status
                self.chat_log = RichLog()
                yield self.chat_log
                self.cmdlist = SelectionList(id="cmdlist")
                yield self.cmdlist
                yield Input(placeholder="输入消息... /help", id="input")
        yield Footer()

    def on_mount(self):
        self.chat_log.write("=== wAgent ===")
        self._refresh()
        self.cmdlist.display = False

    def _refresh(self):
        tokens, window, pct = self.agent.get_context_info()
        self.status.update(f"  {tokens//1000}k / {window//1000}k  ·  {pct}%")
        from core.mcp import MCP_TOOLS_MAP
        servers = list(MCP_TOOLS_MAP.keys())
        self.mcp_status.update("\n".join([f"  ● {s}" for s in servers]) or "  无")
        from core.skills import load_skills
        skills = load_skills()
        self.skill_status.update("\n".join([f"  · {s['name']}" for s in skills]) or "  无")

    def on_input_changed(self, event: Input.Changed):
        val = event.value
        if not val.startswith("/"):
            self.cmdlist.display = False
            return
        self.cmdlist.clear_options()
        matches = [c for c in COMMANDS if c.startswith(val)]
        for cmd in matches:
            self.cmdlist.add_option((cmd, cmd))
        self.cmdlist.display = True

    def on_selection_list_selected(self, event):
        cmd = event.value
        self.query_one("#input", Input).value = cmd
        self.cmdlist.display = False
        self.query_one("#input", Input).focus()

    def on_input_submitted(self, event: Input.Submitted):
        text = event.value.strip()
        if not text:
            return
        self.cmdlist.display = False
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
