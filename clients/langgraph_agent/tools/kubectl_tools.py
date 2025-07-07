from fastmcp import Client
from typing import Any, Optional

from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_core.tools.base import ArgsSchema, BaseTool
import logging
from pydantic import BaseModel, Field, PrivateAttr
import sys

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

kube_tool_url = "http://127.0.0.1:8000/kubectl_mcp_tools/sse"


class ExecKubectlCmdSafelyInput(BaseModel):
    command: str = Field(description='The command you want to execute in a CLI to manage '
                                     'a k8s cluster. It should start with "kubectl".')


class ExecKubectlCmdSafely(BaseTool):
    name: str = "exec_kubectl_cmd_safely"
    description: str = "this is a tool used to safely execute kubectl commands."
    args_schema: Optional[ArgsSchema] = ExecKubectlCmdSafelyInput

    _client: Client = PrivateAttr()

    def __init__(self, client: Client, **kwargs: Any):
        super().__init__(**kwargs)
        self._client = client

    def _run(
        self,
        command: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        logger.error("no sync version of tools, exiting.")
        sys.exit(1)

    async def _arun(
        self,
        command: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        logger.info(f"calling mcp exec_kubectl_cmd_safely from "
                    f"langchain exec_kubectl_cmd_safely, with command: \"{command}\"")
        async with self._client:
            result = await self._client.call_tool("exec_kubectl_cmd_safely", arguments={"cmd": command})
        text_result = "\n".join([part.text for part in result])
        return text_result


kubectl_read_only_cmds = [
    "kubectl api-resources",
    "kubectl api-version",
    # read only if not interactive (interactive commands are prohibited)
    "kubectl attach",
    "kubectl auth can-i",
    "kubectl cluster-info",
    "kubectl describe",
    "kubectl diff",
    "kubectl events",
    "kubectl explain",
    "kubectl get",
    "kubectl logs",
    "kubectl options",
    "kubectl top",
    "kubectl version",
    "kubectl config view",
    "kubectl config current-context",
    "kubectl config get",
]


class ExecReadOnlyKubectlCmdInput(BaseModel):
    command: str = Field(description=f'The read-only kubectl command you want to execute in a CLI '
                                     'to manage a k8s cluster. It should start with "kubectl". '
                                     f'Available Read-only Commands: {kubectl_read_only_cmds}')


class ExecReadOnlyKubectlCmd(BaseTool):
    name: str = "exec_read_only_kubectl_cmd"
    description: str = "this is a tool used to execute read-only kubectl commands."
    args_schema: Optional[ArgsSchema] = ExecReadOnlyKubectlCmdInput

    _client: Client = PrivateAttr()

    def __init__(self, client: Client, **kwargs: Any):
        super().__init__(**kwargs)
        self._client = client

    def _run(
        self,
        command: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        logger.error("no sync version of tools, exiting.")
        sys.exit(1)

    async def _arun(
        self,
        command: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        is_read_only = False
        for c in kubectl_read_only_cmds:
            if command.startswith(c):
                is_read_only = True
                break
        if not is_read_only:
            logger.info(f"Agent is trying to exec a non read-only command {command} with tool {self.name}")
            return f"Your command {command} is not a read-only kubectl command. " \
                   f"Available Read-only Commands: {kubectl_read_only_cmds}."

        logger.info(f"calling mcp exec_kubectl_cmd_safely from "
                    f"langchain {self.name}, with command: \"{command}\"")
        async with self._client:
            result = await self._client.call_tool("exec_kubectl_cmd_safely", arguments={"cmd": command})
        text_result = "\n".join([part.text for part in result])
        return text_result


class RollbackCommand(BaseTool):
    name: str = "rollback_command"
    description: str = "Use this function to roll back the last kubectl command " \
                       "you successfully executed with the \"exec_kubectl_cmd_safely\" tool."
    args_schema: Optional[ArgsSchema] = None

    _client: Client = PrivateAttr()

    def __init__(self, client: Client, **kwargs: Any):
        super().__init__(**kwargs)
        self._client = client

    def _run(
        self,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        logger.error("no sync version of tools, exiting.")
        sys.exit(1)

    async def _arun(
        self,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        logger.info(f"calling langchain rollback_command")
        async with self._client:
            result = await self._client.call_tool("rollback_command")
        text_result = "\n".join([part.text for part in result])
        return text_result


class GetPreviousRollbackabelCmd(BaseTool):
    name: str = "get_previous_rollbackabel_cmd"
    description: str = "Use this function to get a list of commands you " \
                       "previously executed that could be roll-backed. " \
                       "When you call \"rollback_command\" tool multiple times, " \
                       "you will roll-back previous commands in the order " \
                       "of the returned list."
    args_schema: Optional[ArgsSchema] = None

    _client: Client = PrivateAttr()

    def __init__(self, client: Client, **kwargs: Any):
        super().__init__(**kwargs)
        self._client = client

    def _run(
        self,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        logger.error("no sync version of tools, exiting.")
        sys.exit(1)

    async def _arun(
        self,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        logger.info(f"calling langchain get_previous_rollbackabel_cmd")
        async with self._client:
            result = await self._client.call_tool("get_previous_rollbackabel_cmd")
        text_result = "\n".join([part.text for part in result])
        return text_result
