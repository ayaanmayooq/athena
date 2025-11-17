from __future__ import annotations

from typing import Any, Dict, List, Optional

from openai import OpenAI

from athena.core.config import settings
from athena.core.schema import Message, ToolSchema


class LLMClient:
    def __init__(
        self,
        api_key: Optional[str] = None,
        chat_model: Optional[str] = None,
        embedding_model: Optional[str] = None,
    ) -> None:
        self.api_key = api_key or settings.openai_api_key
        self.chat_model = chat_model or settings.openai_chat_model
        self.embedding_model = embedding_model or settings.openai_embedding_model
        self._client = OpenAI(api_key=self.api_key)

    def chat(
        self,
        messages: List[Message],
        tools: Optional[List[ToolSchema]] = None,
        tool_choice: Optional[str] = "auto",
    ) -> Any:
        """
        Wraps OpenAI chat completions. Returns the raw response.
        """
        openai_messages = []
        for m in messages:
            msg: Dict[str, Any] = {"role": m.role, "content": m.content}
            if m.tool_calls:
                msg["tool_calls"] = [tc.model_dump() for tc in m.tool_calls]
            if m.tool_call_id:
                msg["tool_call_id"] = m.tool_call_id
            openai_messages.append(msg)

        kwargs: dict = {
            "model": self.chat_model,
            "messages": openai_messages,
        }

        if tools:
            kwargs["tools"] = [t.model_dump() for t in tools]
            kwargs["tool_choice"] = tool_choice

        resp = self._client.chat.completions.create(**kwargs)
        return resp

    def embed(self, texts: List[str]) -> List[List[float]]:
        """
        Wraps OpenAI embeddings. Returns a list of vectors.
        """
        resp = self._client.embeddings.create(
            model=self.embedding_model,
            input=texts,
        )
        return [d.embedding for d in resp.data]
