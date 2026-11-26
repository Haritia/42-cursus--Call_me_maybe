from pydantic import BaseModel, ConfigDict, ValidationError, model_validator
from typing import Any, Literal, Optional
from enum import Enum
import json


class TestPrompt(BaseModel):
    model_config = ConfigDict(extra='allow', strict=True)  # if strict even int in str is invalid
    prompt: str

# --------------------Exercice 3.2--------------------------------------------


Types = Literal["string", "number", "boolean", "list", "dict", "set", "tuple"]


class Parameters(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=False)
    type: Types
    value: Optional[Any] = None

    def model_post_init(self, __context):
        match self.type:
            case "string" if self.value:
                self.value = str(self.value)
            case "number" if self.value:
                self.value = float(self.value)


class Returns(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    type: Types
    value: Optional[Any] = None

    def model_post_init(self, __context):
        match (self.type, bool(self.value)):
            case ("string", True):
                self.value = str(self.value)
            case ("number", True):
                self.value = float(self.value)



class Fuction(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    name: str
    description: str
    parameters: dict[str, Parameters]
    returns: Returns
    # parameters: Parameters


# class Types(str, Enum):
#     STR = "string"
#     INT = "number"

# ----------------------------------------------------------------------------


def first_pydantic():
    try:
        with open("Work_pattern/revision/ex.json", 'r') as f:
            data = json.load(f)
    except FileNotFoundError:   # fichier absent
        print(f"Error 404: Sorry, the file {f} not found.")
    except json.JSONDecodeError as e:   # json invalide
        print(f"Error with json: {e}")

    tests = [
        {"prompt": "OK", "Tia": "Hari"},  # test valide dict
        {"prompt": 42},  # test invalid value
        {}  # test vide dict
    ]
    for test in tests:
        try:
            obj = TestPrompt.model_validate(test)
            print(obj)
        except ValidationError as e:
            print(f"Error found: {e}")
    try:
        string = json.dumps(data)
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
        print(string)
        func = Fuction.model_validate_json(string)
        print(func)
    except ValidationError as e:
        print(f"Validation error found: {e}")
    except json.JSONDecodeError as e:
        print(f"Error found on json: {e}")

def third_pydantic():
    try:
        with open("Work_pattern/revision/ex.json", 'r') as f:
            data = json.load(f)
    except FileNotFoundError:   # fichier absent
        print(f"Error 404: Sorry, the file {f} not found.")
    except json.JSONDecodeError as e:   # json invalide
        print(f"Error with json: {e}")

    print("--- Valide value ---\nprompt attend str et accepte les extras")
    obj = TestPrompt.model_validate({"prompt": "OK", "Tia": "Hari"})
    print(obj)
    obj = TestPrompt.model_validate({"prompt": "42"})
    print(obj)
    try:
        print("--- Invalid value ---\naccepte uniquement str")
        obj = TestPrompt.model_validate({"prompt": 42})
    except ValidationError as e:
        print(f"Error found: {e}")
    try:
        print("--- test vide ---")
        obj = TestPrompt.model_validate({})
    except ValidationError as e:
        print(f"Error found: {e}")
    try:
        print("--- test value vide ---/ accepter un '' est toujors un str mais vide ")
        obj = TestPrompt.model_validate({"prompt": ""})
        print(obj)
    except ValidationError as e:
        print(f"Error found: {e}")
    try:
        print("--- test on json ---")
        string = json.dumps(data)
        obj = TestPrompt.model_validate_json(string)
        print(obj.prompt)
    except ValidationError as e:
        print(f"Error found: {e}")



if __name__ == "__main__":
    first_pydantic()
    print("\n----------------------------------------------------------------\n")
    second_pydantic()
    print("\n----------------------------------------------------------------\n")
    third_pydantic()
