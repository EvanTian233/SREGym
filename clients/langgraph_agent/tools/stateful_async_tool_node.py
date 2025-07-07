import asyncio
import logging

from langchain_core.messages import ToolMessage
from langchain_core.tools import BaseTool

from fastmcp import Client

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class StatefulAsyncToolNode:
    """A node that runs the stateful remote mcp tools requested in the last AIMessage."""

    def __init__(self, node_tools: list[BaseTool], client: Client) -> None:
        self.tools_by_name = {t.name: t for t in node_tools}
        self.client = client
        self.is_session_established = False

    def __call__(self, inputs: dict):
        if messages := inputs.get("messages", []):
            message = messages[-1]
        else:
            raise ValueError("No message found in input")
        logger.info(f"StatefulAsyncToolNode: {message}")
        outputs = []
        logger.info(f"tool node connection is {'' if self.is_session_established else 'not '}established.")
        for tool_call in message.tool_calls:
            logger.info(f"invoking tool: {tool_call['name']}, tool_call: {tool_call}")
            tool_result = asyncio.run(self.tools_by_name[tool_call["name"]].ainvoke(tool_call.get('args', {})))
            logger.info(f"tool_result: {tool_result}")
            outputs.append(
                ToolMessage(
                    content=tool_result,
                    name=tool_call["name"],
                    tool_call_id=tool_call["id"],
                )
            )

        return {"messages": outputs}
