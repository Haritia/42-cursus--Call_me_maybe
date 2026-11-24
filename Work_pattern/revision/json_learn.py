import json
from pathlib import Path
import os

"""
json.load(file): from config file to python
json.loads: from json formatted string to python
json.dump(obj, f):from python to file json format
jon.dumps(obj): from python to json fomatted string
"""


def first_json():
    try:
        file = Path()
        with open("Work_pattern/revision/example.json", 'r') as f:
            data = json.load(f)
        print(type(data))
        print(type(data[0]))
    except FileNotFoundError:
        print(f"Error 404: Sorry, the file {f} not found.")
    except json.JSONDecodeError as e:
        print(f"Error with json: {e}")


def second_json():
    try:
        with open("Work_pattern/revision/example.json", 'r') as f:
            data = json.load(f)
    except FileNotFoundError:   # fichier absent
        print(f"Error 404: Sorry, the file {f} not found.")
    except json.JSONDecodeError as e:   # json invalide
        print(f"Error with json: {e}")
    for d in data:          # json valide
        print(d)


def third_json():
    data = [
        {
            "name": "fn_add_numbers",
            "description": "Add two numbers together and return their sum.",
            "parameters": {
                "a": 2,
                "b": 3
            },
            "returns": 5
        },
        {
            "name": "fn_greet",
            "description": "Generate a greeting message for a person by name.",
            "parameters": {
                "name": "Tia"
            },
            "returns": "Hello my dear Tia"
        },
    ]
    Path("data/output/").mkdir(parents=True, exist_ok=True)
    with open("data/output/new.json", 'w') as f:
        json.dump(data, f, indent=4)
        
    try:
        with open("Work_pattern/revision/example.json", 'r') as fp:
            config = json.load(fp)
    except FileNotFoundError:
        print(f"404 Error, the file {fp} not found.")
    except json.JSONDecodeError as e:
        print(f"Erron on json: {e}")
    print("=== DATA python list[dict] ===")
    print(data)
    print("=== CONFIG json -> python ===")
    print(config)
    print("=== PYTHON -> JSON STRING ===")
    string = json.dumps(data, indent=2)
    print(f"==> {type(string)} \n{string}")
    print("=== JSON STRING -> PYTHON ===")
    p = json.loads(string)
    print(f"==> {type(p)}\n{p}")



if __name__ == "__main__":
    first_json()
    print("\n---------------------------------------------------------------")
    second_json()
    print("\n---------------------------------------------------------------")
    third_json()
    print("\n---------------------------------------------------------------")
