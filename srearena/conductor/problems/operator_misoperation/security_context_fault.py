"""
The fault sets an invalid runAsUser value.
"""

import time
from datetime import datetime, timedelta
from typing import Any

#from srearena.conductor.oracles.localization import LocalizationOracle
#from srearena.conductor.oracles.target_port_mitigation import TargetPortMisconfigMitigationOracle
from srearena.conductor.problems.base import Problem
from srearena.generators.fault.inject_virtual import VirtualizationFaultInjector
from srearena.paths import TARGET_MICROSERVICES
from srearena.service.apps.fleet_cast import FleetCast
from srearena.service.kubectl import KubeCtl
from srearena.utils.decorators import mark_fault_injected



class K8SOperatorSecurityContextFault(Problem):
    def __init__(self, faulty_service="tidb-app"):
        app = FleetCast()
        super().__init__(app=app, namespace=app.namespace)
        self.faulty_service = faulty_service
        self.kubectl = KubeCtl()
        # === Attach evaluation oracles ===
        #self.localization_oracle = MyFutureLocalizationOracle(problem=self, expected=["tidbclusters"])
        #self.app.create_workload()
       # self.mitigation_oracle = MyOracleMitigation(problem=self)
    @mark_fault_injected
    def inject_fault(self):
        injector = VirtualizationFaultInjector(namespace=self.namespace)
        injector._inject(
            fault_type="security_context",
            microservices=[self.faulty_service],
        )
        print(f"[FAULT INJECTED] {self.faulty_service} security context misconfigured")
    @mark_fault_injected
    def recover_fault(self):
        injector = VirtualizationFaultInjector(namespace=self.namespace)
        injector._recover(
            fault_type="security_context",
            microservices=[self.faulty_service],
        )
        print(f"[FAULT RECOVERED] {self.faulty_service}")
     