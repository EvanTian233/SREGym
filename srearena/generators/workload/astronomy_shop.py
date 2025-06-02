from srearena.generators.workload.stream import StreamWorkloadManager, WorkloadEntry


class AstronomyShopWorkloadManager(StreamWorkloadManager):
    def __init__(self, deployment_name: str):
        super().__init__()
        self.deployment_name = deployment_name

    def retrievelog(self, start_time: float | None = None) -> list[WorkloadEntry]:
        return [WorkloadEntry(time=0.0, number=1, log="Sample log entry", ok=True)]

    def start(self):
        print("== Start Workload ==")
        print("AstronomyShop has a built-in load generator.")

    def stop(self):
        print("== Stop Workload ==")
        print("AstronomyShop's built-in load generator is automatically managed.")
