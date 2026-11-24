from pydantic import BaseModel, ConfigDict, ValidationError, model_validator
from typing import Any
from enum import Enum
import json


class TestPrompt(BaseModel):
    model_config = ConfigDict(extra='allow', strict=True)  # if strict even int in str is invalid
    prompt: str

# --------------------Exercice 3.2--------------------------------------------

class Parameters(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    type: Types
    value: Any | None = None

    def __post_init__(self):
        match self.type and self.value:
            case Types.STR:
                self.value = str(self.value)
            case Types.INT:
                self.value = int(self.value)


class Returns(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    type: Types
    value: Any | None = None

    def __post_init__(self):
        match self.type and self.value:
            case Types.STR:
                self.value = str(self.value)
            case Types.INT:
                self.value = int(self.value)


class Fuction(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    name: str
    description: str
    parameters: dict[str, Parameters]
    # parameters: Parameters
    returns: Returns


class Types(str, Enum):
    STR = "string"
    INT = "number"

# ----------------------------------------------------------------------------


def first_pydantic():
    try:
        with open("Work_pattern/revision/ex.json", 'r') as f:
            data = json.load(f)
    except FileNotFoundError:   # fichier absent
        print(f"Error 404: Sorry, the file {f} not found.")
    except json.JSONDecodeError as e:   # json invalide
        print(f"Error with json: {e}")

    try:
        string = json.dumps(data)
        # test valide dict
        obj = TestPrompt.model_validate({"prompt": "OK", "Tia": "Hari"})
        print(obj)
        # test invalid value
        obj = TestPrompt.model_validate({"prompt": "42"})  # crash, invalid type, must be str
        print(obj)
        # test vide dict
        obj = TestPrompt.model_validate({})  # crash missing requierd
        # test avec un json
        obj = TestPrompt.model_validate_json(string)
        print(obj.prompt)
    except ValidationError as e:
        print(f"Error found: {e}")


def second_pydantic():
    try:
        with open("Work_pattern/revision/func.json", 'r') as f:
            data = json.load(f)
    except FileNotFoundError:   # fichier absent
        print(f"Error 404: Sorry, the file {f} not found.")
    except json.JSONDecodeError as e:   # json invalide
        print(f"Error with json: {e}")

    try:
        string = json.dumps(data)
        func = Fuction.model_validate_json(string)
        print(func)
    except ValidationError as e:
        print(f"Validation error found: {e}")


if __name__ == "__main__":
    first_pydantic()
    print("\n----------------------------------------------------------------\n")
    second_pydantic()
