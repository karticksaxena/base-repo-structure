"""NestJS-style feature modules: every folder in src/app/features/ has the same files."""

from pathlib import Path

import pytest

FEATURES_DIR = Path(__file__).resolve().parents[1] / "src" / "app" / "features"
REQUIRED_FILES = (
    "__init__.py",
    "router.py",
    "service.py",
    "repository.py",
    "schemas.py",
    "dependencies.py",
)
FEATURES = sorted(p for p in FEATURES_DIR.iterdir() if p.is_dir() and p.name != "__pycache__")


@pytest.mark.unit
@pytest.mark.parametrize("feature", FEATURES, ids=[p.name for p in FEATURES])
def test_feature_has_required_files(feature: Path) -> None:
    missing = [name for name in REQUIRED_FILES if not (feature / name).is_file()]
    assert not missing, f"src/app/features/{feature.name}/ is missing: {', '.join(missing)}"
