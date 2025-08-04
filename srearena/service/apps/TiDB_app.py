
import time

from srearena.generators.workload.wrk2 import Wrk2, Wrk2WorkloadManager
from srearena.paths import TIDB_APP_METADATA, TIDB_METADATA, TARGET_MICROSERVICES
from srearena.service.apps.base import Application
from srearena.service.apps.helpers import get_frontend_url
from srearena.service.helm import Helm
from srearena.service.kubectl import KubeCtl

class TIDBApp(Application):
    def __init__(self):
        super().__init__(TIDB_APP_METADATA)
        self.load_app_json()
        self.kubectl = KubeCtl()
        self.local_tls_path = TARGET_MICROSERVICES / "FleetCast/satellite-app"

        self.create_namespace()
        self.create_tls_secret()
        self.payload_script = TIDB_METADATA / "FleetCast/wrk/wrk.lua"

    def load_app_json(self):
        super().load_app_json()
        metadata = self.get_app_json()
        self.frontend_service = metadata.get("frontend_service", "tidb-frontend")
        self.frontend_port = metadata.get("frontend_port", 8080)
    def create_tls_secret(self):
        check_sec = f"kubectl get secret tidb-tls -n {self.namespace}"
        result = self.kubectl.exec_command(check_sec)
        if "notfound" in result.lower():
            create_sec_command = (
                f"kubectl create secret generic tidb-tls "
                f"--from-file=tls.pem={self.local_tls_path}/tls/tls.pem "
                f"--from-file=ca.crt={TIDB_METADATA}/tls/ca.crt "
                f"-n {self.namespace}"
            )
            create_result = self.kubectl.exec_command(create_sec_command)
            print(f"TLS secret created: {create_result.strip()}")
        else:
            print("TLS secret already exists. Skipping creation.")
    def deploy(self):
        """Deploy the Helm configurations."""
        self.kubectl.create_namespace_if_not_exist(self.namespace)
        Helm.add_repo(
            "tidb",
            "https://xlab-uiuc.github.io/FleetCast",
        )
        Helm.install(**self.helm_configs)
        Helm.assert_if_deployed(self.helm_configs["namespace"])
    def delete(self):
        """Delete the Helm configurations."""
        Helm.uninstall(**self.helm_configs)
        self.kubectl.delete_namespace(self.helm_configs["namespace"])
        self.kubectl.wait_for_namespace_deletion(self.namespace)
    def cleanup(self):
        Helm.uninstall(**self.helm_configs)
        self.kubectl.delete_namespace(self.helm_configs["namespace"])
        self.kubectl.wait_for_namespace_deletion(self.namespace)
        if hasattr(self, "wrk"):
            self.wrk.stop()
    def create_workload(self, rate: int = 100, dist: str = "exp", connections: int = 3, duration: int = 10, threads: int = 3):
        self.wrk = Wrk2WorkloadManager(
            wrk=Wrk2(rate=rate, dist=dist, connections=connections, duration=duration, threads=threads),
            payload_script=self.payload_script,
            url=f"{{placeholder}}/wrk2-api/post/compose",
        )
    def start_workload(self):
        if not hasattr(self, "wrk"):
            self.create_workload()
        self.wrk.url = get_frontend_url(self) + "/wrk2-api/post/compose"
        self.wrk.start()

# if __name__ == "__main__":
    



        

    