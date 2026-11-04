from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Input, RichLog, Static
from core.agent import Agent


class ChatTUI(App):
    BINDINGS = [("ctrl+p", "palette", "palette")]

    def __init__(self):
        super().__init__()
        self.agent = Agent()

    def compose(self) -> ComposeResult:
        yield Header()
        self.status = Static("上下文: 0k/128k (默认) 0%")
        yield self.status
        self.chat_log = RichLog()
        yield self.chat_log
        yield Input(placeholder="输入消息，回车发送... /compact 压缩上下文", id="input")
        yield Footer()

    def on_mount(self):
        self.chat_log.write("=== wAgent 文件管理助手 ===")
        self._update_status()

    def _update_status(self):
        tokens, window, pct = self.agent.get_context_info()
        self.status.update(f"上下文: {tokens//1000}k/{window//1000}k (默认) {pct}%")

    def on_input_submitted(self, event: Input.Submitted):
        text = event.value.strip()
        if not text:
            return
        self.chat_log.write(f"你: {text}")
        self.query_one("#input", Input).value = ""
        try:
            reply = self.agent.chat(text)
            self.chat_log.write(f"AI: {reply}")
        except Exception as e:
            self.chat_log.write(f"出错: {e}")
        self._update_status()
def run():
    ChatTUI().run()
