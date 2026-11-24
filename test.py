# from rich import print
# from rich.panel import Panel
# from rich.console import Console
# from rich import box

# print(Panel(
#     "Hello, World!",
#     box=box.ROUNDED,
#     title="My Panel",
#     title_align="left",
#     subtitle="footer text",
#     subtitle_align="right",
#     expand=False,
#     style="on purple",
#     border_style="bold red",
#     width=30,
#     height=5,
#     padding=(0, 0),
#     highlight=True,
# ))

# dico = {
#     'hello': 'world',
#     'fuck': 'you',
#     'beach': 'bitch'
# }
# console = Console()
# console.print(dico["beach"])

import json

data = {"name": "Alice", "active": True}

# Write Python object directly to a file
with open("data/outout/tia.txt", "w") as f:
    json.dump(data, f, indent=8)

# Read JSON file directly into a Python dictionary
with open("data/outout/tia.txt", "r") as f:
    loaded_data = json.load(f)

print(loaded_data["name"])



