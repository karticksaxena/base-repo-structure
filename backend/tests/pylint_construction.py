"""Pylint plugin: only a feature's dependencies.py builds services and repositories.

dishka creates them from each feature's Provider (Nest module providers) and hands them to whoever
asks in `__init__`. A `*Service(...)` or `*Repository(...)` call anywhere else in src/ skips the
container: its scope is ignored and tests can't swap in a fake. Tests may build them directly.
Loaded from pyproject.toml ([tool.pylint.main]); lives in tests/ because it is a structure check,
like test_structure.py.
"""

from astroid import nodes  # pyright: ignore[reportMissingTypeStubs] -- astroid ships no stubs
from pylint.checkers import BaseChecker
from pylint.lint import PyLinter
from pylint.typing import MessageDefinitionTuple

PROVIDED = ("Service", "Repository")


def called_name(call: nodes.Call) -> str | None:
    # Matches by name: an alias, `type(x)()`, `cls()` in a classmethod or `getattr()` slips through
    if isinstance(call.func, nodes.Name):
        return call.func.name
    if isinstance(call.func, nodes.Attribute):
        return call.func.attrname
    return None


class ConstructionChecker(BaseChecker):
    name: str = "construction"
    msgs: dict[str, MessageDefinitionTuple] = {  # noqa: RUF012 -- BaseChecker declares it this way
        "E9001": (
            "%s() built outside dependencies.py; take it as an __init__ parameter",
            "construction-outside-provider",
            "Services and repositories are built only by the feature's dishka Provider.",
        )
    }

    def visit_call(self, node: nodes.Call) -> None:
        module = node.root().name
        if not module.startswith("src.") or module.endswith(".dependencies"):
            return
        name = called_name(node)
        if name and name.endswith(PROVIDED):
            self.add_message("construction-outside-provider", node=node, args=(name,))


def register(linter: PyLinter) -> None:
    linter.register_checker(ConstructionChecker(linter))
