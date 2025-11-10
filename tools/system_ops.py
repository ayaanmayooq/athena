import subprocess
from .base import Tool

def _open_app(app_name: str) -> str:
    try:
        subprocess.run(["open", "-a", app_name], check=True)
        return f"Opened app '{app_name}'."
    except Exception as e:
        return f"Failed to open app '{app_name}': {e}"

open_app_tool = Tool(
    name="open_app",
    description="Open a macOS application by name.",
    parameters_schema={
        "type": "object",
        "properties": {"app_name": {"type": "string"}},
        "required": ["app_name"],
    },
    func=_open_app,
)
