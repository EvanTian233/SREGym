"""
SREArena CLI client. Use this for debugging and platform development work—
otherwise use main.py.

This version talks directly to the in-process Conductor for both environment
setup and grading, but still gives you the PromptToolkit+Rich UI.
"""

import asyncio
import json
import sys

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit.styles import Style
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from srearena.conductor.conductor import Conductor
from srearena.service.shell import Shell
from srearena.agent_registry import AgentRegistration, save_agent, list_agents, get_agent
from srearena.agent_launcher import AgentLauncher

WELCOME = """
# SREArena
- Type your commands or actions below.
"""

OPTIONS = """
- Use `start <problem_id>` to begin a new problem.
- Use `deploy <app_name>` / `undeploy <app_name>` to manage standalone apps.
- Use `list` to see deployed apps.
- Use `options` to re-print this list.
- Use `exit` to quit.
"""

WARNING = (
    "[bold yellow][WARNING][/bold yellow] Starting a new problem will "
    "restart any running app. Make sure you finish working before you start."
)

# (If you still want TASK_MESSAGE for problem context, you can re-enable it here.)


class HumanAgent:
    def __init__(self, conductor: Conductor):
        self.session = PromptSession()
        self.console = Console(force_terminal=True, color_system="auto")
        self.conductor = conductor
        self.pids = self.conductor.problems.get_problem_ids()
        self.completer = WordCompleter(
            ["list", "options", "exit"] + [f"start {pid}" for pid in self.pids],
            ignore_case=True,
            match_middle=True,
            sentence=True,
        )
        self.launcher = AgentLauncher()
        self.completer = WordCompleter(
            ["list", "options", "exit", "agents", "register-agent", "kickoff-agent"] + [f"start {pid}" for pid in self.pids],
            ignore_case=True,
            match_middle=True,
            sentence=True,
)

        self.session_purpose = None  # "problem", "exit", etc.

    def display_welcome(self):
        self.console.print(Markdown(WELCOME), justify="center")
        self.console.print(Markdown(OPTIONS), justify="center")
        self.console.print(WARNING)
        self.console.print()

    async def select_mode(self):
        """Prompt until we get 'start <problem_id>' or 'exit'."""
        while True:
            inp = await self._prompt()
            cmd = inp.strip().split(maxsplit=1)
            if cmd[0].lower() == "exit":
                sys.exit(0)
            if cmd[0].lower() == "options":
                self.console.print(Markdown(OPTIONS), justify="center")
                continue
            if cmd[0].lower() == "list":
                apps = self.conductor.get_deployed_apps()
                text = "\n".join(apps) if apps else "No apps deployed"
                self.console.print(Panel(text, title="Deployed Apps"))
                continue
            if cmd[0].lower() == "start" and len(cmd) == 2:
                pid = cmd[1]
                if pid not in self.pids:
                    self.console.print(f"[red]Unknown problem id: {pid}")
                    continue
                self.conductor.problem_id = pid
                self.session_purpose = "problem"
                return
            self.console.print("[red]Invalid command. Type `options` to see choices.")


            if cmd[0].lower() == "agents":
                regs = list_agents()
                if not regs:
                    self.console.print("No registered agents.")
                else:
                    lines = [f"- {name}: kickoff={regs[name].kickoff_command!r}" for name in regs]
                    self.console.print(Panel("\n".join(lines), title="Registered Agents"))
                continue

            if cmd[0].lower() == "register-agent" and len(cmd) == 2:
                # Expect JSON: {"name":"stratus","kickoff_command":"python -m ...","kickoff_workdir":".","kickoff_env":{"KUBECONFIG":"$KUBECONFIG"}}
                try:
                    data = json.loads(cmd[1])
                    reg = AgentRegistration(
                        name=data["name"],
                        kickoff_command=data.get("kickoff_command"),
                        kickoff_workdir=data.get("kickoff_workdir"),
                        kickoff_env=data.get("kickoff_env"),
                    )
                    save_agent(reg)
                    self.console.print(f"[green]Registered agent '{reg.name}'.[/green]")
                except Exception as e:
                    self.console.print(f"[red]Bad register-agent payload: {e}[/red]")
                continue

            if cmd[0].lower() == "kickoff-agent" and len(cmd) == 2:
                name = cmd[1]
                reg = get_agent(name)
                if not reg:
                    self.console.print(f"[red]No agent named '{name}' in registry.[/red]")
                    continue
                await self.launcher.ensure_started(reg)
                self.console.print(f"[green]Kicked off agent '{name}'.[/green]")
                continue


    async def interactive_loop(self):
        """Once problem is started, repeatedly shell or submit until done."""
        env = ""
        while self.conductor.submission_stage != "done":
            # display last environment or grading response
            if env:
                print(env)

            inp = await self._prompt()
            text = inp.strip()

            # shell command
            if not text.startswith("submit("):
                try:
                    out = Shell.exec(text)
                except Exception as e:
                    out = f"[❌] Shell error: {e}"
                env = out
                continue

            wrapped = f"```\n{text}\n```"
            try:
                resp = await self.conductor.submit(wrapped)
            except Exception as e:
                env = f"[❌] Grading error: {e}"
            else:
                env = resp

        # final results panel
        final = json.dumps(self.conductor.results, indent=2)
        self.console.print(Panel(final, title="Final Results", style="bold green"))

    async def _prompt(self) -> str:
        loop = asyncio.get_running_loop()
        style = Style.from_dict({"prompt": "ansigreen bold"})
        prompt_txt = [("class:prompt", "SREArena> ")]
        with patch_stdout():
            try:
                return await loop.run_in_executor(
                    None,
                    lambda: self.session.prompt(prompt_txt, style=style, completer=self.completer),
                )
            except (KeyboardInterrupt, EOFError):
                sys.exit(0)


async def main():
    conductor = Conductor()
    agent = HumanAgent(conductor)
    conductor.register_agent()  # no-op but for symmetry

    # 1) Intro & pick a problem
    agent.display_welcome()
    await agent.select_mode()

    # 2) Deploy environment & launch HTTP server
    await conductor.start_problem()

    # 3) Interactive shell / submit loop
    await agent.interactive_loop()


if __name__ == "__main__":
    asyncio.run(main())
