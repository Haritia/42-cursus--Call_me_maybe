from pydantic import BaseModel, ConfigDict, ValidationError
from typing import Any
from enum import Enum
import json


class TestPrompt(BaseModel):
    model_config = ConfigDict(extra='allow', strict=True)
    prompt: str

class Fuction(BaseModel):
    name: str
    description: str
    parameters: dict[Any]
    returns: Any


class Types(str, Enum):
    STR = "string"
    INT = "number"


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
        obj = TestPrompt.model_validate({"prompt": 42}) # crash, invalid type, must be str
        # test vide dict
        obj = TestPrompt.model_validate({}) # crash missing requierd
        # test avec un json
        second = TestPrompt.model_validate_json(string)
        print(second.prompt)
    except ValidationError as e:
        print(f"Error found: {e}")


if __name__ == "__main__":
    first_pydantic()
    print("\n----------------------------------------------------------------\n")
