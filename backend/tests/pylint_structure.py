"""Pylint plugin: the NestJS-style layout and the ways around the checks.

Import rules between folders are tach's job and loops between features import-linter's. This covers
what they can't see: missing or extra files, a feature's edited layer rules, a feature left out of
main.py or app_module.py, missing tests, and comments or calls that switch a check off.
Checker.close() runs after the last file, so a layout problem shows up on every pylint run.
"""

import hashlib
import re
import tokenize
import tomllib
from collections.abc import Iterator
from pathlib import Path
from typing import override

from astroid import nodes  # pyright: ignore[reportMissingTypeStubs] -- astroid ships no stubs
from pylint.checkers import BaseTokenChecker
from pylint.lint import PyLinter
from pylint.typing import MessageDefinitionTuple

BACKEND_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = BACKEND_DIR / "src"
APP_DIR = SRC_DIR / "app"
FEATURES_DIR = APP_DIR / "features"
TESTS_DIR = BACKEND_DIR / "tests" / "features"
# Fingerprint of the layer rules every feature carries. Changing the rules means editing
# features/items/tach.domain.toml, copying it to every feature and putting its new hash here.
LAYER_RULES_SHA256 = "8b419fcfe020d849c0814291e665af42fb2ae02059a66e3474bf4801fbfca22b"
REQUIRED_FILES = ("__init__.py", "dependencies.py", "tach.domain.toml")
REQUIRED_PACKAGES = ("routers", "services", "repositories", "schemas", "constants", "utils")
APP_ENTRIES = ("__init__.py", "main.py", "app_module.py", "core", "common", "features")
IGNORED = ("__pycache__",)
BYPASS_COMMENTS = re.compile(
    r"tach-ignore|noqa:[^#\n]*TID|reportImportCycles|pylint:\s*(?:disable|skip-file)"
)
DYNAMIC_IMPORTS = frozenset({"__import__", "import_module"})


def entries(folder: Path) -> set[str]:
    return {p.name for p in folder.iterdir() if p.name not in IGNORED}


def feature_problems(feature: Path) -> Iterator[str]:
    where = f"src/app/features/{feature.name}/"
    missing = [name for name in REQUIRED_FILES if not (feature / name).is_file()]
    missing += [
        f"{name}/" for name in REQUIRED_PACKAGES if not (feature / name / "__init__.py").is_file()
    ]
    if missing:
        yield f"{where} is missing: {', '.join(missing)}"
    extra = sorted(entries(feature) - {*REQUIRED_FILES, *REQUIRED_PACKAGES})
    if extra:
        yield f"{where} has entries outside the layout: {', '.join(extra)}"
    rules = feature / "tach.domain.toml"
    if rules.is_file() and hashlib.sha256(rules.read_bytes()).hexdigest() != LAYER_RULES_SHA256:
        yield f"{where}tach.domain.toml differs from the layer rules pinned in pylint_structure.py"
    if not list((TESTS_DIR / feature.name).glob("test_*.py")):
        yield f"tests/features/{feature.name}/ has no test_*.py files"
    module = f"src.app.features.{feature.name}"
    if f"{module}.routers" not in (APP_DIR / "main.py").read_text():
        yield f"{module} router is not registered in main.py"
    if f"{module}.dependencies" not in (APP_DIR / "app_module.py").read_text():
        yield f"{module} provider is not registered in app_module.py"


def app_problems() -> Iterator[str]:
    extra = sorted(entries(SRC_DIR) - {"__init__.py", "app"})
    extra += sorted(f"app/{name}" for name in entries(APP_DIR) - set(APP_ENTRIES))
    extra += sorted(
        f"app/features/{name}"
        for name in entries(FEATURES_DIR) - {"__init__.py"}
        if not (FEATURES_DIR / name).is_dir()
    )
    if extra:
        yield f"src/ has entries outside the layout: {', '.join(extra)}"
    config: dict[str, list[dict[str, str]]] = tomllib.loads((BACKEND_DIR / "tach.toml").read_text())
    modules = {module["path"] for module in config["modules"]}
    core_names = entries(APP_DIR / "core") - {"__init__.py"}
    missing = sorted(n for n in core_names if f"src.app.core.{Path(n).stem}" not in modules)
    if missing:
        yield f"src/app/core/ entries without a module in tach.toml: {', '.join(missing)}"


def layout_problems() -> Iterator[str]:
    yield from app_problems()
    for feature in sorted(
        p for p in FEATURES_DIR.iterdir() if p.is_dir() and p.name not in IGNORED
    ):
        yield from feature_problems(feature)


class StructureChecker(BaseTokenChecker):
    name: str = "structure"
    msgs: dict[str, MessageDefinitionTuple] = {  # noqa: RUF012 -- BaseChecker declares it this way
        "E9030": ("%s", "structure-layout", "Every feature has the same files, nothing else."),
        "E9031": ("%s gets around a structure check", "structure-bypass", "Fix the code instead."),
    }

    @override
    def process_tokens(self, tokens: list[tokenize.TokenInfo]) -> None:
        for token in tokens:
            if token.type == tokenize.COMMENT and BYPASS_COMMENTS.search(token.string):
                self.add_message("structure-bypass", line=token.start[0], args=(token.string,))

    def visit_call(self, node: nodes.Call) -> None:
        func = node.func
        name = func.name if isinstance(func, nodes.Name) else None
        name = func.attrname if isinstance(func, nodes.Attribute) else name
        if name in DYNAMIC_IMPORTS:
            self.add_message("structure-bypass", line=node.lineno, args=(f"{name}()",))

    @override
    def close(self) -> None:
        for problem in layout_problems():
            self.add_message("structure-layout", line=1, args=(problem,))


def register(linter: PyLinter) -> None:
    linter.register_checker(StructureChecker(linter))
