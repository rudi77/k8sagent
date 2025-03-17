"""
KubectlExecutionTool for interacting with Kubernetes clusters.
"""

import subprocess
from typing import Any, Dict, List, Optional

from kubernetes import client, config
from kubernetes.client.rest import ApiException
from smolagents import tool

from src.config.settings import settings
from src.utils.logging import logger


@tool
def kubectl_exec(command: str) -> str:
    """
    Executes a kubectl command and returns the output.
    
    Args:
        command: The kubectl command to execute (without 'kubectl' prefix)
    """
    try:
        result = subprocess.run(f"kubectl {command}", shell=True, capture_output=True, text=True)
        return result.stdout if result.returncode == 0 else result.stderr
    except Exception as e:
        error_msg = f"Error executing kubectl {command}: {str(e)}"
        logger.error(error_msg)
        return error_msg


class KubectlClient:
    """Helper class for interacting with Kubernetes using the Python client."""
    
    def __init__(self, context: Optional[str] = None):
        """
        Initialize the KubectlClient.
        
        Args:
            context: Kubernetes context to use
        """
        self.context = context or settings.kubernetes_context
        self.namespace = settings.kubernetes_namespace
        
        # Load kubernetes configuration
        try:
            config.load_kube_config(context=self.context)
            self.core_v1 = client.CoreV1Api()
            self.apps_v1 = client.AppsV1Api()
            logger.info(f"Successfully initialized Kubernetes client with context: {self.context}")
        except Exception as e:
            logger.error(f"Failed to initialize Kubernetes client: {str(e)}")
            raise
    
    def get_nodes(self) -> List[Dict[str, Any]]:
        """Get information about all nodes in the cluster."""
        try:
            nodes = self.core_v1.list_node()
            return [
                {
                    "name": node.metadata.name,
                    "status": node.status.conditions[-1].type,
                    "ready": any(
                        cond.type == "Ready" and cond.status == "True"
                        for cond in node.status.conditions
                    ),
                    "cpu": node.status.capacity.get("cpu"),
                    "memory": node.status.capacity.get("memory"),
                }
                for node in nodes.items
            ]
        except ApiException as e:
            logger.error(f"Error getting nodes: {str(e)}")
            raise
    
    def get_pods(self, namespace: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get information about pods in the specified namespace.
        
        Args:
            namespace: Kubernetes namespace (defaults to settings.kubernetes_namespace)
        """
        namespace = namespace or self.namespace
        try:
            pods = self.core_v1.list_namespaced_pod(namespace)
            return [
                {
                    "name": pod.metadata.name,
                    "status": pod.status.phase,
                    "ready": all(
                        container.ready for container in pod.status.container_statuses
                    ) if pod.status.container_statuses else False,
                    "restarts": sum(
                        container.restart_count
                        for container in pod.status.container_statuses
                    ) if pod.status.container_statuses else 0,
                    "node": pod.spec.node_name,
                }
                for pod in pods.items
            ]
        except ApiException as e:
            logger.error(f"Error getting pods in namespace {namespace}: {str(e)}")
            raise
    
    def get_events(self, namespace: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get recent events from the specified namespace.
        
        Args:
            namespace: Kubernetes namespace (defaults to settings.kubernetes_namespace)
        """
        namespace = namespace or self.namespace
        try:
            events = self.core_v1.list_namespaced_event(namespace)
            return [
                {
                    "type": event.type,
                    "reason": event.reason,
                    "message": event.message,
                    "count": event.count,
                    "first_timestamp": event.first_timestamp,
                    "last_timestamp": event.last_timestamp,
                    "involved_object": {
                        "kind": event.involved_object.kind,
                        "name": event.involved_object.name,
                    },
                }
                for event in events.items
            ]
        except ApiException as e:
            logger.error(f"Error getting events in namespace {namespace}: {str(e)}")
            raise
    
    def get_pod_logs(
        self,
        pod_name: str,
        namespace: Optional[str] = None,
        container: Optional[str] = None,
        tail_lines: int = 100
    ) -> str:
        """
        Get logs from a specific pod.
        
        Args:
            pod_name: Name of the pod
            namespace: Kubernetes namespace
            container: Container name (if pod has multiple containers)
            tail_lines: Number of lines to return from the end of the logs
        """
        namespace = namespace or self.namespace
        try:
            return self.core_v1.read_namespaced_pod_log(
                name=pod_name,
                namespace=namespace,
                container=container,
                tail_lines=tail_lines
            )
        except ApiException as e:
            logger.error(
                f"Error getting logs for pod {pod_name} in namespace {namespace}: {str(e)}"
            )
            raise
    
    def describe_pod(self, pod_name: str, namespace: Optional[str] = None) -> Dict[str, Any]:
        """
        Get detailed information about a specific pod.
        
        Args:
            pod_name: Name of the pod
            namespace: Kubernetes namespace
        """
        namespace = namespace or self.namespace
        try:
            pod = self.core_v1.read_namespaced_pod(
                name=pod_name,
                namespace=namespace
            )
            return {
                "name": pod.metadata.name,
                "namespace": pod.metadata.namespace,
                "status": pod.status.phase,
                "ip": pod.status.pod_ip,
                "node": pod.spec.node_name,
                "start_time": pod.status.start_time,
                "containers": [
                    {
                        "name": container.name,
                        "image": container.image,
                        "ready": container.ready,
                        "restart_count": container.restart_count,
                        "state": next(iter(container.state.to_dict().keys())),
                    }
                    for container in pod.status.container_statuses
                ] if pod.status.container_statuses else [],
                "conditions": [
                    {
                        "type": condition.type,
                        "status": condition.status,
                        "message": condition.message,
                    }
                    for condition in pod.status.conditions
                ] if pod.status.conditions else [],
            }
        except ApiException as e:
            logger.error(
                f"Error describing pod {pod_name} in namespace {namespace}: {str(e)}"
            )
            raise


# Additional SmolAgents tools for Kubernetes operations
@tool
def get_nodes() -> str:
    """Get information about all nodes in the Kubernetes cluster."""
    return kubectl_exec("get nodes -o wide")


@tool
def get_pods(namespace: Optional[str] = None) -> str:
    """
    Get information about pods in the specified namespace.
    
    Args:
        namespace: Kubernetes namespace (defaults to default namespace)
    """
    namespace_arg = f"-n {namespace}" if namespace else "--all-namespaces"
    return kubectl_exec(f"get pods {namespace_arg} -o wide")


@tool
def get_events(namespace: Optional[str] = None) -> str:
    """
    Get recent events from the specified namespace.
    
    Args:
        namespace: Kubernetes namespace (defaults to all namespaces)
    """
    namespace_arg = f"-n {namespace}" if namespace else "--all-namespaces"
    return kubectl_exec(f"get events {namespace_arg}")


@tool
def describe_pod(pod_name: str, namespace: Optional[str] = None) -> str:
    """
    Get detailed information about a specific pod.
    
    Args:
        pod_name: Name of the pod
        namespace: Kubernetes namespace
    """
    namespace_arg = f"-n {namespace}" if namespace else ""
    return kubectl_exec(f"describe pod {pod_name} {namespace_arg}")


@tool
def get_pod_logs(pod_name: str, namespace: Optional[str] = None, tail_lines: int = 100) -> str:
    """
    Get logs from a specific pod.
    
    Args:
        pod_name: Name of the pod
        namespace: Kubernetes namespace
        tail_lines: Number of lines to return from the end of the logs
    """
    namespace_arg = f"-n {namespace}" if namespace else ""
    return kubectl_exec(f"logs {pod_name} {namespace_arg} --tail={tail_lines}")


# List of all kubectl tools for easy import
kubectl_tools = [
    kubectl_exec,
    get_nodes,
    get_pods,
    get_events,
    describe_pod,
    get_pod_logs
] 