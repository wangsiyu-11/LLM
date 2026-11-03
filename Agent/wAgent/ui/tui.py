from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Input, RichLog
from core.agent import Agent


class ChatTUI(App):
    BINDINGS = [("ctrl+p", "palette", "palette")]

    def __init__(self):
        super().__init__()
        self.agent = Agent()

    def compose(self) -> ComposeResult:
        yield Header()
        self.chat_log = RichLog()
        yield self.chat_log
        yield Input(placeholder="输入消息，回车发送...", id="input")
        yield Footer()

    def on_mount(self):
        self.chat_log.write("=== wAgent 文件管理助手 ===")

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


def run():
    ChatTUI().run()
