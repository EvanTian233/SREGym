import asyncio, os, sys
from typing import Dict, Optional
from datetime import datetime
from .agent_registry import AgentRegistration

class AgentProcess:
    def __init__(self, name: str, proc: asyncio.subprocess.Process):
        self.name = name
        self.proc = proc
        self.started_at = datetime.utcnow()

class AgentLauncher:
    def __init__(self):
        self._procs: Dict[str, AgentProcess] = {}

    async def ensure_started(self, reg: AgentRegistration) -> Optional[AgentProcess]:
        if not reg or not reg.kickoff_command:
            return None
        existing = self._procs.get(reg.name)
        if existing and existing.proc.returncode is None:
            return existing

        env = os.environ.copy()
        if reg.kickoff_env:
            env.update(reg.kickoff_env)

        proc = await asyncio.create_subprocess_shell(
            reg.kickoff_command,
            cwd=reg.kickoff_workdir or os.getcwd(),
            env=env,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        ap = AgentProcess(reg.name, proc)
        self._procs[reg.name] = ap
        asyncio.create_task(self._pipe_logs(reg.name, proc))
        return ap

    async def _pipe_logs(self, name: str, proc: asyncio.subprocess.Process):
        if proc.stdout is None:
            return
        async for line in proc.stdout:
            sys.stdout.write(f"[{name}] {line.decode(errors='ignore')}")
            sys.stdout.flush()
