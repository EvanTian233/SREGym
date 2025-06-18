"""TrainTicket Fault Injector

Provides fault injection capabilities for TrainTicket microservices
through feature flags (flagd). Supports all 22 documented faults.

This injector manages fault states by updating flagd ConfigMaps
and restarting the flagd deployment to apply changes.
"""

import json
import time
import logging
from typing import Dict, List, Any, Optional

from srearena.service.kubectl import KubeCtl

logger = logging.getLogger(__name__)


class TrainTicketFaultInjector:
    """Fault injector for TrainTicket microservices.
    
    Manages 22 different fault scenarios through feature flags.
    """
    
    def __init__(self, namespace: str = "train-ticket"):
        self.namespace = namespace
        self.kubectl = KubeCtl()
        self.configmap_name = "flagd-config"
        self.flagd_deployment = "flagd"
        
        # Map of all 22 TrainTicket faults
        self.fault_mapping = {
            "fault-1-async-message-order": "F1: Async message order violation in order cancellation",
            "fault-2-cpu-occupancy": "F2: High CPU usage in service",
            "fault-3-memory-leak": "F3: Memory leak in service",
            "fault-4-connection-pool-exhaustion": "F4: Database connection pool exhaustion",
            "fault-5-network-partition": "F5: Network partition between services",
            "fault-6-disk-space-full": "F6: Disk space exhaustion",
            "fault-7-service-unavailable": "F7: Service becomes unavailable",
            "fault-8-database-lock-timeout": "F8: Database lock timeout",
            "fault-9-message-queue-overflow": "F9: Message queue overflow",
            "fault-10-slow-database-query": "F10: Slow database queries",
            "fault-11-configuration-error": "F11: Configuration error",
            "fault-12-authentication-failure": "F12: Authentication failures",
            "fault-13-cache-miss-storm": "F13: Cache miss storm",
            "fault-14-http-timeout": "F14: HTTP request timeouts",
            "fault-15-data-inconsistency": "F15: Data inconsistency",
            "fault-16-service-discovery-failure": "F16: Service discovery failure",
            "fault-17-load-balancer-failure": "F17: Load balancer failure",
            "fault-18-session-timeout": "F18: Session timeout issues",
            "fault-19-payment-gateway-error": "F19: Payment gateway errors",
            "fault-20-email-service-failure": "F20: Email service failure",
            "fault-21-file-upload-failure": "F21: File upload failures",
            "fault-22-monitoring-system-failure": "F22: Monitoring system failure"
        }
        
    def inject_fault(self, fault_name: str) -> bool:
        """Inject a specific fault by enabling its feature flag.
        
        Args:
            fault_name: Name of the fault to inject (e.g., "fault-1-async-message-order")
            
        Returns:
            bool: True if fault injection successful
        """
        print(f"[TrainTicket] Injecting fault: {fault_name}")
        return self._set_fault_state(fault_name, "on")
        
    def recover_fault(self, fault_name: str) -> bool:
        """Recover from a specific fault by disabling its feature flag.
        
        Args:
            fault_name: Name of the fault to recover from
            
        Returns:
            bool: True if fault recovery successful
        """
        print(f"[TrainTicket] Recovering from fault: {fault_name}")
        return self._set_fault_state(fault_name, "off")
        
    def _get_configmap(self) -> Dict[str, Any]:
        """Get the current flagd ConfigMap.
        
        Returns:
            Dict: Parsed ConfigMap data or empty dict on error
        """
        try:
            result = self.kubectl.exec_command(
                f"kubectl get configmap {self.configmap_name} -n {self.namespace} -o json"
            )
            
            return json.loads(result) if result else {}
            
        except Exception as e:
            logger.error(f"Error getting ConfigMap: {e}")
            return {}
            
    def _update_configmap(self, configmap_data: Dict[str, Any]) -> bool:
        """Update the flagd ConfigMap.
        
        Args:
            configmap_data: Updated ConfigMap data
            
        Returns:
            bool: True if update successful
        """
        try:
            # Create temporary file for kubectl apply
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                json.dump(configmap_data, f)
                temp_path = f.name
            
            result = self.kubectl.exec_command(f"kubectl apply -f {temp_path}")
            
            # Clean up temp file
            import os
            if os.path.exists(temp_path):
                os.remove(temp_path)
                
            return bool(result)
        except Exception as e:
            logger.error(f"Error updating ConfigMap: {e}")
            return False
            
    def _set_fault_state(self, fault_name: str, state: str) -> bool:
        """Set the state of a specific fault.
        
        Args:
            fault_name: Name of the fault
            state: "on" or "off"
            
        Returns:
            bool: True if state change successful
        """
        try:
            # Get current ConfigMap
            configmap = self._get_configmap()
            if not configmap:
                print("Failed to get ConfigMap")
                return False
                
            # Parse the flags YAML
            import yaml
            flags_yaml = configmap.get("data", {}).get("flags.yaml", "")
            flags_data = yaml.safe_load(flags_yaml)
            
            if not flags_data or "flags" not in flags_data:
                print("Invalid flags data in ConfigMap")
                return False
                
            # Update the specific fault's defaultVariant
            if fault_name in flags_data["flags"]:
                flags_data["flags"][fault_name]["defaultVariant"] = state
                
                # Convert back to YAML
                updated_yaml = yaml.dump(flags_data, default_flow_style=False)
                
                # Update ConfigMap
                configmap["data"]["flags.yaml"] = updated_yaml
                
                if self._update_configmap(configmap):
                    # Restart flagd to apply changes
                    self._restart_flagd()
                    return True
                else:
                    print("Failed to update ConfigMap")
                    return False
            else:
                print(f"Fault {fault_name} not found in ConfigMap")
                return False
                
        except Exception as e:
            logger.error(f"Error setting fault state: {e}")
            return False
            
    def _restart_flagd(self):
        """Restart flagd deployment to apply ConfigMap changes."""
        print(f"[TrainTicket] Restarting flagd deployment...")
        
        try:
            result = self.kubectl.exec_command(
                f"kubectl rollout restart deployment/{self.flagd_deployment} -n {self.namespace}"
            )
            
        except Exception as e:
            logger.error(f"Error restarting flagd: {e}")
            
        # Wait for rollout to complete
        self._wait_for_rollout()
        
    def _wait_for_rollout(self):
        """Wait for flagd rollout to complete."""
        print(f"[TrainTicket] Waiting for flagd rollout to complete...")
        
        try:
            # Use kubectl wait instead of sleep
            result = self.kubectl.exec_command(
                f"kubectl rollout status deployment/{self.flagd_deployment} -n {self.namespace} --timeout=60s"
            )
            
            if "successfully rolled out" in result:
                print("✅ flagd deployment restarted successfully")
                # Wait for pod to be ready
                self.kubectl.wait_for_ready(self.namespace, selector=f"app={self.flagd_deployment}", max_wait=30)
            else:
                print(f"❌ flagd rollout may have issues")
        except Exception as e: 
            logger.error(f"Error waiting for rollout: {e}")
            
    def health_check(self) -> Dict[str, bool]:
        """Check health of fault injection system.
        
        Returns:
            Dict: Health status of various components
        """
        status = {
            "configmap_exists": False,
            "flagd_running": False,
            "flagd_ready": False,
            "flags_loaded": False
        }
        
        try:
            # Check ConfigMap
            cm_result = self.kubectl.exec_command(f"kubectl get configmap {self.configmap_name} -n {self.namespace}")
            status["configmap_exists"] = bool(cm_result)
            
            # Check flagd deployment
            deploy_result = self.kubectl.exec_command(f"kubectl get deployment {self.flagd_deployment} -n {self.namespace}")
            status["flagd_running"] = bool(deploy_result)
            
            # Check if we can list available faults
            faults = self.list_available_faults()
            status["flags_loaded"] = len(faults) > 0
            
        except Exception as e:
            logger.error(f"Error in health check: {e}")
            
        return status
        
    def get_fault_status(self, fault_name: str) -> str:
        """Get current status of a specific fault.
        
        Args:
            fault_name: Name of the fault
            
        Returns:
            str: "on", "off", or "unknown"
        """
        try:
            result = self.kubectl.exec_command(
                f"kubectl get configmap {self.configmap_name} -n {self.namespace} -o jsonpath='{{.data.flags\\.yaml}}'"
            )
            
            if result and fault_name in result:
                # Parse YAML to check defaultVariant
                import yaml
                flags_data = yaml.safe_load(result)
                
                if "flags" in flags_data and fault_name in flags_data["flags"]:
                    return flags_data["flags"][fault_name].get("defaultVariant", "unknown")
                    
        except Exception as e:
            logger.error(f"Error getting fault status: {e}")
            
        return "unknown"
        
    def list_available_faults(self) -> List[str]:
        """List all available fault names.
        
        Returns:
            List[str]: List of fault names
        """
        return list(self.fault_mapping.keys())
        
    def get_fault_description(self, fault_name: str) -> Optional[str]:
        """Get description of a specific fault.
        
        Args:
            fault_name: Name of the fault
            
        Returns:
            Optional[str]: Fault description or None if not found
        """
        return self.fault_mapping.get(fault_name)


# Example usage
if __name__ == "__main__":
    print("TrainTicketFaultInjector - Use via SREArena CLI")
