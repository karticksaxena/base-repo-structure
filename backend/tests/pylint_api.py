"""Pylint plugin: the API rules of backend/CLAUDE.md (3, 5, 6, 9, 13), shown while you type.

Reads the source, so it sees what is written: a route added any way but a decorator, or a prefix
set in include_router(), would hide from it, and both are errors here. Loaded from pyproject.toml.
"""

import re
from pathlib import Path
from typing import override

from astroid import exceptions, nodes  # pyright: ignore[reportMissingTypeStubs] -- no stubs
from pylint.checkers import BaseChecker
from pylint.checkers.utils import safe_infer
from pylint.lint import PyLinter
from pylint.typing import MessageDefinitionTuple
from pylint_construction import name_of, real_name, return_annotation, route_decorators

VERBS = frozenset(
    {
        "add", "create", "delete", "do", "edit", "fetch", "get", "list", "make", "post", "put",
        "read", "remove", "replace", "run", "save", "search", "send", "set", "update",
    }
)  # fmt: skip
SINGULAR_ALLOWED = frozenset({"health", "ready"})  # /health, /health/ready
SECRET = re.compile(r"password|passwd|pwd|secret|api_?key|access_?token|credential", re.IGNORECASE)
ACTING_USER = re.compile(r"^(x[-_])?(user|account|tenant|org)", re.IGNORECASE)
SUCCESS_STATUS = {"post": ("HTTP_201_CREATED", "201"), "delete": ("HTTP_204_NO_CONTENT", "204")}
SOURCES = {"Query": "query", "Header": "header", "Path": "path", "Body": "body", "Cookie": "cookie"}
INJECTED = frozenset({"Request", "Response", "BackgroundTasks", "WebSocket"})
CONTAINERS = frozenset({"list", "dict", "set", "tuple", "Sequence", "Mapping"})
ALIAS_DEPTH = 4


def keyword(call: nodes.Call, name: str) -> nodes.NodeNG | None:
    return next((k.value for k in call.keywords or () if k.arg == name), None)


def literal(expr: nodes.NodeNG | None) -> str | None:
    if not isinstance(expr, nodes.Const):
        return None
    value: object = expr.value  # pyright: ignore[reportAny] -- astroid types it as Any
    return value if isinstance(value, str) else None


def resolve_alias(expr: nodes.NodeNG, depth: int = ALIAS_DEPTH) -> nodes.NodeNG:
    """`Limit` in a route is `Annotated[int, Query()]` in common/schemas.py: follow it there."""
    if depth == 0 or not isinstance(expr, nodes.Name):
        return expr
    _, found = expr.lookup(expr.name)
    for statement in found:
        if isinstance(statement, nodes.AssignName) and isinstance(statement.parent, nodes.Assign):
            return resolve_alias(statement.parent.value, depth - 1)
        if isinstance(statement, nodes.ImportFrom):
            try:
                module = statement.do_import_module()
                _, targets = module.lookup(statement.real_name(expr.name))
            except exceptions.AstroidError:
                return expr
            for target in targets:
                if isinstance(target, nodes.AssignName) and isinstance(target.parent, nodes.Assign):
                    return resolve_alias(target.parent.value, depth - 1)
    return expr


def inherits(expr: nodes.NodeNG, name: str) -> bool:
    inferred = expr if isinstance(expr, nodes.ClassDef) else safe_infer(expr)
    if not isinstance(inferred, nodes.ClassDef):
        return False
    return inferred.name == name or any(a.name == name for a in inferred.ancestors())


def is_schema(expr: nodes.NodeNG) -> bool:
    return inherits(expr.value if isinstance(expr, nodes.Subscript) else expr, "BaseSchema")


def unwrap(annotation: nodes.NodeNG) -> tuple[nodes.NodeNG, list[nodes.Call]]:
    """`Annotated[int, Query()]` -> the type, and the calls that say where the value comes from."""
    resolved = resolve_alias(annotation)
    if isinstance(resolved, nodes.Subscript) and name_of(resolved.value) == "Annotated":
        items = resolved.slice.elts if isinstance(resolved.slice, nodes.Tuple) else []
        if items and isinstance(items[0], nodes.NodeNG):
            return resolve_alias(items[0]), [c for c in items[1:] if isinstance(c, nodes.Call)]
    return resolved, []


def parameter_source(name: str, annotation: nodes.NodeNG, path: str) -> str:
    """Where FastAPI reads this parameter from."""
    core, markers = unwrap(annotation)
    for marker in markers:
        marker_name = real_name(marker.func) or ""
        if marker_name in {"Depends", "Security"}:
            return "group"
        if marker_name in SOURCES:
            return SOURCES[marker_name]
    head = name_of(core.value) if isinstance(core, nodes.Subscript) else name_of(core)
    if head == "FromDishka":
        return "dishka"
    if head in INJECTED:
        return "injected"
    if "{" + name + "}" in path:
        return "path"
    return "body" if is_schema(core) or head in CONTAINERS else "query"


def group_fields(annotation: nodes.NodeNG) -> list[str]:
    """The query parameters a bare `Annotated[Filters, Depends()]` adds."""
    core, _ = unwrap(annotation)
    inferred = safe_infer(core)
    if not isinstance(inferred, nodes.ClassDef):
        return []
    return [
        s.target.name
        for s in inferred.body
        if isinstance(s, nodes.AnnAssign) and isinstance(s.target, nodes.AssignName)
    ]


def route_parameters(node: nodes.FunctionDef, path: str) -> list[tuple[str, str]]:
    """(name, source) for each parameter, with grouped parameters expanded."""
    args = node.args
    pairs = [
        *zip(args.args or [], args.annotations or [], strict=False),
        *zip(args.kwonlyargs or [], args.kwonlyargs_annotations or [], strict=False),
    ]
    found: list[tuple[str, str]] = []
    for argument, annotation in pairs:
        if annotation is None:
            continue
        source = parameter_source(argument.name, annotation, path)
        if source == "group":
            found += [(field, "query") for field in group_fields(annotation)]
        else:
            found.append((argument.name, source))
    return found


def router_prefix(decorator: nodes.Call) -> str:
    target = decorator.func.expr if isinstance(decorator.func, nodes.Attribute) else None
    if not isinstance(target, nodes.Name):
        return ""
    _, found = target.lookup(target.name)
    for statement in found:
        if isinstance(statement, nodes.AssignName) and isinstance(statement.parent, nodes.Assign):
            value = statement.parent.value
            if isinstance(value, nodes.Call):
                return literal(keyword(value, "prefix")) or ""
    return ""


def bad_segments(path: str) -> list[str]:
    segments = [s for s in path.split("/") if s and not s.startswith("{")]
    return [
        s
        for s in segments
        if re.split(r"[-_]", s)[0].lower() in VERBS
        or not (s.endswith("s") or s in SINGULAR_ALLOWED)
    ]


def message(text: str, symbol: str) -> MessageDefinitionTuple:
    return (text, symbol, text)


class ApiChecker(BaseChecker):
    name: str = "api-rules"
    msgs: dict[str, MessageDefinitionTuple] = {  # noqa: RUF012 -- BaseChecker declares it this way
        "E9010": message("path %s: use plural nouns and ids, no verbs", "route-path"),
        "E9011": message("return a BaseSchema, Page[T] or None, not %s", "route-return-type"),
        "E9012": message("route functions are named <verb>_<noun>: %s", "route-name"),
        "E9013": message("route function name %s is already used", "route-name-repeated"),
        "E9014": message("%s returns %s", "route-status"),
        "E9015": message("%s", "route-parameter"),
        "E9016": message("Page[T] routes take limit: Limit and offset: Offset", "route-paging"),
        "E9017": message("APIRouter needs route_class=DishkaRoute", "router-without-dishka"),
        "E9018": message("%s: declare routes with a decorator", "route-not-decorated"),
        "E9019": message("set prefix= on the APIRouter, not in include_router", "include-prefix"),
        "E9020": message("field %s needs Field(description=...)", "schema-field-undocumented"),
        "E9021": message("BaseSchema's extra='forbid' must not change", "schema-not-strict"),
        "E9022": message("secret setting %s must be SecretStr", "setting-not-secretstr"),
        "E9023": message("mark %s @pytest.mark.unit or integration", "test-without-mark"),
    }

    def __init__(self, linter: PyLinter) -> None:
        super().__init__(linter)
        self.route_names: set[str] = set()

    @override
    def open(self) -> None:
        self.route_names = set()

    def visit_call(self, node: nodes.Call) -> None:
        if not node.root().name.startswith("src."):
            return
        name = name_of(node.func)
        if name in {"add_api_route", "add_route", "add_websocket_route"}:
            self.add_message("route-not-decorated", node=node, args=(name,))
        elif name == "include_router" and keyword(node, "prefix") is not None:
            self.add_message("include-prefix", node=node)
        elif (
            name == "APIRouter"
            and ".routers." in node.root().name
            and keyword(node, "route_class") is None
        ):
            self.add_message("router-without-dishka", node=node)

    def visit_classdef(self, node: nodes.ClassDef) -> None:
        if not node.root().name.startswith("src."):
            return
        if inherits(node, "BaseSettings"):
            self._check_settings(node)
        if inherits(node, "BaseSchema"):
            self._check_schema(node)

    def _check_settings(self, node: nodes.ClassDef) -> None:
        for statement in node.body:
            if isinstance(statement, nodes.AnnAssign) and isinstance(
                statement.target, nodes.AssignName
            ):
                field = statement.target.name
                if SECRET.search(field) and name_of(statement.annotation) != "SecretStr":
                    self.add_message("setting-not-secretstr", node=statement, args=(field,))

    def _check_schema(self, node: nodes.ClassDef) -> None:
        for statement in node.body:
            if isinstance(statement, nodes.AnnAssign) and isinstance(
                statement.target, nodes.AssignName
            ):
                self._check_schema_field(statement, statement.target.name)
            elif isinstance(statement, nodes.Assign) and statement.targets:
                target = statement.targets[0]
                if isinstance(target, nodes.AssignName) and target.name == "model_config":
                    self._check_config(statement, statement.value)

    def _check_schema_field(self, statement: nodes.AnnAssign, field: str) -> None:
        if field == "model_config":
            self._check_config(statement, statement.value)
        elif not (
            isinstance(statement.value, nodes.Call) and real_name(statement.value.func) == "Field"
        ):
            self.add_message("schema-field-undocumented", node=statement, args=(field,))

    def _check_config(self, statement: nodes.NodeNG, value: nodes.NodeNG | None) -> None:
        extra = keyword(value, "extra") if isinstance(value, nodes.Call) else None
        if extra is not None and literal(extra) != "forbid":
            self.add_message("schema-not-strict", node=statement)

    def visit_functiondef(self, node: nodes.FunctionDef) -> None:
        self._check_test_mark(node)
        if not node.root().name.startswith("src."):
            return
        for decorator in route_decorators(node):
            self._check_route(node, decorator)

    def visit_asyncfunctiondef(self, node: nodes.AsyncFunctionDef) -> None:
        self.visit_functiondef(node)

    def _check_test_mark(self, node: nodes.FunctionDef) -> None:
        file = node.root().file or ""
        if "/tests/" not in file or not Path(file).name.startswith("test_"):
            return
        if not node.name.startswith("test_"):
            return
        marks = [d.as_string() for d in (node.decorators.nodes if node.decorators else [])]
        if not any("mark.unit" in m or "mark.integration" in m for m in marks):
            self.add_message("test-without-mark", node=node, args=(node.name,))

    def _check_route(self, node: nodes.FunctionDef, decorator: nodes.Call) -> None:
        method = decorator.func.attrname if isinstance(decorator.func, nodes.Attribute) else ""
        raw = literal(decorator.args[0]) if decorator.args else literal(keyword(decorator, "path"))
        path = router_prefix(decorator) + (raw if raw is not None else "/non-literal-path")
        if bad_segments(path):
            self.add_message("route-path", node=node, args=(path,))
        self._check_name(node)
        self._check_status(node, decorator, method)
        self._check_return(node)
        self._check_parameters(node, method, path)

    def _check_name(self, node: nodes.FunctionDef) -> None:
        if "_" not in node.name or node.name.split("_")[0] not in VERBS:
            self.add_message("route-name", node=node, args=(node.name,))
        if node.name in self.route_names:
            self.add_message("route-name-repeated", node=node, args=(node.name,))
        self.route_names.add(node.name)

    def _check_status(self, node: nodes.FunctionDef, decorator: nodes.Call, method: str) -> None:
        expected = SUCCESS_STATUS.get(method)
        if expected is None:
            return
        status = keyword(decorator, "status_code")
        text = status.as_string() if status is not None else ""
        if not text.endswith(expected):
            self.add_message("route-status", node=node, args=(method.upper(), expected[1]))

    def _check_return(self, node: nodes.FunctionDef) -> None:
        annotation = return_annotation(node)
        if annotation is None:
            return  # Ruff ANN201 already fails this
        resolved = resolve_alias(annotation)
        is_none = isinstance(resolved, nodes.Const) and resolved.value is None  # pyright: ignore[reportAny] -- astroid types it as Any
        if not (is_none or is_schema(resolved) or inherits(resolved, "Response")):
            self.add_message("route-return-type", node=node, args=(annotation.as_string(),))

    def _check_parameters(self, node: nodes.FunctionDef, method: str, path: str) -> None:
        parameters = route_parameters(node, path)
        for name, source in parameters:
            problem = self._parameter_problem(name, source, method)
            if problem:
                self.add_message("route-parameter", node=node, args=(problem,))
        returns = return_annotation(node)
        annotation = resolve_alias(returns) if returns is not None else None
        paged = isinstance(annotation, nodes.Subscript) and name_of(annotation.value) == "Page"
        if paged and not {"limit", "offset"} <= {name for name, _ in parameters}:
            self.add_message("route-paging", node=node)

    @staticmethod
    def _parameter_problem(name: str, source: str, method: str) -> str | None:
        if source == "query" and method != "get":
            return f"{name}: query parameters are for GET only"
        if source == "body" and method in {"get", "delete"}:
            return f"{name}: GET and DELETE take no body"
        if source in {"query", "path"} and SECRET.search(name):
            return f"{name}: URLs get logged, send secrets in the body or a header"
        if source == "header" and ACTING_USER.search(name):
            return f"{name}: the acting user comes from auth (a provider)"
        return None


def register(linter: PyLinter) -> None:
    linter.register_checker(ApiChecker(linter))
