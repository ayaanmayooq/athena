import json
from typing import Any, Dict, List
from openai import OpenAI
from tools import ALL_TOOLS, get_tool_schemas_for_openai
from .config import SYSTEM_PROMPT, MODEL_NAME, MAX_TOOL_CALLS

client = OpenAI()

def run_agent(user_input: str) -> str:
    messages: List[Dict[str, Any]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_input},
    ]
    tools = get_tool_schemas_for_openai()
    tool_calls_used = 0

    while True:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            tools=tools,
        )
        msg = response.choices[0].message

        # If a tool call is requested
        if msg.tool_calls:
            if tool_calls_used >= MAX_TOOL_CALLS:
                messages.append({
                    "role": "assistant",
                    "content": "Too many tool calls; summarizing instead."
                })
                continue

            tool_calls_used += len(msg.tool_calls)
            for tc in msg.tool_calls:
                name = tc.function.name
                args = json.loads(tc.function.arguments or "{}")
                tool = ALL_TOOLS.get(name)
                if not tool:
                    result = f"Tool '{name}' not found."
                else:
                    result = tool(**args)

                # Add results to conversation
                messages.append({"role": "assistant", "tool_calls": [tc.model_dump()]})
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "name": name,
                    "content": str(result),
                })
            continue

        # Otherwise, final answer
        messages.append({"role": "assistant", "content": msg.content})
        return msg.content
