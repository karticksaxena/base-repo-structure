"""Pylint plugin: only a feature's dependencies.py builds services and repositories.

dishka creates them from each feature's Provider (Nest module providers) and hands them to whoever
asks in `__init__`. A `*Service(...)` or `*Repository(...)` call anywhere else in src/ skips the
container: its scope is ignored and tests can't swap in a fake. So does FastAPI's
`Depends(SomeService)`, which builds the class itself. Tests may build them directly.
Loaded from pyproject.toml ([tool.pylint.main]); lives in tests/ because it is a structure check,
like test_structure.py.
"""

from astroid import nodes  # pyright: ignore[reportMissingTypeStubs] -- astroid ships no stubs
from pylint.checkers import BaseChecker
from pylint.lint import PyLinter
from pylint.typing import MessageDefinitionTuple

PROVIDED = ("Service", "Repository")


def name_of(expr: nodes.NodeNG) -> str | None:
    # By name only: an alias, `type(x)()`, `cls()`, `getattr()`, `Depends(X.factory)` slip through
    if isinstance(expr, nodes.Name):
        return expr.name
    if isinstance(expr, nodes.Attribute):
        return expr.attrname
    return None


def depends_target(call: nodes.Call) -> nodes.NodeNG | None:
    """The class or function handed to `Depends(...)`, positional or `dependency=`."""
    if call.args:
        return call.args[0]
    return next((kw.value for kw in call.keywords or () if kw.arg == "dependency"), None)


class ConstructionChecker(BaseChecker):
    name: str = "construction"
    msgs: dict[str, MessageDefinitionTuple] = {  # noqa: RUF012 -- BaseChecker declares it this way
        "E9001": (
            "%s() built outside dependencies.py; take it as an __init__ parameter",
            "construction-outside-provider",
            "Services and repositories are built only by the feature's dishka Provider.",
        ),
        "E9002": (
            "Depends(%s) builds it outside dishka; take FromDishka[%s] instead",
            "construction-through-depends",
            "FastAPI's Depends() must not build services or repositories — dishka does.",
        ),
    }

    def visit_call(self, node: nodes.Call) -> None:
        module = node.root().name
        if not module.startswith("src.") or module.endswith(".dependencies"):
            return
        name = name_of(node.func)
        if name == "Depends":
            target = depends_target(node)
            provided = name_of(target) if target is not None else None
            if provided and provided.endswith(PROVIDED):
                self.add_message("construction-through-depends", node=node, args=(provided,) * 2)
        elif name and name.endswith(PROVIDED):
            self.add_message("construction-outside-provider", node=node, args=(name,))


def register(linter: PyLinter) -> None:
    linter.register_checker(ConstructionChecker(linter))
