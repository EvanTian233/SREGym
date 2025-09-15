from srearena.service.kubectl import KubeCtl


class NormalOperationGenerator:
    """ This generator is used to generate normal operation for the system. """
    def __init__(self):
        self.kubectl = KubeCtl()
        
    def trigger_rollout(self, deployment_name: str, namespace: str):
        self.kubectl.exec_command(f"kubectl rollout restart deployment {deployment_name} -n {namespace}")
        
    def trigger_scale(self, deployment_name: str, namespace: str, replicas: int):
        self.kubectl.exec_command(f"kubectl scale deployment {deployment_name} -n {namespace} --replicas={replicas}")
        