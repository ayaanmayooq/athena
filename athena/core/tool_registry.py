from __future__ import annotations

import importlib
import pkgutil
from typing import Any, Callable, Dict, List

from athena.core.schema import ToolSchema
from athena.core.tool_base import Tool


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: Dict[str, Callable[..., Any]] = {}
        self._schemas: Dict[str, ToolSchema] = {}

    def register_function(self, func: Callable[..., Any]) -> None:
        meta = getattr(func, "_athena_tool_meta", None)
        if not meta:
            return

        name: str = meta["name"]
        desc: str = meta["description"]
        params: dict = meta["parameters"]

        self._tools[name] = func
        self._schemas[name] = ToolSchema(
            function={
                "name": name,
                "description": desc,
                "parameters": params,
            }
        )

    def get(self, name: str) -> Callable[..., Any]:
        return self._tools[name]

    def list_schemas(self) -> List[ToolSchema]:
        return list(self._schemas.values())

    def autodiscover(self) -> None:
        """
        Import all modules in athena.tools and register decorated functions.
        """
        import athena.tools as tools_pkg

        for _, module_name, _ in pkgutil.iter_modules(tools_pkg.__path__):
            module = importlib.import_module(f"{tools_pkg.__name__}.{module_name}")
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                meta = getattr(attr, "_athena_tool_meta", None)
                if meta:
                    self.register_function(attr)


# global-ish registry for simple usage
tool_registry = ToolRegistry()
