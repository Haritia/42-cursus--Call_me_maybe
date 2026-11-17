#!/usr/bin/env python3
# ########################################################################### #
#   shebang: 1                                                                #
#                                                          :::      ::::::::  #
#   __main__.py                                          :+:      :+:    :+:  #
#                                                      +:+ +:+         +:+    #
#   By: haranivo <haranivo@student.42antananarivo.   +#+  +:+       +#+       #
#                                                  +#+#+#+#+#+   +#+          #
#   Created: 2026/11/17 08:58:40 by haranivo            #+#    #+#            #
#   Updated: 2026/11/17 10:38:28 by haranivo           ###   ########.fr      #
#                                                                             #
# ########################################################################### #


from sys import argv
from rich.console import Console, Group
from rich.theme import Theme
from rich.text import Text
from rich.panel import Panel

custom_theme = Theme(
    {
        'banner': 'bold italic medium_orchid'
    }
)
console = Console(theme=custom_theme)


def main():
    """
    uv run python -m src
    --functions_definition data/input/functions_definition.json
    --input data/input/function_calling_tests.json
    --output data/output/function_calls.json
    """
    if len(argv) < 2: # if there is no arguments
        func = "data/input/functions_definition.json"
        inp = "data/input/function_calling_tests.json"
        outp = "data/output/function_calls.json"

    banner = (
        "[banner] ██████╗ █████╗ ██╗     ██╗         ███╗   ███╗███████╗[/]"
        "[banner]    ███╗   ███╗ █████╗ ██╗   ██╗██████╗ ███████╗[/]\n"
        "[banner]██╔════╝██╔══██╗██║     ██║         ████╗ ████║██╔════╝[/]"
        "[banner]    ████╗ ████║██╔══██╗╚██╗ ██╔╝██╔══██╗██╔════╝[/]\n"
        "[banner]██║     ███████║██║     ██║         ██╔████╔██║█████╗  [/]"
        "[banner]    ██╔████╔██║███████║ ╚████╔╝ ██████╔╝█████╗  [/]\n"
        "[banner]██║     ██╔══██║██║     ██║         ██║╚██╔╝██║██╔══╝  [/]"
        "[banner]    ██║╚██╔╝██║██╔══██║  ╚██╔╝  ██╔══██╗██╔══╝  [/]\n"
        "[banner]╚██████╗██║  ██║███████╗███████╗    ██║ ╚═╝ ██║███████╗[/]"
        "[banner]    ██║ ╚═╝ ██║██║  ██║   ██║   ██████╔╝███████╗[/]\n"
        "[banner] ╚═════╝╚═╝  ╚═╝╚══════╝╚══════╝    ╚═╝     ╚═╝╚══════╝[/]"
        "[banner]    ╚═╝     ╚═╝╚═╝  ╚═╝   ╚═╝   ╚═════╝ ╚══════╝[/]"
        )

    bloc = Group(
        Panel(banner,
              expand=False,
              border_style="purple",
              padding=(1, 2))

    )

    console.print(bloc)

    

if __name__ == "__main__":
    main()
