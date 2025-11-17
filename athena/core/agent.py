from __future__ import annotations

import json
from typing import List

from athena.core.config import settings
from athena.core.llm import LLMClient
from athena.core.logging import logger
from athena.core.schema import Message, ToolCall
from athena.core.tool_registry import tool_registry
from athena.memory.db import get_session
from athena.memory.models import MessageORM, ensure_db_initialized


class Agent:
    """
    Single-agent orchestration:
    - loads recent history from DB
    - calls LLM with tools
    - executes tools
    - returns final answer
    """

    def __init__(self, llm_client: LLMClient | None = None) -> None:
        self.llm = llm_client or LLMClient()

    def _load_history(self, user_id: str) -> List[Message]:
        session = get_session()
        q = (
            session.query(MessageORM)
            .filter(MessageORM.user_id == user_id)
            .order_by(MessageORM.created_at.desc())
            .limit(settings.max_history_messages)
        )
        rows = list(reversed(q.all()))
        session.close()

        return [
            Message(
                role=row.role,
                content=row.content,
                tool_name=row.tool_name,
                created_at=row.created_at,
            )
            for row in rows
        ]

    def _save_message(self, user_id: str, msg: Message) -> None:
        session = get_session()
        row = MessageORM(
            user_id=user_id,
            role=msg.role,
            content=msg.content,
            tool_name=msg.tool_name,
        )
        session.add(row)
        session.commit()
        session.close()

    def run(self, user_id: str, new_user_message: str) -> str:
        """
        One user turn.
        """
        logger.info("Agent.run(user_id=%s)", user_id)

        history = self._load_history(user_id)
        user_msg = Message(role="user", content=new_user_message)
        history.append(user_msg)

        # First call with tools enabled
        resp = self.llm.chat(
            messages=history,
            tools=tool_registry.list_schemas(),
            tool_choice="auto",
        )
        choice = resp.choices[0]
        assistant = choice.message

        # Convert assistant message into our Message model
        tool_calls_models: List[ToolCall] = []
        if getattr(assistant, "tool_calls", None):
            for tc in assistant.tool_calls:
                tool_calls_models.append(
                    ToolCall(
                        id=tc.id,
                        type=tc.type,
                        function={
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    )
                )

        assistant_msg = Message(
            role="assistant",
            content=assistant.content or "",
            tool_calls=tool_calls_models or None,
        )
        history.append(assistant_msg)

        # Handle tool calls, if any
        tool_calls = getattr(assistant, "tool_calls", None)
        if tool_calls:
            for tc in tool_calls:
                tool_name = tc.function.name
                tool_args = tc.function.arguments
                if isinstance(tool_args, str):
                    try:
                        tool_args = json.loads(tool_args)
                    except json.JSONDecodeError:
                        logger.error(
                            "Failed to parse tool arguments for %s: %s",
                            tool_name,
                            tool_args,
                        )
                        tool_args = {}

                func = tool_registry.get(tool_name)
                # Force correct user_id when tool expects it; model often guesses.
                if "user_id" in getattr(func, "_athena_tool_meta", {}).get(
                    "parameters", {}
                ).get("properties", {}):
                    tool_args = dict(tool_args)
                    tool_args["user_id"] = user_id
                logger.info("Calling tool %s with %s", tool_name, tool_args)
                result = func(**tool_args)

                tool_msg = Message(
                    role="tool",
                    content=str(result),
                    tool_name=tool_name,
                    tool_call_id=tc.id,
                )
                history.append(tool_msg)

            # Second pass, no tools (just synthesize)
            resp2 = self.llm.chat(
                messages=history,
                tools=None,
                tool_choice="none",
            )
            final_choice = resp2.choices[0]
            final_assistant = final_choice.message
            final_msg = Message(
                role="assistant",
                content=final_assistant.content or "",
            )
            history.append(final_msg)
            final_text = final_msg.content
        else:
            final_text = assistant_msg.content

        # Persist last user + last assistant message
        ensure_db_initialized()
        self._save_message(user_id, user_msg)
        self._save_message(user_id, Message(role="assistant", content=final_text))

        return final_text


# simple factory / singleton-ish pattern
_default_agent: Agent | None = None


def get_default_agent() -> Agent:
    global _default_agent
    if _default_agent is None:
        ensure_db_initialized()
        tool_registry.autodiscover()
        _default_agent = Agent()
    return _default_agent
