"""Pylint plugin: the backend rules that need the code's shape, not just its imports.

Only a feature's dependencies.py builds services and repositories: dishka creates them from each
feature's Provider (Nest module providers) and hands them to whoever asks in `__init__`. A
`*Service(...)` or `*Repository(...)` call anywhere else in src/ skips the container: its scope is
ignored and tests can't swap in a fake. So does FastAPI's `Depends(SomeService)`, which builds the
class itself. Tests may build them directly. The rest are rules 3, 5, 6, 7 of backend/CLAUDE.md.
Loaded from pyproject.toml ([tool.pylint.main]).
"""

import re

from astroid import nodes  # pyright: ignore[reportMissingTypeStubs] -- astroid ships no stubs
from pylint.checkers import BaseChecker
from pylint.checkers.utils import safe_infer
from pylint.lint import PyLinter
from pylint.typing import MessageDefinitionTuple

PROVIDED = ("Service", "Repository")
ROUTE_METHODS = {"get", "post", "put", "patch", "delete", "head", "options", "api_route"}
LOG_METHODS = {"trace", "debug", "info", "success", "warning", "error", "critical", "exception"}
LOGIC = (
    nodes.If, nodes.IfExp, nodes.For, nodes.While, nodes.Match, nodes.Try, nodes.BinOp,
    nodes.BoolOp, nodes.Compare, nodes.ListComp, nodes.SetComp, nodes.DictComp, nodes.GeneratorExp,
)  # fmt: skip
MAX_ROUTE_STATEMENTS = 3  # parse, call a service, return
CLASS_VALUE_OK = frozenset({"isinstance", "issubclass", "cast", "Depends", "Security"})
DYNAMIC_BUILDERS = {"type", "getattr"}
PERCENT_PLACEHOLDER = re.compile(r"%[sdrif]")
SERVICE_TYPE = re.compile(r"\w*Service\b")


def name_of(expr: nodes.NodeNG) -> str | None:
    if isinstance(expr, nodes.Name):
        return expr.name
    if isinstance(expr, nodes.Attribute):
        return expr.attrname
    return None


def real_name(expr: nodes.NodeNG) -> str | None:
    """Follows aliases: after `Repo = ItemRepository`, `Repo` is still ItemRepository."""
    inferred = safe_infer(expr)
    if isinstance(inferred, nodes.ClassDef | nodes.FunctionDef):
        return inferred.name
    return name_of(expr)


def provided_class(expr: nodes.NodeNG) -> str | None:
    """The service or repository class this name or attribute points to, aliases followed."""
    if not isinstance(expr, nodes.Name | nodes.Attribute):
        return None
    inferred = safe_infer(expr)
    if isinstance(inferred, nodes.ClassDef) and inferred.name.endswith(PROVIDED):
        return inferred.name
    return None


def service_parameters(node: nodes.FunctionDef) -> set[str]:
    """Parameters annotated with a *Service class, e.g. `service: FromDishka[ItemService]`."""
    args = node.args
    names = [*(args.args or []), *args.kwonlyargs]
    annotations = [*args.annotations, *args.kwonlyargs_annotations]
    return {
        arg.name
        for arg, annotation in zip(names, annotations, strict=False)
        if annotation is not None and SERVICE_TYPE.search(annotation.as_string())
    }


def depends_target(call: nodes.Call) -> nodes.NodeNG | None:
    """The class or function handed to `Depends(...)`, positional or `dependency=`."""
    if call.args:
        return call.args[0]
    return next((kw.value for kw in call.keywords or () if kw.arg == "dependency"), None)


def has_keyword(call: nodes.Call, name: str) -> bool:
    return any(kw.arg == name for kw in call.keywords or ())


def is_percent_log(call: nodes.Call) -> bool:
    """`logger.info("x %s", v)`: loguru only formats `{}`, so this writes a literal `%s`."""
    func = call.func
    if not (isinstance(func, nodes.Attribute) and func.attrname in LOG_METHODS):
        return False
    if name_of(func.expr) != "logger" or len(call.args) < 2:
        return False
    first = call.args[0]
    if not isinstance(first, nodes.Const):
        return False
    text: object = first.value  # pyright: ignore[reportAny] -- astroid types it as Any
    return isinstance(text, str) and bool(PERCENT_PLACEHOLDER.search(text))


def return_annotation(node: nodes.FunctionDef) -> nodes.NodeNG | None:
    return node.returns  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType] -- astroid has no stubs


def route_decorators(node: nodes.FunctionDef) -> list[nodes.Call]:
    found = node.decorators.nodes if node.decorators else []
    return [
        d
        for d in found
        if isinstance(d, nodes.Call)
        and isinstance(d.func, nodes.Attribute)
        and d.func.attrname in ROUTE_METHODS
    ]


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
        "E9003": (
            "Depends(%s): objects come from dishka (FromDishka); bare Depends() groups parameters",
            "depends-with-target",
            "FastAPI's Depends is only for grouping request parameters.",
        ),
        "E9004": (
            "Field() has no description=",
            "field-without-description",
            "Every Field() documents itself for OpenAPI.",
        ),
        "E9005": (
            "response_model= repeats the return type; remove it",
            "redundant-response-model",
            "response_model is only for returning a different type than the public schema.",
        ),
        "E9006": (
            "logic in a route (branch, loop, arithmetic, over 3 statements); use services/",
            "logic-in-route",
            "Routes parse the request, call a service and return its result.",
        ),
        "E9007": (
            "loguru only formats {}; this logs a literal %% placeholder",
            "percent-log-args",
            "Use logger.info('x {}', value).",
        ),
        "E9008": (
            "%s passed around as a value; dishka builds it, ask for an instance in __init__",
            "provided-class-as-value",
            "A class handed to a call can be built anywhere, skipping dishka.",
        ),
        "E9009": (
            "route %s; one service call, nothing else (functions, a second service)",
            "route-calls-beyond-service",
            "Routes call a single service method and return its result.",
        ),
    }

    def visit_call(self, node: nodes.Call) -> None:
        module = node.root().name
        if not module.startswith("src."):
            return
        name = real_name(node.func)
        if name == "Field" and not has_keyword(node, "description"):
            self.add_message("field-without-description", node=node)
        if is_percent_log(node):
            self.add_message("percent-log-args", node=node)
        if module.endswith(".dependencies"):
            return
        self._check_class_values(node, name)
        if isinstance(node.func, nodes.Call) and name_of(node.func.func) in DYNAMIC_BUILDERS:
            self.add_message("construction-outside-provider", node=node, args=("type(x)/getattr",))
        elif name in {"Depends", "Security"}:
            self._check_depends(node)
        elif name and name.endswith(PROVIDED):
            self.add_message("construction-outside-provider", node=node, args=(name,))
        elif isinstance(node.func, nodes.Attribute) and node.func.attrname == "__new__":
            built = provided_class(node.func.expr)
            if built:
                self.add_message("construction-outside-provider", node=node, args=(built,))

    def _check_class_values(self, node: nodes.Call, name: str | None) -> None:
        if name in CLASS_VALUE_OK:
            return
        values = [*node.args, *(kw.value for kw in node.keywords or ())]
        for value in values:
            held = provided_class(value)
            if held:
                self.add_message("provided-class-as-value", node=node, args=(held,))

    def _check_depends(self, node: nodes.Call) -> None:
        target = depends_target(node)
        if target is None:
            return
        provided = real_name(target)
        if provided and provided.endswith(PROVIDED):
            self.add_message("construction-through-depends", node=node, args=(provided,) * 2)
        else:
            self.add_message("depends-with-target", node=node, args=(provided or "...",))

    def visit_functiondef(self, node: nodes.FunctionDef) -> None:
        module = node.root().name
        decorators = route_decorators(node)
        if not module.startswith("src.") or not decorators:
            return
        annotation = return_annotation(node)
        returns = annotation.as_string() if annotation is not None else None
        for call in decorators:
            model = next((k.value for k in call.keywords or () if k.arg == "response_model"), None)
            if model is not None and model.as_string() == returns:
                self.add_message("redundant-response-model", node=node)
        body_has_logic = any(next(s.nodes_of_class(LOGIC), None) is not None for s in node.body)
        if body_has_logic or len(node.body) > MAX_ROUTE_STATEMENTS:
            self.add_message("logic-in-route", node=node)
        self._check_route_calls(node)

    def _check_route_calls(self, node: nodes.FunctionDef) -> None:
        services = service_parameters(node)
        service_calls = 0
        for statement in node.body:
            for call in statement.nodes_of_class(nodes.Call):
                func = call.func
                if isinstance(func, nodes.Attribute) and name_of(func.expr) in services:
                    service_calls += 1
                    continue
                inferred = safe_infer(func)
                if inferred is not None and not isinstance(inferred, nodes.ClassDef):
                    self.add_message(
                        "route-calls-beyond-service", node=call, args=(f"calls {name_of(func)}()",)
                    )
        if service_calls > 1:
            self.add_message(
                "route-calls-beyond-service",
                node=node,
                args=(f"makes {service_calls} service calls",),
            )

    def visit_asyncfunctiondef(self, node: nodes.AsyncFunctionDef) -> None:
        self.visit_functiondef(node)


def register(linter: PyLinter) -> None:
    linter.register_checker(ConstructionChecker(linter))
