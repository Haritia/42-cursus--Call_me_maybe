#!/usr/bin/env python3
# ########################################################################### #
#   shebang: 1                                                                #
#                                                          :::      ::::::::  #
#   parser.py                                            :+:      :+:    :+:  #
#                                                      +:+ +:+         +:+    #
#   By: haranivo <haranivo@student.42antananarivo.   +#+  +:+       +#+       #
#                                                  +#+#+#+#+#+   +#+          #
#   Created: 2026/11/19 23:41:01 by haranivo            #+#    #+#            #
#   Updated: 2026/11/20 00:13:43 by haranivo           ###   ########.fr      #
#                                                                             #
# ########################################################################### #


"""Parsing JSON formated values, and limit as necessary."""


import json
import pydantic
from dataclasses import dataclass
from rich.console import Console, Group
from rich.theme import Theme
from rich.panel import Panel

custom_theme = Theme(
    {
        'error': 'bold red',
        'message': 'bold purple'
    }
)
console = Console(theme=custom_theme)

@dataclass
class Parser:
    """Configuration file jon formated input/output parser."""

    file: str
    with open(file, 'r') as f:
        for content in f:
            match content.startswith():
                case
