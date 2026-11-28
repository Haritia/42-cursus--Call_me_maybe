#!/usr/bin/env python3
# ########################################################################### #
#   shebang: 1                                                                #
#                                                          :::      ::::::::  #
#   exercice4.py                                         :+:      :+:    :+:  #
#                                                      +:+ +:+         +:+    #
#   By: haranivo <haranivo@student.42antananarivo.   +#+  +:+       +#+       #
#                                                  +#+#+#+#+#+   +#+          #
#   Created: 2026/11/27 23:24:07 by haranivo            #+#    #+#            #
#   Updated: 2026/11/28 07:11:13 by haranivo           ###   ########.fr      #
#                                                                             #
# ########################################################################### #


import sys
import json
from rich.theme import Theme
from rich.console import Console
from pydantic import BaseModel, ConfigDict, ValidationError
from collections.abc import Iterable
from typing import Any, Literal
from dataclasses import dataclass
import argparse


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


def load_functions(path) -> list[Function_def]:
    """Load the function definition and assign an object."""
    funcs: Any = None
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
        funcs = Function_def.model_validate(d)
    return funcs


def loads_prompt(path) -> list[Prompt]:
    """Load the prompt configuration file needed."""
    prompts: Any = None
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
        prompts = Prompt.model_validate(d)
    return prompts


def parse_arg():
    parser = argparse.ArgumentParser()
    parser.add_argument('--functions_definition',
                        type=str,
                        default='data/input/functions_definition.json',
                        help=(
                            "function_definition_file, where to get the"
                            "reference functions."
                        ))
    parser.add_argument('--input',
                        type=str,
                        default="data/input/function_calling_tests.json",
                        help="input_file, where to get the input configuration to use.")
    parser.add_argument('--output',
                        type=str,
                        default="data/output/function_calls.json",
                        help="output_file, where to write the output.")
    args = parser.parse_args()
    return args


def main() -> None:
    """Main test for this part."""
    try:
        args = parse_arg()
        path_prompt = args.input
        path_func = args.functions_definition
        prompts = loads_prompt(path_prompt)
        funcs = load_functions(path_func)
    except FileNotFoundError:
        raise ParseError("This file do not exist sorry.")
    except PermissionError:
        raise ParseError("No permission to touch that file.")
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        raise ParseError(f"{e}")
    except ValidationError as e:
        raise ParseError("During Validation", f"{e}")
    except ParseError as e:
        console.print(e.ferror)
        sys.exit(1)
    else:
        console.print(prompts)
        console.print(funcs)


if __name__ == "__main__":
    try:
        main()
    except ParseError as e:
        console.print(e.ferror)
        sys.exit(1)
