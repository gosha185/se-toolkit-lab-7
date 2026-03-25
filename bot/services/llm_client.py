"""LLM client for intent classification and tool use.

Provides methods to call the LLM with tool definitions.
Uses OpenAI-compatible API format.
"""

import json
import sys
from typing import Any

import httpx


class LLMError(Exception):
    """Base exception for LLM errors."""
    pass


class LLMClient:
    """Client for LLM API with tool calling support."""

    def __init__(self, api_key: str, base_url: str, model: str):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self._headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

    async def chat(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        tool_choice: str | dict | None = "auto",
    ) -> dict:
        """Send a chat request to the LLM.

        Args:
            messages: List of message dicts with 'role' and 'content'
            tools: List of tool definitions (function schemas)
            tool_choice: How to use tools ("auto", "none", "required", or specific)

        Returns:
            Dict with 'content' and/or 'tool_calls' keys
        """
        url = f"{self.base_url}/chat/completions"

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
        }

        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = tool_choice

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    headers=self._headers,
                    json=payload,
                    timeout=60.0,
                )
                response.raise_for_status()
                data = response.json()

                # Extract choice
                choice = data.get("choices", [{}])[0]
                message = choice.get("message", {})

                result = {
                    "content": message.get("content"),
                    "tool_calls": message.get("tool_calls"),
                }

                # Debug output to stderr
                if result["tool_calls"]:
                    for tc in result["tool_calls"]:
                        func = tc.get("function", {})
                        print(
                            f"[tool] LLM called: {func.get('name')}({func.get('arguments', '{}')})",
                            file=sys.stderr,
                        )

                return result

        except httpx.ConnectError as e:
            raise LLMError(f"LLM connection error: {e}")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise LLMError(
                    "LLM authentication failed (HTTP 401). "
                    "Token may have expired. Try: cd ~/qwen-code-oai-proxy && docker compose restart"
                )
            raise LLMError(f"LLM HTTP error: {e.response.status_code} {e.response.reason_phrase}")
        except httpx.TimeoutException:
            raise LLMError("LLM request timed out")
        except httpx.HTTPError as e:
            raise LLMError(f"LLM error: {e}")
        except (KeyError, IndexError, TypeError) as e:
            raise LLMError(f"Unexpected LLM response format: {e}")

    def format_tool_result(self, tool_call_id: str, content: str) -> dict:
        """Format a tool result as a message for the LLM.

        Args:
            tool_call_id: ID from the tool_call that triggered this result
            content: The result content as JSON string

        Returns:
            Message dict for the conversation
        """
        return {
            "role": "tool",
            "tool_call_id": tool_call_id,
            "content": content,
        }

    def format_user_message(self, text: str) -> dict:
        """Format a user message."""
        return {"role": "user", "content": text}

    def format_system_message(self, text: str) -> dict:
        """Format a system message."""
        return {"role": "system", "content": text}

    def format_assistant_message(self, text: str | None = None, tool_calls: list | None = None) -> dict:
        """Format an assistant message."""
        msg = {"role": "assistant"}
        if text:
            msg["content"] = text
        if tool_calls:
            msg["tool_calls"] = tool_calls
        return msg
