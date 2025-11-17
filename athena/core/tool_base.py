from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, Protocol


class Tool(Protocol):
    name: str
    description: str
    parameters: Dict[str, Any]

    def __call__(self, **kwargs: Any) -> Any: ...


class BaseTool(ABC):
    name: str
    description: str
    parameters: Dict[str, Any]

    @abstractmethod
    def __call__(self, **kwargs: Any) -> Any:
        ...


def tool(
    name: str,
    description: str,
    parameters: Dict[str, Any],
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    Decorator to tag a function as an Athena tool.
    """

    def wrapper(func: Callable[..., Any]) -> Callable[..., Any]:
        func._athena_tool_meta = {
            "name": name,
            "description": description,
            "parameters": parameters,
        }
        return func

    return wrapper
