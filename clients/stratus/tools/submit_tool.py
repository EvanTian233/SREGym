import ast
import json
import logging
from contextlib import AsyncExitStack
from typing import Annotated, Any, Dict, Optional

from langchain_core.messages import ToolMessage
from langchain_core.tools import InjectedToolCallId, tool
from langgraph.prebuilt import InjectedState
from langgraph.types import Command
from mcp import ClientSession
from mcp.client.sse import sse_client

from clients.stratus.configs.langgraph_tool_configs import LanggraphToolConfig
from clients.stratus.stratus_agent.state import State

submit_tool_docstring = """
Use this tool to submit your answer to the assigned tasks. You can give partial answer or empty answer
    (still of type dict) if you can not solve all of them.

    Args:
        ans (string): the answer you would like to submit
"""

rollback_submit_tool_docstring = """
The tool to submit after you rolled back all the changes.
"""
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

langgraph_tool_config = LanggraphToolConfig()


def _strip_code_fences(text: str) -> str:
    t = text.strip()
    if t.startswith("```"):
        parts = t.split("```")
        for chunk in parts:
            chunk = chunk.strip()
            if not chunk:
                continue
            if "\n" in chunk:
                first, rest = chunk.split("\n", 1)
                if first.lower() in {"json", "javascript", "js"}:
                    return rest.strip()
            return chunk
    return t


def _parse_submit_result(result_obj: Any) -> Dict[str, Any]:
    """
    Accepts the raw result from `session.call_tool(...)`.
    Returns a dict with at least a 'status' field when possible.
    """
    if isinstance(result_obj, dict) and "status" in result_obj:
        return result_obj

    content = getattr(result_obj, "content", None)
    if isinstance(content, list) and content:
        item = content[0]
        data = getattr(item, "data", None)
        if data and isinstance(data, (dict, list)):
            if isinstance(data, list) and data and isinstance(data[0], dict):
                return data[0]
            if isinstance(data, dict):
                return data

        text = getattr(item, "text", None)
        if isinstance(text, str):
            text = _strip_code_fences(text)
            try:
                parsed = json.loads(text)
                if isinstance(parsed, dict):
                    return parsed
            except Exception:
                pass
            if any(k in text for k in ("True", "False", "None")):
                try:
                    parsed = ast.literal_eval(text)
                    if isinstance(parsed, dict):
                        return parsed
                except Exception:
                    pass
            return {"status": "parse_error", "raw": text[:200]}
    return {"status": "unknown_format", "raw": str(result_obj)[:200]}


def _is_success_status(status_val: Any) -> bool:
    if status_val == 200:
        return True
    if isinstance(status_val, str) and status_val.strip() == "200":
        return True
    return False


@tool(description=submit_tool_docstring)
async def submit_tool(
    ans: str, state: Annotated[State, InjectedState], tool_call_id: Annotated[str, InjectedToolCallId]
) -> Command:
    logging.info("submitting to benchmark, answer length: %s", len(ans))
    exit_stack = AsyncExitStack()

    try:
        logger.info("Using HTTP, connecting to server (MCP SSE).")
        server_url = langgraph_tool_config.submit_mcp_url
        http_transport = await exit_stack.enter_async_context(sse_client(url=server_url))
        session = await exit_stack.enter_async_context(ClientSession(*http_transport))

        await session.initialize()

        mcp_result = await session.call_tool(
            "submit",
            arguments={"ans": ans},
        )

        parsed = _parse_submit_result(mcp_result)
        status = parsed.get("status")
        if not _is_success_status(status):
            logger.info("HTTP submission failed: %s", parsed)
            return Command(
                update={
                    "num_steps": state["num_steps"] - 1,
                    "messages": [
                        ToolMessage(
                            content=f"HTTP submission failed: {parsed}",
                            tool_call_id=tool_call_id
                        ),
                    ],
                }
            )

        logger.info("submission succeeded.")
        return Command(
            update={
                "submitted": True,
                "messages": [
                    ToolMessage("Submission complete. No further action is needed.", tool_call_id=tool_call_id)
                ],
            }
        )
    except Exception as e:
        snippet = ans[:200].replace("\n", "\\n")
        logger.exception("submit_tool exception: %s | ans[:200]=%r", e, snippet)
        return Command(
            update={
                "num_steps": max(0, state["num_steps"] - 1),
                "messages": [
                    ToolMessage(
                        content=f"Submission error: {e}. First 200 chars of ans: {snippet!r}",
                        tool_call_id=tool_call_id
                    ),
                ],
            }
        )
    finally:
        await exit_stack.aclose()


@tool("f_submit_tool", description=submit_tool_docstring)
async def fake_submit_tool(ans: str, tool_call_id: Annotated[str, InjectedToolCallId]) -> Command:
    logging.info("_NOT_ submitting to benchmark, answer length: %s", len(ans))
    logger.info("This method only toggles state[submitted]. Mitigation submission is done outside agent logic for retry.")
    return Command(
        update={
            "submitted": True,
            "messages": [ToolMessage("Submission complete. No further action is needed.", tool_call_id=tool_call_id)],
        }
    )


@tool("r_submit_tool", description=rollback_submit_tool_docstring)
async def rollback_submit_tool(tool_call_id: Annotated[str, InjectedToolCallId]) -> Command:
    logger.info("rollback agent submits (toggling submitted=True).")
    return Command(
        update={
            "submitted": True,
            "messages": [ToolMessage("Submission complete. No further action is needed.", tool_call_id=tool_call_id)],
        }
    )


async def manual_submit_tool(ans: str) -> str:
    logging.info("_manually_ submitting to benchmark, answer length: %s", len(ans))
    exit_stack = AsyncExitStack()
    try:
        logger.info("Using HTTP, connecting to server (MCP SSE).")
        server_url = langgraph_tool_config.submit_mcp_url
        http_transport = await exit_stack.enter_async_context(sse_client(url=server_url))
        session = await exit_stack.enter_async_context(ClientSession(*http_transport))

        await session.initialize()
        mcp_result = await session.call_tool("submit", arguments={"ans": ans})

        parsed = _parse_submit_result(mcp_result)
        status = parsed.get("status")
        if not _is_success_status(status):
            logger.info("Manual submit failed: %s", parsed)
            return f"Submit failed: {parsed}"
        logger.info("Submission complete. No further action is needed.")
        return "Submitted"
    finally:
        await exit_stack.aclose()
