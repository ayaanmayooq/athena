from dataclasses import dataclass
from typing import Any, Callable, Dict

@dataclass
class Tool:
    name: str
    description: str
    parameters_schema: Dict[str, Any]
    func: Callable[..., Any]

    def __call__(self, **kwargs):
        return self.func(**kwargs)
