"""TrainTicket F1 Async Message Order Problem Definition

Implements F1 fault injection for TrainTicket order cancellation flow.
The fault introduces an 8-second delay in payment drawback causing
async message order violation.
"""

import logging
import time
from typing import Any, Dict

from srearena.conductor.oracles.detection import DetectionOracle
from srearena.conductor.oracles.localization import LocalizationOracle
from srearena.conductor.oracles.mitigation import MitigationOracle
from srearena.conductor.problems.base import Problem
from srearena.generators.fault.inject_tt import TrainTicketFaultInjector  
from srearena.service.apps.train_ticket import TrainTicket
from srearena.generators.workload.trainticket_locust import TrainTicketLocustWorkloadManager

logger = logging.getLogger(__name__)


class TrainTicketF1AsyncMessageOrderProblem(Problem):
    """
    F1: Async Message Order Violation in TrainTicket order cancellation.

    This problem injects an 8-second delay in the payment drawback process
    during order cancellation, causing the "Reset Order Status" message
    to complete before the "Drawback Money" message, violating the expected
    async message sequence.
    """

    def __init__(self):
        app = TrainTicket()
        super().__init__(app=app, namespace=app.namespace)
        self.fault_injector = TrainTicketFaultInjector(app.namespace)
        self.faulty_service = "ts-cancel-service"
        self.fault_name = "fault-1-async-message-order"
        
        # === Attach evaluation oracles ===
        self.detection_oracle = DetectionOracle(problem=self)
        self.detection_oracle.expected = "Yes"
        
        self.localization_oracle = LocalizationOracle(problem=self, expected=[self.faulty_service])
        
        self.mitigation_oracle = MitigationOracle(problem=self)
        self.mitigation_oracle.expected = False  # This fault cannot be mitigated by agents, only recovered by disabling
        
        self.results = {
            "fault_injected": False,
            "fault_recovered": False,
            "delay_observed": False,
            "logs_captured": [],
            "timing_analysis": {},
        }

    def inject_fault(self) -> bool:
        """
        Inject F1 fault by enabling the async message order flag.
        
        Returns:
            bool: True if fault injection successful
        """
        try:
            print(f"[TrainTicket F1] Injecting async message order fault...")
            
            if not self.fault_injector.inject_fault(self.fault_name):
                logger.error("Failed to inject F1 fault")
                return False
                
            self.results["fault_injected"] = True
            
            print(f"[TrainTicket F1] F1 fault injected successfully")
            print(f"[TrainTicket F1] Order cancellation will now have 8-second delay")
            
            return True
            
        except Exception as e:
            logger.error(f"Error injecting F1 fault: {e}")
            return False

    def recover_fault(self) -> bool:
        """
        Recover from F1 fault by disabling the async message order flag.
        
        Returns:
            bool: True if fault recovery successful
        """
        try:
            print(f"[TrainTicket F1] Recovering from async message order fault...")
            
            if not self.fault_injector.recover_fault(self.fault_name):
                logger.error("Failed to recover F1 fault")
                return False
                
            self.results["fault_recovered"] = True
            
            print(f"[TrainTicket F1] F1 fault recovered successfully")
            print(f"[TrainTicket F1] Order cancellation should now be normal")
            
            return True
            
        except Exception as e:
            logger.error(f"Error recovering F1 fault: {e}")
            return False

    def start_workload(self):
        """
        Start workload using Locust to trigger F1 fault scenario.
        """
        print("== Start Workload ==")
        
        try:
            # Try to use the app's workload method if available
            if hasattr(self.app, 'start_workload'):
                self.app.start_workload()
                print("[TrainTicket F1] Workload started via app")
            else:
                print("[TrainTicket F1] Manual workload instructions:")
                print("1. Access TrainTicket UI at service endpoint")
                print("2. Login with: fdse_microservice/111111") 
                print("3. Create and cancel orders to trigger F1 fault")
                print("4. Monitor logs for 8-second delay evidence")
            
        except Exception as e:
            logger.error(f"Error starting F1 workload: {e}")

    def check_fault_status(self) -> str:
        """
        Check current status of F1 fault.
        
        Returns:
            str: Current fault status ("on", "off", or "unknown")
        """
        return self.fault_injector.get_fault_status(self.fault_name)

    def analyze_logs(self) -> Dict[str, Any]:
        """
        Analyze service logs for F1 fault injection evidence.
        
        Returns:
            Dict: Log analysis results
        """
        try:
            from srearena.service.kubectl import KubeCtl
            kubectl = KubeCtl()
            
            analysis = {
                "cancel_service_logs": [],
                "payment_service_logs": [],
                "order_service_logs": [],
                "fault_messages_found": False,
                "delay_evidence": False,
            }
            
            services = ["ts-cancel-service", "ts-inside-payment-service", "ts-order-service"]
            
            for service in services:
                try: 
                    # Get pod name for the service
                    pod_name = kubectl.get_pod_name(self.namespace, f"app={service}")
                    if pod_name:
                        # Get logs
                        logs = kubectl.get_pod_logs(pod_name, self.namespace, tail=50)
                        if logs:
                            analysis[f"{service.replace('-', '_')}_logs"] = logs.split("\n")
                            
                            # Check for fault evidence
                            if "F1 FAULT INJECTED" in logs:
                                analysis["fault_messages_found"] = True
                            
                            if "8-second delay" in logs or "8000" in logs:
                                analysis["delay_evidence"] = True
                        
                except Exception as e:
                    logger.warning(f"Failed to get logs for {service}: {e}")
                    
            self.results["logs_captured"] = analysis
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing logs: {e}")
            return {}

    def get_health_status(self) -> Dict[str, bool]:
        """
        Get health status of F1 fault injection system.
        
        Returns:
            Dict: Health check results
        """
        return self.fault_injector.health_check()

    def oracle(self) -> bool:
        """
        Oracle to detect if F1 fault is working correctly.
        
        Returns:
            bool: True if F1 fault behavior is detected
        """
        try:
            fault_status = self.check_fault_status()
            log_analysis = self.analyze_logs()
            
            if fault_status == "on":
                if log_analysis.get("fault_messages_found", False):
                    print(f"[TrainTicket F1] Oracle: F1 fault is active and logging correctly")
                    return True
                else:
                    print(f"[TrainTicket F1] Oracle: F1 fault is active but no log evidence")
                    return False
            else:
                print(f"[TrainTicket F1] Oracle: F1 fault is not active")
                return False
                
        except Exception as e:
            logger.error(f"Error in F1 oracle: {e}")
            return False

    def get_results(self) -> Dict[str, Any]:
        """
        Get comprehensive results of F1 fault injection.
        
        Returns:
            Dict: Complete results including timing and logs
        """
        self.results.update(
            {
                "fault_status": self.check_fault_status(),
                "health_status": self.get_health_status(),
                "log_analysis": self.analyze_logs(),
            }
        )
        
        # Also include oracle results
        self.results["detection_result"] = self.detection_oracle.evaluate()
        self.results["localization_result"] = self.localization_oracle.evaluate()
        
        return self.results


def main():
    """Example usage of TrainTicket F1 problem."""
    problem = TrainTicketF1AsyncMessageOrderProblem()

    print("=== TrainTicket F1 Async Message Order Problem ===")

    health = problem.get_health_status()
    print(f"Health status: {health}")

    print(f"Current fault status: {problem.check_fault_status()}")

    if problem.inject_fault():
        print("F1 fault injected successfully")
        problem.start_workload()
        
        time.sleep(2)
        
        if problem.oracle():
            print("F1 fault is working correctly")
        else:
            print("F1 fault may not be working as expected")
            
        if problem.recover_fault():
            print("F1 fault recovered successfully")
        else:
            print("Failed to recover F1 fault")
    else:
        print("Failed to inject F1 fault")

    results = problem.get_results()
    print(f"Final results: {results}")


if __name__ == "__main__":
    main()
