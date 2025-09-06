"""A class representing a composite of mulitple applications"""

import json

from srearena.paths import TARGET_MICROSERVICES
from srearena.service.apps.base import Application


class CompositeApp:
    def __init__(self, apps: list[Application]):
        self.apps = apps
        self.name = "CompositeApp"

    def deploy(self):
        # FIXME: this can be optimized to parallel deploy later
        for app in self.apps:
            print(f"[CompositeApp] Deploying {app.name}...")
            app.deploy()

    def start_workload(self):
        # FIXME: this can be optimized to parallel start later
        for app in self.apps:
            print(f"[CompositeApp] Starting workload for {app.name}...")
            app.start_workload()

    def cleanup(self):
        # FIXME: this can be optimized to parallel cleanup later
        for app in self.apps:
            print(f"[CompositeApp] Cleaning up {app.name}...")
            app.cleanup()
