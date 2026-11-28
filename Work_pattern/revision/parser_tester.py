#!/usr/bin/env python3
"""Black-box tester for the call-me-maybe input/output handling.

The tester never imports your code. It builds throw-away files in a
temporary folder, runs your program as a subprocess and judges what it
sees: exit code, traceback, message. It works with any implementation:

    python3 parser_tester.py --cmd "python3 exercice4.py"
    python3 parser_tester.py --cmd "uv run python -m src" --cwd ~/project

Verdicts:
    PASS  the program did what a robust program should do
    WARN  it works, but the message could be clearer
    FAIL  crash, silence, or wrong accept / reject

Exit code of the tester: 0 if no FAIL, 1 otherwise.
"""

import argparse
import json
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Optional, Union

FUNCTIONS_NAME = "functions_definition.json"
PROMPTS_NAME = "function_calling_tests.json"
OUTPUT_NAME = "result.json"


class Marker(Enum):
    """Special file states that are not plain text."""

    ABSENT = "absent"
    DIRECTORY = "directory"


Content = Union[str, bytes, Marker]


# --------------------------------------------------------------------------
# Valid reference data (taken from the subject)
# --------------------------------------------------------------------------

def _fn(name: str, desc: str, params: dict[str, str], ret: str) -> Any:
    """Build one function definition in the format of the subject."""
    return {
        "name": name,
        "description": desc,
        "parameters": {k: {"type": v} for k, v in params.items()},
        "returns": {"type": ret},
    }


GOOD_FUNCTION = _fn("fn_add_numbers", "Add two numbers.",
                    {"a": "number", "b": "number"}, "number")

VALID_FUNCTIONS = json.dumps([
    GOOD_FUNCTION,
    _fn("fn_greet", "Greet a person.", {"name": "string"}, "string"),
    _fn("fn_reverse_string", "Reverse a string.", {"s": "string"},
        "string"),
], indent=2)

VALID_PROMPTS = json.dumps([
    {"prompt": "What is the sum of 2 and 3?"},
    {"prompt": "What is the sum of 265 and 345?"},
    {"prompt": "Greet shrek"},
    {"prompt": "Reverse the string 'hello'"},
], indent=2)


def funcs_with(**changes: Any) -> str:
    """Valid function list where the first function is modified."""
    first = dict(GOOD_FUNCTION)
    first.update(changes)
    return json.dumps([first])


def funcs_without(key: str) -> str:
    """Valid function list where the first function lacks one key."""
    first = dict(GOOD_FUNCTION)
    del first[key]
    return json.dumps([first])


# --------------------------------------------------------------------------
# The test catalogue
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class Case:
    """One scenario: files to build, and what we expect."""

    cid: str
    group: str
    title: str
    expect: str  # "ok", "error" or "either" (design decision)
    functions: Content = VALID_FUNCTIONS
    prompts: Content = VALID_PROMPTS
    culprit: Optional[str] = None  # file the message should name
    hint: str = ""
    note: str = ""
    args: Optional[tuple[str, ...]] = None  # replaces the default args
    out: str = "fresh"  # fresh | dir | under_file | existing
    needs_output: bool = False
    check_output: bool = False


G_FUNC = "Fichier des fonctions"
G_PROMPT = "Fichier des prompts"
G_MIX = "Combinaisons"
G_ARGS = "Options en ligne de commande"
G_OUT = "Fichier de sortie (option --with-output)"

NOT_LIST = (
    "Après json.load, le résultat peut être n'importe quoi (None, "
    "nombre, texte, dict). Vérifie que c'est bien une liste AVANT de "
    "la parcourir, ou laisse pydantic valider le tout (list[Modèle])."
)
BAD_ENCODING = (
    "UnicodeDecodeError hérite de ValueError, pas de OSError. "
    "Attrape-la avec JSONDecodeError : except (A, B) as e."
)
DIR_INSTEAD = (
    "IsADirectoryError est une OSError. Attraper les erreurs d'ouverture "
    "de fichier avec OSError couvre aussi droits, dossier, disque."
)
NAME_FILE = (
    "Mets le chemin du fichier fautif dans le message : avec deux "
    "fichiers, l'utilisateur doit savoir lequel est en cause."
)
BRACKETS = (
    "Les crochets de la donnée sont lus comme du formatage par rich. "
    "Échappe le texte (rich.markup.escape) ou n'utilise pas de "
    "balises dans le texte d'une exception."
)

HUGE_FUNCTIONS = json.dumps([
    _fn(f"fn_{i}", f"Function number {i}.", {"x": "number"}, "number")
    for i in range(1000)
])

SPECIAL_PROMPTS = json.dumps([
    {"prompt": "Say \"hi\" to O'Brien"},
    {"prompt": "Reverse 'héllo wörld 😀'"},
    {"prompt": "Line1\nLine2\tTabbed"},
    {"prompt": "Path C:\\temp\\new and {braces} [/x] <b>&amp;</b>"},
    {"prompt": ""},
])


def build_cases() -> list[Case]:
    """Return every scenario, in display order."""
    f_ok = "functions"
    p_ok = "prompts"
    return [
        # ---- functions file ------------------------------------------
        Case("F01", G_FUNC, "Fichier valide (3 fonctions)", "ok"),
        Case("F02", G_FUNC, "Fichier absent", "error",
             functions=Marker.ABSENT, culprit=f_ok, hint=NAME_FILE),
        Case("F03", G_FUNC, "Fichier vide (0 octet)", "error",
             functions="", culprit=f_ok),
        Case("F04", G_FUNC, "JSON avec virgule en trop", "error",
             functions='[{"name": "x",}]', culprit=f_ok),
        Case("F05", G_FUNC, "JSON coupé en plein milieu", "error",
             functions=VALID_FUNCTIONS[:60], culprit=f_ok),
        Case("F06", G_FUNC, "Un objet {} au lieu d'une liste", "error",
             functions=json.dumps(GOOD_FUNCTION), culprit=f_ok,
             hint=NOT_LIST),
        Case("F07", G_FUNC, "`null` au lieu d'une liste", "error",
             functions="null", culprit=f_ok, hint=NOT_LIST),
        Case("F08", G_FUNC, "Un nombre `5` au lieu d'une liste", "error",
             functions="5", culprit=f_ok, hint=NOT_LIST),
        Case("F09", G_FUNC, "Un texte \"abc\" au lieu d'une liste",
             "error", functions='"abc"', culprit=f_ok, hint=NOT_LIST),
        Case("F10", G_FUNC, "Liste de nombres [1, 2]", "error",
             functions="[1, 2]", culprit=f_ok),
        Case("F11", G_FUNC, "Un dossier à la place du fichier", "error",
             functions=Marker.DIRECTORY, culprit=f_ok, hint=DIR_INSTEAD),
        Case("F12", G_FUNC, "Octets illisibles (pas de l'UTF-8)", "error",
             functions=b"\xff\xfe\x00bad", culprit=f_ok,
             hint=BAD_ENCODING),
        Case("F13", G_FUNC, "Fichier avec BOM UTF-8 (éditeurs Windows)",
             "either", functions=b"\xef\xbb\xbf" + VALID_FUNCTIONS.encode(),
             note="Accepter (encoding='utf-8-sig') ou refuser : au choix, "
                  "mais sans plantage."),
        Case("F14", G_FUNC, "Fonction sans `name`", "error",
             functions=funcs_without("name"), culprit=f_ok),
        Case("F15", G_FUNC, "`name` n'est pas un texte (123)", "error",
             functions=funcs_with(name=123), culprit=f_ok),
        Case("F16", G_FUNC, "Type de paramètre inconnu (\"banana\")",
             "error",
             functions=funcs_with(parameters={"a": {"type": "banana"}}),
             culprit=f_ok),
        Case("F17", G_FUNC, "Type \"integer\" (absent de ta liste ?)",
             "either",
             functions=funcs_with(parameters={"a": {"type": "integer"}}),
             note="Le sujet dit « number, string, boolean, etc. ». Si tu "
                  "acceptes un type, ta contrainte devra savoir le "
                  "générer."),
        Case("F18", G_FUNC, "`parameters` est une liste", "error",
             functions=funcs_with(parameters=[]), culprit=f_ok),
        Case("F19", G_FUNC, "Paramètre sans `type`", "error",
             functions=funcs_with(parameters={"a": {}}), culprit=f_ok),
        Case("F20", G_FUNC, "Fonction sans aucun paramètre (`{}`)", "ok",
             functions=funcs_with(parameters={}),
             hint="Une fonction comme fn_get_time n'a pas de paramètre : "
                  "c'est valide."),
        Case("F21", G_FUNC, "Fonction sans `returns`", "either",
             functions=funcs_without("returns"),
             note="Le sujet dit que chaque fonction a un type de retour."),
        Case("F22", G_FUNC, "Fonction sans `description`", "either",
             functions=funcs_without("description"),
             note="Le sujet dit que chaque fonction a une description."),
        Case("F23", G_FUNC, "Clé inconnue en plus (\"version\")", "either",
             functions=funcs_with(version=2),
             note="extra='forbid' (strict) ou 'ignore' (tolérant) : à "
                  "décider. Le sujet prévient que les fichiers peuvent "
                  "changer."),
        Case("F24", G_FUNC, "Deux fonctions avec le même nom", "either",
             functions=json.dumps([GOOD_FUNCTION, GOOD_FUNCTION]),
             note="Ambigu pour le LLM : refuser ou ignorer, à décider."),
        Case("F25", G_FUNC, "Liste vide []", "either", functions="[]",
             note="Aucune fonction à choisir : message clair conseillé."),
        Case("F26", G_FUNC, "Texte spécial (accents, émoji, guillemets)",
             "ok",
             functions=funcs_with(
                 description="Dit « bonjour » à O'Brien 😀 \"ok\" [/x]"),
             hint="Les données valides ne doivent jamais faire planter."),
        Case("F27", G_FUNC, "1000 fonctions (lenteur ?)", "ok",
             functions=HUGE_FUNCTIONS),
        # ---- prompts file --------------------------------------------
        Case("P01", G_PROMPT, "Fichier valide (4 prompts)", "ok"),
        Case("P02", G_PROMPT, "Fichier absent", "error",
             prompts=Marker.ABSENT, culprit=p_ok, hint=NAME_FILE),
        Case("P03", G_PROMPT, "Fichier vide (0 octet)", "error",
             prompts="", culprit=p_ok),
        Case("P04", G_PROMPT, "JSON avec virgule en trop", "error",
             prompts='[{"prompt": "x",}]', culprit=p_ok),
        Case("P05", G_PROMPT, "Un objet {} au lieu d'une liste", "error",
             prompts='{"prompt": "x"}', culprit=p_ok, hint=NOT_LIST),
        Case("P06", G_PROMPT, "`null` au lieu d'une liste", "error",
             prompts="null", culprit=p_ok, hint=NOT_LIST),
        Case("P07", G_PROMPT, "`prompt` est un nombre (42)", "error",
             prompts='[{"prompt": 42}]', culprit=p_ok),
        Case("P08", G_PROMPT, "Clé `prompt` manquante", "error",
             prompts='[{"text": "x"}]', culprit=p_ok),
        Case("P09", G_PROMPT, "Éléments qui ne sont pas des objets",
             "error", prompts='["a", "b"]', culprit=p_ok),
        Case("P10", G_PROMPT, "`prompt` vaut null", "error",
             prompts='[{"prompt": null}]', culprit=p_ok),
        Case("P11", G_PROMPT, "Prompt = chaîne vide \"\"", "ok",
             prompts='[{"prompt": ""}]',
             hint="Le sujet (V.6) demande de tester les chaînes vides : "
                  "c'est du texte valide pour le parseur."),
        Case("P12", G_PROMPT, "Caractères spéciaux (\", \\, \\n, émoji)",
             "ok", prompts=SPECIAL_PROMPTS,
             hint="Les données valides ne doivent jamais faire planter."),
        Case("P13", G_PROMPT, "Prompt géant (100 000 caractères)", "ok",
             prompts=json.dumps([{"prompt": "a" * 100_000}])),
        Case("P14", G_PROMPT, "Clé inconnue en plus (\"id\")", "either",
             prompts='[{"prompt": "x", "id": 1}]',
             note="Un seul prompt avec une clé en trop doit-il bloquer "
                  "tout le fichier ? À décider."),
        Case("P15", G_PROMPT, "Liste vide []", "either", prompts="[]",
             note="Rien à traiter : sortie vide ou message clair."),
        Case("P16", G_PROMPT, "Un dossier à la place du fichier", "error",
             prompts=Marker.DIRECTORY, culprit=p_ok, hint=DIR_INSTEAD),
        Case("P17", G_PROMPT, "Octets illisibles (pas de l'UTF-8)",
             "error", prompts=b"\xff\xfe\x00bad", culprit=p_ok,
             hint=BAD_ENCODING),
        Case("P18", G_PROMPT, "Grands nombres écrits dans le texte", "ok",
             prompts=json.dumps([
                 {"prompt": "Add 99999999999999999999 and 1e308"}]),
             hint="Ce sont des mots dans une phrase : texte valide."),
        Case("P19", G_PROMPT, "Valeur invalide qui contient [/x]",
             "error", prompts='[{"prompt": ["[/x]"]}]', culprit=p_ok,
             hint=BRACKETS),
        # ---- combinations --------------------------------------------
        Case("X01", G_MIX, "Fichiers inversés (--input et --functions)",
             "error", functions=VALID_PROMPTS, prompts=VALID_FUNCTIONS,
             culprit="any",
             hint="Un message qui nomme le fichier et dit ce qui est "
                  "attendu aide l'utilisateur à voir l'inversion."),
        Case("X02", G_MIX, "Les deux fichiers absents", "error",
             functions=Marker.ABSENT, prompts=Marker.ABSENT,
             culprit="any"),
        Case("X03", G_MIX, "Les deux fichiers invalides", "error",
             functions="{", prompts="[", culprit="any"),
        # ---- command line --------------------------------------------
        Case("A01", G_ARGS, "Option inconnue (--foo)", "error",
             args=("--foo", "1"),
             note="argparse s'en charge : code 2 et message d'usage."),
        Case("A02", G_ARGS, "--input sans valeur", "error",
             args=("--input",)),
        Case("A03", G_ARGS, "Ancien nom --function_definition (sans s)",
             "error", args=("--function_definition", "x.json")),
        Case("A04", G_ARGS, "--help", "ok", args=("--help",),
             hint="--help doit afficher l'aide et finir avec le code 0."),
        # ---- output --------------------------------------------------
        Case("S01", G_OUT, "Sortie dans un dossier qui n'existe pas",
             "ok", needs_output=True, check_output=True,
             hint="data/output/ n'est pas dans le dépôt : crée-le "
                  "(Path.mkdir(parents=True, exist_ok=True))."),
        Case("S02", G_OUT, "Fichier de sortie déjà existant", "ok",
             out="existing", needs_output=True, check_output=True,
             hint="Il doit être écrasé, pas ajouté ni refusé."),
        Case("S03", G_OUT, "La sortie est un dossier", "error",
             out="dir", culprit="output", needs_output=True,
             hint=DIR_INSTEAD),
        Case("S04", G_OUT, "Le « dossier » parent est un fichier",
             "error", out="under_file", culprit="output",
             needs_output=True,
             hint="NotADirectoryError est aussi une OSError."),
    ]


# --------------------------------------------------------------------------
# Running one case
# --------------------------------------------------------------------------

@dataclass
class Run:
    """What the subprocess did."""

    returncode: int
    output: str
    seconds: float
    timed_out: bool
    out_path: Path


@dataclass
class Verdict:
    """Judgement of one case."""

    status: str  # PASS, WARN, FAIL
    kind: str  # machine name of the problem, "" when PASS
    message: str  # plain-language sentence
    detail: str = ""


ANSI = re.compile(r"\x1b\[[0-9;]*m")


def write_content(path: Path, content: Content) -> None:
    """Create the file, folder, or nothing, as the case requires."""
    if content is Marker.ABSENT:
        return
    if content is Marker.DIRECTORY:
        path.mkdir()
    elif isinstance(content, bytes):
        path.write_bytes(content)
    else:
        path.write_text(content, encoding="utf-8")


def prepare_output(case: Case, root: Path) -> Path:
    """Return the --output path, building what the case needs."""
    if case.out == "dir":
        path = root / "out_is_a_dir"
        path.mkdir()
    elif case.out == "under_file":
        (root / "plain_file").write_text("x", encoding="utf-8")
        path = root / "plain_file" / OUTPUT_NAME
    elif case.out == "existing":
        path = root / OUTPUT_NAME
        path.write_text("old garbage, not json", encoding="utf-8")
    else:
        path = root / "new_folder" / "deep" / OUTPUT_NAME
    return path


def run_case(case: Case, cmd: list[str], cwd: Path,
             timeout: float) -> Run:
    """Build the files, run the program, return what happened."""
    with tempfile.TemporaryDirectory(prefix="parser_tester_") as tmp:
        root = Path(tmp)
        funcs, prompts = root / FUNCTIONS_NAME, root / PROMPTS_NAME
        write_content(funcs, case.functions)
        write_content(prompts, case.prompts)
        out_path = prepare_output(case, root)
        if case.args is not None:
            args = list(case.args)
        else:
            args = ["--functions_definition", str(funcs),
                    "--input", str(prompts), "--output", str(out_path)]
        start = time.monotonic()
        code, raw, timed_out = -1, b"", False
        try:
            proc = subprocess.run(cmd + args, cwd=cwd, timeout=timeout,
                                  capture_output=True, check=False)
            code, raw = proc.returncode, proc.stdout + proc.stderr
        except subprocess.TimeoutExpired as exc:
            raw, timed_out = exc.stdout or b"", True
        seconds = time.monotonic() - start
        text = ANSI.sub("", raw.decode("utf-8", errors="replace"))
        run = Run(code, text, seconds, timed_out, out_path)
        if case.check_output:
            run = check_output_file(case, run)
        run.output = _with_paths(run.output, root)
        return run


def check_output_file(case: Case, run: Run) -> Run:
    """Append a marker to the output if the result file is unusable."""
    if run.returncode != 0 or case.out == "dir":
        return run
    problem = ""
    if not run.out_path.is_file():
        problem = "le fichier de sortie n'a pas été créé"
    else:
        try:
            data = json.loads(run.out_path.read_text(encoding="utf-8"))
            if not isinstance(data, list):
                problem = "la sortie n'est pas une liste JSON"
        except (OSError, ValueError):
            problem = "la sortie n'est pas du JSON valide"
    if problem:
        run.output += f"\n@@OUTPUT_PROBLEM@@ {problem}"
    return run


def _with_paths(text: str, root: Path) -> str:
    """Keep the temp folder out of the displayed text."""
    return text.replace(str(root), "<tmp>")


# --------------------------------------------------------------------------
# Judging
# --------------------------------------------------------------------------

def squash(text: str) -> str:
    """Remove all whitespace: messages may be wrapped by the program."""
    return re.sub(r"\s+", "", text)


def first_lines(text: str, count: int = 2, width: int = 110) -> str:
    """Short excerpt of a message for display."""
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    excerpt = " | ".join(lines[:count])
    return excerpt if len(excerpt) <= width else excerpt[:width - 3] + "..."


def traceback_summary(text: str) -> str:
    """Last line of a Python traceback: the exception and its message."""
    lines = [ln for ln in text.splitlines() if ln.strip()]
    return lines[-1].strip() if lines else ""


def names_culprit(case: Case, text: str) -> bool:
    """Does the message name the file in fault?"""
    flat = squash(text)
    names = {"functions": [FUNCTIONS_NAME], "prompts": [PROMPTS_NAME],
             "output": [OUTPUT_NAME, "out_is_a_dir", "plain_file"],
             "any": [FUNCTIONS_NAME, PROMPTS_NAME]}
    return any(squash(n) in flat for n in names.get(case.culprit or "", []))


def judge(case: Case, run: Run) -> Verdict:
    """Compare what happened with what a robust program should do."""
    text = run.output
    if run.timed_out:
        return Verdict("FAIL", "timeout",
                       f"le programme ne se termine pas ({run.seconds:.0f} "
                       "s écoulées)", first_lines(text))
    if "Traceback (most recent call last)" in text:
        return Verdict("FAIL", "crash",
                       "le programme plante avec une trace Python",
                       traceback_summary(text))
    problem = re.search(r"@@OUTPUT_PROBLEM@@ (.*)", text)
    if problem and case.expect != "error":
        return Verdict("FAIL", "output",
                       "programme terminé, mais " + problem.group(1))
    ok = run.returncode == 0
    if case.expect == "ok":
        if ok:
            return Verdict("PASS", "", "accepté")
        return Verdict("FAIL", "rejected",
                       "une entrée valide est refusée (code "
                       f"{run.returncode})", first_lines(text))
    if case.expect == "error":
        if ok:
            return Verdict("FAIL", "accepted",
                           "entrée invalide acceptée (code 0, aucune "
                           "erreur)", first_lines(text))
        if not text.strip():
            return Verdict("FAIL", "silent",
                           f"échec (code {run.returncode}) sans aucun "
                           "message : l'utilisateur ne sait pas pourquoi")
        if case.culprit and not names_culprit(case, text):
            return Verdict("WARN", "unclear",
                           "erreur propre, mais le message ne nomme pas le "
                           "fichier en cause", first_lines(text))
        return Verdict("PASS", "", "refusé proprement",
                       first_lines(text))
    # "either": any clean behaviour is fine
    if ok:
        return Verdict("PASS", "", "accepté")
    if not text.strip():
        return Verdict("FAIL", "silent",
                       f"échec (code {run.returncode}) sans aucun message")
    return Verdict("PASS", "", "refusé proprement", first_lines(text))


# --------------------------------------------------------------------------
# Display
# --------------------------------------------------------------------------

USE_COLOR = sys.stdout.isatty()
ICON = {"PASS": "✅", "WARN": "⚠️ ", "FAIL": "❌"}
COLOR = {"PASS": "32", "WARN": "33", "FAIL": "31"}

KIND_INFO = {
    "crash": ("Plantages",
              "Une trace Python = projet « non fonctionnel » (sujet IV.1)."
              " Attrape l'erreur et affiche un message."),
    "timeout": ("Programme bloqué",
                "Une boucle infinie ou une attente sans fin."),
    "silent": ("Échecs silencieux",
               "Le programme échoue sans dire pourquoi."),
    "accepted": ("Entrées invalides acceptées",
                 "Une validation manque : le programme continue avec des "
                 "données fausses."),
    "rejected": ("Entrées valides refusées",
                 "Une règle est trop stricte ou boguée."),
    "output": ("Sortie absente ou invalide",
               "Le fichier résultat n'est pas créé ou pas du JSON."),
    "unclear": ("Messages peu clairs",
                "Le message n'indique pas quel fichier est en cause."),
}
KIND_ORDER = list(KIND_INFO)


def paint(text: str, code: str) -> str:
    """Colour a text when writing to a terminal."""
    return f"\033[{code}m{text}\033[0m" if USE_COLOR else text


def show(case: Case, verdict: Verdict, run: Run, verbose: bool) -> None:
    """Print the result of one case."""
    icon = paint(ICON[verdict.status], COLOR[verdict.status])
    print(f"{icon} {case.cid}  {case.title}")
    if verdict.status == "PASS":
        if case.expect == "either":
            tail = f" : {verdict.detail}" if verdict.detail else ""
            print(f"       → {verdict.message}{tail}")
            if case.note:
                print(f"       ℹ  {case.note}")
    else:
        print(f"       Problème : {verdict.message}")
        if verdict.detail:
            print(f"       Constaté : {verdict.detail}")
        if case.hint:
            print(f"       Piste    : {case.hint}")
    if verbose:
        for line in run.output.strip().splitlines()[:12]:
            print(f"       │ {line}")


def summary(results: list[tuple[Case, Verdict]]) -> int:
    """Print the final report, return the exit code."""
    total = len(results)
    counts = {s: sum(v.status == s for _, v in results)
              for s in ("PASS", "WARN", "FAIL")}
    print("\n" + "=" * 70)
    print(f"RÉSUMÉ : {counts['PASS']} ✅   {counts['WARN']} ⚠️    "
          f"{counts['FAIL']} ❌   ({total} cas)")
    bad = [(c, v) for c, v in results if v.status != "PASS"]
    if not bad:
        print("Aucun problème trouvé sur ces cas. Bien joué.")
        return 0
    print("\nÀ régler dans cet ordre :")
    number = 0
    for kind in KIND_ORDER:
        ids = [c.cid for c, v in bad if v.kind == kind]
        if not ids:
            continue
        number += 1
        title, why = KIND_INFO[kind]
        print(f"  {number}. {title} ({len(ids)}) : {' '.join(ids)}")
        print(f"     {why}")
    return 1 if counts["FAIL"] else 0


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    """Read the command line."""
    parser = argparse.ArgumentParser(
        description="Teste le traitement des fichiers d'entrée / sortie.")
    parser.add_argument("--cmd", default="uv run python -m src",
                        help="commande qui lance ton programme "
                             "(défaut : %(default)s)")
    parser.add_argument("--cwd", default=".",
                        help="dossier où lancer la commande")
    parser.add_argument("--timeout", type=float, default=30.0,
                        help="secondes max par cas (défaut : 30)")
    parser.add_argument("--only", default="",
                        help="ids ou préfixes séparés par des virgules, "
                             "ex. F07,P ou S")
    parser.add_argument("--errors-only", action="store_true",
                        help="saute les cas valides (utile quand le "
                             "programme complet appelle le LLM : lent)")
    parser.add_argument("--with-output", action="store_true",
                        help="ajoute les cas du fichier de sortie")
    parser.add_argument("--verbose", action="store_true",
                        help="affiche le texte produit par le programme")
    parser.add_argument("--list", action="store_true",
                        help="liste les cas sans les lancer")
    return parser.parse_args()


def select(cases: list[Case], args: argparse.Namespace) -> list[Case]:
    """Apply the user's filters."""
    wanted = [p.strip().upper() for p in args.only.split(",") if p.strip()]
    chosen = []
    for case in cases:
        if case.needs_output and not args.with_output:
            continue
        if args.errors_only and case.expect == "ok":
            continue
        if wanted and not any(case.cid.startswith(w) for w in wanted):
            continue
        chosen.append(case)
    return chosen


def main() -> int:
    """Run the selected cases and print the report."""
    args = parse_args()
    chosen = select(build_cases(), args)
    if args.list:
        for case in chosen:
            print(f"{case.cid}  [{case.expect:6}]  {case.title}")
        return 0
    cmd = shlex.split(args.cmd)
    cwd = Path(args.cwd).expanduser().resolve()
    if not cwd.is_dir():
        print(f"Dossier introuvable pour --cwd : {cwd}")
        return 2
    if not cmd or shutil.which(cmd[0]) is None:
        print(f"Commande introuvable : {cmd[0] if cmd else '(vide)'}")
        return 2
    print(f"Commande : {args.cmd}\nDossier  : {cwd}\n")
    results: list[tuple[Case, Verdict]] = []
    group = ""
    for case in chosen:
        if case.group != group:
            group = case.group
            print(f"\n=== {group} ===")
        run = run_case(case, cmd, cwd, args.timeout)
        verdict = judge(case, run)
        show(case, verdict, run, args.verbose)
        results.append((case, verdict))
    return summary(results)


if __name__ == "__main__":
    sys.exit(main())
