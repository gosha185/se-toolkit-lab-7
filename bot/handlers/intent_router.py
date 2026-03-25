"""Intent router for natural language queries.

Routes user messages to appropriate backend tools via LLM.
Uses tool calling to fetch data and generate responses.
"""

import json
import sys
from typing import Any

from config import Config
from services.api_client import APIClient
from services.llm_client import LLMClient, LLMError


# System prompt that teaches the LLM how to use tools
SYSTEM_PROMPT = """You are an assistant for a Learning Management System (LMS). 
You help users query information about labs, scores, learners, and analytics.

You have access to the following tools. Use them to answer user questions accurately.

IMPORTANT: 
- Always use tools to get real data before answering questions about labs, scores, or learners.
- If the user asks about a specific lab (e.g., "lab 4", "lab-04"), use "lab-04" format.
- For comparison questions (e.g., "which lab has the lowest"), first get all labs, then fetch data for each.
- After receiving tool results, analyze them and provide a clear, helpful answer.
- If you don't have enough information, ask the user to clarify.

Available tools:
1. get_items - List all labs and tasks. Use when user asks "what labs are available" or needs to see all options.
2. get_pass_rates - Get per-task average scores and attempt counts for a specific lab. Use for "show scores", "pass rates", "how did students do".
3. get_scores - Get score distribution (4 buckets) for a lab. Use for "score distribution", "how many got A/B/C/D".
4. get_timeline - Get submissions per day for a lab. Use for "when did students submit", "submission activity".
5. get_groups - Get per-group performance for a lab. Use for "which group is best", "compare groups".
6. get_top_learners - Get top N learners by score. Use for "who are the best students", "top performers".
7. get_completion_rate - Get completion rate percentage for a lab. Use for "how many completed", "completion percentage".
8. get_learners - Get all enrolled learners. Use for "how many students", "who is enrolled".
9. trigger_sync - Refresh data from autochecker. Use when user asks to "update data" or "sync".

When answering:
- Be specific and include numbers from the data.
- Format percentages with % symbol.
- Mention attempt counts when available.
- For comparisons, name the specific lab/group/learner and the value."""


def get_tool_definitions() -> list[dict]:
    """Return tool definitions for the LLM.

    Each tool is a function schema that the LLM can call.
    """
    return [
        {
            "type": "function",
            "function": {
                "name": "get_items",
                "description": "List all available labs and tasks in the LMS",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_pass_rates",
                "description": "Get per-task average scores and attempt counts for a specific lab",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "lab": {
                            "type": "string",
                            "description": "Lab identifier in format 'lab-XX', e.g., 'lab-01', 'lab-04'",
                        },
                    },
                    "required": ["lab"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_scores",
                "description": "Get score distribution (4 buckets) for a lab",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "lab": {
                            "type": "string",
                            "description": "Lab identifier in format 'lab-XX'",
                        },
                    },
                    "required": ["lab"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_timeline",
                "description": "Get submission timeline (submissions per day) for a lab",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "lab": {
                            "type": "string",
                            "description": "Lab identifier in format 'lab-XX'",
                        },
                    },
                    "required": ["lab"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_groups",
                "description": "Get per-group performance (scores and student counts) for a lab",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "lab": {
                            "type": "string",
                            "description": "Lab identifier in format 'lab-XX'",
                        },
                    },
                    "required": ["lab"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_top_learners",
                "description": "Get top N learners by score for a lab",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "lab": {
                            "type": "string",
                            "description": "Lab identifier in format 'lab-XX'",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Number of top learners to return (default: 5)",
                            "default": 5,
                        },
                    },
                    "required": ["lab"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_completion_rate",
                "description": "Get completion rate percentage for a lab",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "lab": {
                            "type": "string",
                            "description": "Lab identifier in format 'lab-XX'",
                        },
                    },
                    "required": ["lab"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_learners",
                "description": "Get all enrolled learners in the LMS",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "trigger_sync",
                "description": "Trigger ETL sync to refresh data from autochecker",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
            },
        },
    ]


class IntentRouter:
    """Routes natural language queries to backend tools via LLM."""

    def __init__(self, config: Config):
        self.config = config
        self.api_client = APIClient(config.lms_api_url, config.lms_api_key)
        
        # Only initialize LLM client if credentials are available
        self.llm_client = None
        if config.llm_api_key and config.llm_api_base_url and config.llm_api_model:
            self.llm_client = LLMClient(
                api_key=config.llm_api_key,
                base_url=config.llm_api_base_url,
                model=config.llm_api_model,
            )
        
        self.tools = get_tool_definitions()

    async def execute_tool(self, name: str, arguments: dict) -> Any:
        """Execute a tool by calling the appropriate API method.

        Args:
            name: Tool name (e.g., "get_items", "get_pass_rates")
            arguments: Tool arguments as dict

        Returns:
            Tool result (API response)
        """
        # Map tool names to API client methods
        method_map = {
            "get_items": self.api_client._request,
            "get_learners": self.api_client.get_learners,
            "get_pass_rates": self.api_client.get_pass_rates,
            "get_scores": self.api_client.get_scores,
            "get_timeline": self.api_client.get_timeline,
            "get_groups": self.api_client.get_groups,
            "get_top_learners": self.api_client.get_top_learners,
            "get_completion_rate": self.api_client.get_completion_rate,
            "trigger_sync": self.api_client.sync_pipeline,
        }

        method = method_map.get(name)
        if not method:
            return {"error": f"Unknown tool: {name}"}

        try:
            # Special handling for methods with different signatures
            if name == "get_items":
                result = await method("GET", "/items/")
            elif name in ("get_pass_rates", "get_scores", "get_timeline", "get_groups", 
                          "get_top_learners", "get_completion_rate"):
                # These take lab as first positional arg
                lab = arguments.get("lab", "")
                if name == "get_top_learners":
                    limit = arguments.get("limit", 5)
                    result = await method(lab, limit)
                else:
                    result = await method(lab)
            elif name in ("get_learners", "trigger_sync"):
                result = await method()
            else:
                result = await method(**arguments)

            # Debug output
            if isinstance(result, (list, dict)):
                preview = str(result)[:200]
                if isinstance(result, list):
                    print(f"[tool] Result: {len(result)} items", file=sys.stderr)
                else:
                    print(f"[tool] Result: {preview}...", file=sys.stderr)
            else:
                print(f"[tool] Result: {result}", file=sys.stderr)

            return result

        except Exception as e:
            error_msg = f"Tool execution error: {type(e).__name__}: {e}"
            print(f"[tool] Error: {error_msg}", file=sys.stderr)
            return {"error": error_msg}

    async def route(self, user_message: str) -> str:
        """Route a user message through the LLM tool loop.

        Args:
            user_message: The user's natural language query

        Returns:
            Formatted response text
        """
        # Check if LLM is configured
        if not self.llm_client:
            return (
                "⚠️ LLM is not configured. Please set LLM_API_KEY, LLM_API_BASE_URL, "
                "and LLM_API_MODEL in .env.bot.secret\n\n"
                "For now, use slash commands like /health, /labs, /scores lab-04"
            )

        # Initialize conversation
        messages = [
            self.llm_client.format_system_message(SYSTEM_PROMPT),
            self.llm_client.format_user_message(user_message),
        ]

        # Tool execution loop (max iterations to prevent infinite loops)
        max_iterations = 5
        iteration = 0

        while iteration < max_iterations:
            iteration += 1

            # Call LLM
            try:
                response = await self.llm_client.chat(messages, tools=self.tools)
            except LLMError as e:
                return f"❌ LLM error: {str(e)}"

            # Check if LLM returned tool calls
            tool_calls = response.get("tool_calls")
            content = response.get("content")

            if not tool_calls:
                # LLM returned final answer
                if content:
                    return content
                else:
                    return "I'm not sure how to help with that. Try asking about labs, scores, or learners."

            # Add assistant message with tool calls to conversation
            messages.append(
                self.llm_client.format_assistant_message(
                    tool_calls=tool_calls
                )
            )

            # Execute each tool and collect results
            print(f"[summary] Executing {len(tool_calls)} tool call(s)", file=sys.stderr)
            
            for tool_call in tool_calls:
                tool_id = tool_call.get("id")
                function = tool_call.get("function", {})
                name = function.get("name")
                arguments_str = function.get("arguments", "{}")

                try:
                    arguments = json.loads(arguments_str) if arguments_str else {}
                except json.JSONDecodeError:
                    arguments = {}

                # Execute the tool
                result = await self.execute_tool(name, arguments)

                # Format result as JSON string for LLM
                result_json = json.dumps(result, ensure_ascii=False, default=str)

                # Add tool result to conversation
                messages.append(
                    self.llm_client.format_tool_result(tool_id, result_json)
                )

            print(f"[summary] Feeding {len(tool_calls)} tool result(s) back to LLM", file=sys.stderr)

        # If we exit the loop without a response, return what we have
        if content:
            return content
        return "I encountered an issue processing your request. Please try again or use a slash command."


async def handle_natural_language(text: str, config: Config) -> str:
    """Handle a natural language query.

    Args:
        text: User's message
        config: Bot configuration

    Returns:
        Response text
    """
    router = IntentRouter(config)
    return await router.route(text)
