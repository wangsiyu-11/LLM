from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Input, RichLog
from core.agent import Agent


class ChatTUI(App):
    CSS = """
    Screen { layout: vertical; }
    #chat { height: 1fr; border: solid blue; padding: 1; }
    #input { height: 3; margin: 1; }
    """

    def __init__(self):
        super().__init__()
        self.agent = Agent()

    def compose(self) -> ComposeResult:
        yield Header()
        yield RichLog(id="chat", markup=True)
        yield Input(placeholder="输入消息，回车发送...", id="input")
        yield Footer()

    def on_mount(self):
        self.query_one("#input", Input).focus()
        self.query_one("#chat", RichLog).write("[bold cyan]=== wAgent 文件管理助手 ===[/bold cyan]")

    def on_input_submitted(self, event: Input.Submitted):
        text = event.value.strip()
        if not text:
            return
        chat = self.query_one("#chat", RichLog)
        chat.write(f"[bold green]你:[/bold green] {text}")
        self.query_one("#input", Input).value = ""
        try:
            reply = self.agent.send(text)
            chat.write(f"[bold magenta]AI:[/bold magenta] {reply}")
        except Exception as e:
            chat.write(f"[bold red]出错: {e}[/bold red]")


def run():
    app = ChatTUI()
    app.run()
