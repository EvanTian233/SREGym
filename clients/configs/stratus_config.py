import logging
import os
import uuid
from pathlib import Path

import yaml
from dotenv import load_dotenv
from fastmcp import Client
from fastmcp.client.transports import SSETransport
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field, field_validator

from clients.langgraph_agent.tools.jaeger_tools import get_operations, get_services, get_traces
from clients.langgraph_agent.tools.kubectl_tools import (
    ExecKubectlCmdSafely,
    ExecReadOnlyKubectlCmd,
    GetPreviousRollbackableCmd,
    RollbackCommand,
)
from clients.langgraph_agent.tools.prometheus_tools import get_metrics
from clients.langgraph_agent.tools.submit_tool import submit_tool
from clients.langgraph_agent.tools.wait_tool import wait_tool

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

parent_dir = Path(__file__).resolve().parent

load_dotenv()


class BaseAgentCfg(BaseModel):
    max_round: int = Field(
        default=int(os.environ["MAX_ROUND"]), description="maximum rounds allowed for tool calling", gt=0
    )

    max_rec_round: int = Field(
        default=int(os.environ["MAX_REC_ROUND"]),
        description="maximum rounds allowed for submission rectification",
        gt=0,
    )

    max_tool_call_one_round: int = Field(
        default=int(os.environ["MAX_TOOL_CALL_ONE_ROUND"]),
        description="maximum number of tool_calls allowed in one round",
        gt=0,
    )

    prompts_file_path: str = Field(
        description="prompts used for diagnosis agent",
    )

    sync_tools: list[BaseTool] = Field(
        description="provided sync tools for the agent",
    )

    async_tools: list[BaseTool] = Field(
        description="provided async tools for the agent",
    )

    @field_validator("prompts_file_path")
    @classmethod
    def validate_prompts_file_path(cls, v):
        path = v
        if not os.path.exists(path):
            raise FileNotFoundError(f"Path does not exist: {path}")

        if not os.path.isfile(path):
            raise ValueError(f"Path is not a file: {path}")

        if not path.endswith((".yaml", ".yml")):
            raise ValueError(f"Invalid file extension (expected .yaml or .yml): {path}")

        try:
            with open(path, "r", encoding="utf-8") as f:
                yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ValueError(f"YAML parsing error: {e}")
        except Exception as e:
            raise RuntimeError(f"Unexpected error reading YAML file: {e}")
        return v


def get_diagnosis_agent_cfg():
    client = get_client()

    exec_read_only_kubectl_cmd = ExecReadOnlyKubectlCmd(client)
    diagnosis_agent_cfg = BaseAgentCfg(
        prompts_file_path=str(parent_dir / "stratus_diagnosis_agent_prompts.yaml"),
        sync_tools=[],
        async_tools=[get_traces, get_services, get_operations, get_metrics, exec_read_only_kubectl_cmd, submit_tool],
    )
    return diagnosis_agent_cfg


def get_client():
    session_id = str(uuid.uuid4())
    transport = SSETransport(
        url=f"{os.environ['MCP_SERVER_URL']}/kubectl_mcp_tools/sse",
        headers={"srearena_ssid": session_id},
    )
    client = Client(transport)
    return client


def get_mitigation_rollback_agent_cfg():
    client = get_client()
    # Initialize tools
    exec_kubectl_cmd_safely = ExecKubectlCmdSafely(client)
    rollback_command = RollbackCommand(client)
    get_previous_rollbackable_cmd = GetPreviousRollbackableCmd(client)

    mitigation_agent_cfg = BaseAgentCfg(
        prompts_file_path=str(parent_dir / "stratus_mitigation_agent_prompts.yaml"),
        sync_tools=[wait_tool],
        async_tools=[get_traces, get_services, get_operations, get_metrics, exec_kubectl_cmd_safely, submit_tool],
    )

    rollback_agent_cfg = BaseAgentCfg(
        prompts_file_path=str(parent_dir / "stratus_rollback_agent_prompts.yaml"),
        sync_tools=[],
        async_tools=[rollback_command, get_previous_rollbackable_cmd, submit_tool],
    )
    return mitigation_agent_cfg, rollback_agent_cfg
