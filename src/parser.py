#!/usr/bin/env python3
# ########################################################################### #
#   shebang: 1                                                                #
#                                                          :::      ::::::::  #
#   parser.py                                            :+:      :+:    :+:  #
#                                                      +:+ +:+         +:+    #
#   By: haranivo <haranivo@student.42antananarivo.   +#+  +:+       +#+       #
#                                                  +#+#+#+#+#+   +#+          #
#   Created: 2026/11/19 23:41:01 by haranivo            #+#    #+#            #
#   Updated: 2026/11/28 07:50:16 by haranivo           ###   ########.fr      #
#                                                                             #
# ########################################################################### #


"""Parsing JSON formated values, and limit as necessary."""


import json
from rich.theme import Theme
from rich.console import Console
from pydantic import BaseModel, ConfigDict, ValidationError
from collections.abc import Iterable
from typing import Any, Literal
from dataclasses import dataclass


custom_theme = Theme(
    {
        'error': 'bold red',
        'message': 'italic red',
        'details': "purple"
    }
)

console = Console(theme=custom_theme)

Types = Literal["string", "number", "boolean", "list", "dict", "None"]


class Arguments(BaseModel):
    """Arguments model."""

    model_config = ConfigDict(extra='forbid', strict=True)
    type: Types
    value: Any = None

    def model_post_init(self, __context):
        """Type casting value if exist."""
        match self.type:
            case "string" if self.value is not None:
                self.value = str(self.value)
            case "number" if self.value is not None:
                self.value = float(self.value)


class Function_def(BaseModel):
    """Function definition model."""

    model_config = ConfigDict(extra='forbid', strict=True)
    name: str
    description: str
    parameters: dict[str, Arguments]
    returns: Arguments | None


class Prompt(BaseModel):
    """Prompt model."""

    model_config = ConfigDict(extra='forbid', strict=True)
    prompt: str


@dataclass
class ParseError(Exception):
    """Customize error for parsing."""

    model_config = ConfigDict(extra='forbid', strict=True)
    message: str
    details: str = ""

    def __post_init__(self) -> None:
        """Parse error output format."""
        if self.details:
            self.ferror = (
                f"[error]Oops error[/]: [message]{self.message}[/]"
                f"\n\n[details]=> {self.details}[/]"
            )
        else:
            self.ferror = f"[error]Oops error[/]: [message]{self.message}[/]"
        super().__init__(self.ferror)


class Loading:
    """Load the need json formated file."""

    @staticmethod
    def loads_functions(path) -> list[Function_def]:
        """Load the function definition and assign an object."""
        funcs: list = []
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except FileNotFoundError:
            raise ParseError(f"The function file '{path}' do not exist sorry.")
        except PermissionError:
            raise ParseError("No permission to touch that file.")
        except (UnicodeDecodeError, json.JSONDecodeError) as e:
            raise ParseError("Decode", f"{e}")
        if isinstance(data, Iterable):
            for d in data:
                funcs.append(Function_def.model_validate(d))
        else:
            funcs.append(Function_def.model_validate(d))
        return funcs

    @staticmethod
    def loads_prompt(path) -> list[Prompt]:
        """Load the prompt configuration file needed."""
        prompts: list = []
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except FileNotFoundError:
            raise ParseError(f"The prompt file '{path}' do not exist sorry.")
        except PermissionError:
            raise ParseError("No permission to touch that file.")
        except (UnicodeDecodeError, json.JSONDecodeError) as e:
            raise ParseError("Decode", f"{e}")
        if isinstance(data, Iterable):
            for d in data:
                prompts.append(Prompt.model_validate(d))
        else:
            prompts.append(Prompt.model_validate(d))
        return prompts
