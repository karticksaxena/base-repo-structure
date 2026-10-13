"""NestJS-style layout: every feature has the same layer folders, and nothing sits outside them.

Import rules between the folders are checked by tach (tach.toml + each feature's
tach.domain.toml). This test covers what tach can't see: files that import nothing, a feature whose
layer rules were edited, missing tests, and code or comments that switch the structure checks off.
"""

import re
import tomllib
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = BACKEND_DIR / "src"
APP_DIR = SRC_DIR / "app"
FEATURES_DIR = APP_DIR / "features"
TESTS_DIR = BACKEND_DIR / "tests" / "features"
TEMPLATE_RULES = FEATURES_DIR / "items" / "tach.domain.toml"  # the feature every new one copies
REQUIRED_FILES = ("__init__.py", "dependencies.py", "tach.domain.toml")
REQUIRED_PACKAGES = ("routers", "services", "repositories", "schemas", "constants", "utils")
APP_ENTRIES = ("__init__.py", "main.py", "app_module.py", "core", "common", "features")
IGNORED = ("__pycache__",)
# Code or comments that would get around a structure check: tach, Ruff's banned imports, import
# cycles, and dynamic imports tach can't see
BYPASSES = re.compile(
    r"tach-ignore|noqa:[^#\n]*TID|reportImportCycles|\b__import__\(|import_module\("
)
FEATURES = sorted(p for p in FEATURES_DIR.iterdir() if p.is_dir() and p.name not in IGNORED)
IDS = [p.name for p in FEATURES]


def entries(folder: Path) -> set[str]:
    return {p.name for p in folder.iterdir() if p.name not in IGNORED}


@pytest.mark.unit
@pytest.mark.parametrize("feature", FEATURES, ids=IDS)
def test_feature_has_required_files(feature: Path) -> None:
    missing = [name for name in REQUIRED_FILES if not (feature / name).is_file()]
    missing += [
        f"{name}/" for name in REQUIRED_PACKAGES if not (feature / name / "__init__.py").is_file()
    ]
    assert not missing, f"src/app/features/{feature.name}/ is missing: {', '.join(missing)}"


@pytest.mark.unit
@pytest.mark.parametrize("feature", FEATURES, ids=IDS)
def test_feature_has_nothing_else(feature: Path) -> None:
    extra = sorted(entries(feature) - {*REQUIRED_FILES, *REQUIRED_PACKAGES})
    assert not extra, (
        f"src/app/features/{feature.name}/ has entries outside the layout: {', '.join(extra)}"
        " — move the code into a layer folder"
    )


@pytest.mark.unit
@pytest.mark.parametrize("feature", FEATURES, ids=IDS)
def test_feature_layer_rules_match_the_template(feature: Path) -> None:
    rules = feature / "tach.domain.toml"
    assert rules.read_text() == TEMPLATE_RULES.read_text(), (
        f"src/app/features/{feature.name}/tach.domain.toml differs from"
        " features/items/tach.domain.toml — every feature has the same layer rules"
    )


@pytest.mark.unit
@pytest.mark.parametrize("feature", FEATURES, ids=IDS)
def test_feature_has_tests(feature: Path) -> None:
    tests = list((TESTS_DIR / feature.name).glob("test_*.py"))
    assert tests, f"tests/features/{feature.name}/ has no test_*.py files"


@pytest.mark.unit
def test_app_has_nothing_else() -> None:
    extra = sorted(entries(SRC_DIR) - {"__init__.py", "app"})
    extra += sorted(f"app/{name}" for name in entries(APP_DIR) - set(APP_ENTRIES))
    extra += sorted(
        f"app/features/{name}"
        for name in entries(FEATURES_DIR) - {"__init__.py"}
        if not (FEATURES_DIR / name).is_dir()
    )
    assert not extra, f"src/ has entries outside the layout: {', '.join(extra)}"


@pytest.mark.unit
def test_core_files_have_layer_rules() -> None:
    config: dict[str, list[dict[str, str]]] = tomllib.loads((BACKEND_DIR / "tach.toml").read_text())
    modules = {module["path"] for module in config["modules"]}
    core_names = entries(APP_DIR / "core") - {"__init__.py"}
    missing = sorted(n for n in core_names if f"src.app.core.{Path(n).stem}" not in modules)
    assert not missing, f"src/app/core/ entries without a module in tach.toml: {', '.join(missing)}"


@pytest.mark.unit
def test_nothing_gets_around_structure_checks() -> None:
    found = [
        f"{path.relative_to(BACKEND_DIR)}:{number}"
        for path in sorted(SRC_DIR.rglob("*.py"))
        for number, line in enumerate(path.read_text().splitlines(), start=1)
        if BYPASSES.search(line)
    ]
    assert not found, f"code that gets around a structure check: {', '.join(found)}"
