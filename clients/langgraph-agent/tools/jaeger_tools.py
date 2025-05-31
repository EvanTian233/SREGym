import asyncio
import logging
from typing import Any, Optional

from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_core.tools import tool
from langchain_core.tools.base import ArgsSchema, BaseTool
from pydantic import BaseModel, Field

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class GetTracesInput(BaseModel):
    service: str = Field(description="service name")
    operation: str = Field(description="operation name")
    last_n_minutes: int = Field(description="last n minutes of traces")


class GetTraces(BaseTool):
    name: str = "get_traces"
    description: str = (
        "get traces of last n minutes from jaeger by service and operation"
    )
    args_schema: Optional[ArgsSchema] = GetTracesInput
    # FIXME: this is also very janky, what's the type?
    mcp_ctx: Any = None

    def __init__(self, mcp_ctx):
        super().__init__()
        self.mcp_ctx = mcp_ctx

    def _run(
        self,
        service: str,
        operation: str,
        last_n_minutes: int,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        logger.info(
            f"calling mcp get_traces from langchain get_traces, with service {service} and operation {operation}"
        )
        result = self.mcp_ctx.call_tool(
            "get_traces",
            arguments={
                "service": service,
                "operation": operation,
                "last_n_minutes": last_n_minutes,
            },
        )
        return result


class GetServices(BaseTool):
    name: str = "get_services"
    description: str = "get services from jaeger"
    args_schema: Optional[ArgsSchema] = None
    # FIXME: this is also very janky, what's the type?
    mcp_ctx: Any = None

    def __init__(self, mcp_ctx):
        super().__init__()
        self.mcp_ctx = mcp_ctx

    def _run(
        self,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        logger.info(f"calling mcp get_services from langchain get_services")
        result = self.mcp_ctx.call_tool("get_services")
        return result

    async def _arun(
        self, run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        logger.info(f"*async* calling mcp get_services from langchain get_services")
        result = asyncio.run(self.mcp_ctx.call_tool("get_services"))
        return result


class GetOperationsInput(BaseModel):
    service: str = Field(description="service name")


class GetOperations(BaseTool):
    name: str = "get_operations"
    description: str = "get operations from jaeger by service"
    args_schema: Optional[ArgsSchema] = GetOperationsInput
    # FIXME: this is also very janky, what's the type?
    mcp_ctx: Any = None

    def __init__(self, mcp_ctx):
        super().__init__()
        self.mcp_ctx = mcp_ctx

    def _run(
        self,
        service: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        logger.info(
            f"calling mcp get_operations from langchain get_operations with service {service}"
        )
        result = self.mcp_ctx.call_tool(
            "get_operations",
            arguments={"service": service},
        )
        return result
