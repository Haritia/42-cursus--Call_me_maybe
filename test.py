from rich import print
from rich.panel import Panel
from rich import box

print(Panel(
    "Hello, World!",
    box=box.ROUNDED,
    title="My Panel",
    title_align="left",
    subtitle="footer text",
    subtitle_align="right",
    expand=False,
    style="on purple",
    border_style="bold red",
    width=30,
    height=5,
    padding=(0, 0),
    highlight=True,
))   