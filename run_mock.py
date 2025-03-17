"""
Script to run the K8s monitoring agent with mock data.
This allows testing the agent without a real Kubernetes cluster.
"""

import os
import argparse
from unittest.mock import patch

from src.models.monitoring_agent import RAGK8sAgent
from src.utils.logging import logger


# Mock data for Kubernetes commands
MOCK_NODES = """
NAME           STATUS   ROLES                  AGE   VERSION
master-node    Ready    control-plane,master   92d   v1.26.1
worker-node1   Ready    worker                 92d   v1.26.1
worker-node2   NotReady worker                 92d   v1.26.1
"""

MOCK_PODS = """
NAMESPACE     NAME                                      READY   STATUS             RESTARTS   AGE
kube-system   coredns-787d4945fb-9mzcv                  1/1     Running            0          92d
kube-system   etcd-master-node                          1/1     Running            0          92d
kube-system   kube-apiserver-master-node                1/1     Running            0          92d
kube-system   kube-controller-manager-master-node       1/1     Running            0          92d
kube-system   kube-proxy-4jfcj                          1/1     Running            0          92d
kube-system   kube-scheduler-master-node                1/1     Running            0          92d
default       nginx-deployment-66b6c48dd5-7tzxz         1/1     Running            0          12h
default       redis-deployment-5f58584d84-vqtlm         0/1     CrashLoopBackOff   5          30m
monitoring    prometheus-deployment-5f58584d84-2jfcj    1/1     Running            0          2d
"""

MOCK_EVENTS = """
NAMESPACE     LAST SEEN   TYPE      REASON              OBJECT                                MESSAGE
default       30m         Warning   BackOff             pod/redis-deployment-5f58584d84-vqtlm   Back-off restarting failed container
kube-system   92d         Normal    Started             pod/coredns-787d4945fb-9mzcv            Started container coredns
default       12h         Normal    Created             pod/nginx-deployment-66b6c48dd5-7tzxz   Created container nginx
default       12h         Normal    Started             pod/nginx-deployment-66b6c48dd5-7tzxz   Started container nginx
default       30m         Normal    Scheduled           pod/redis-deployment-5f58584d84-vqtlm   Successfully assigned default/redis-deployment-5f58584d84-vqtlm to worker-node1
default       30m         Normal    Pulled              pod/redis-deployment-5f58584d84-vqtlm   Container image "redis:latest" already present on machine
default       30m         Normal    Created             pod/redis-deployment-5f58584d84-vqtlm   Created container redis
default       30m         Warning   Failed              pod/redis-deployment-5f58584d84-vqtlm   Error: failed to start container "redis": Error response from daemon: OCI runtime create failed: container_linux.go:380: starting container process caused: exec: "invalid-command": executable file not found in $PATH: unknown
"""


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Run K8s monitoring agent with mock data"
    )
    
    parser.add_argument(
        "--openai-api-key",
        type=str,
        help="OpenAI API key (or set OPENAI_API_KEY env var)",
        default=os.environ.get("OPENAI_API_KEY")
    )
    
    parser.add_argument(
        "--openai-model",
        type=str,
        help="OpenAI model to use",
        default="gpt-4-turbo-preview"
    )
    
    return parser.parse_args()


def mock_kubectl_command(command):
    """Mock kubectl command execution."""
    if "get nodes" in command:
        return MOCK_NODES
    elif "get pods" in command:
        return MOCK_PODS
    elif "get events" in command:
        return MOCK_EVENTS
    else:
        return f"Mock command executed: {command}"


def main():
    """Run the agent with mock data."""
    args = parse_args()
    
    if not args.openai_api_key:
        print("Error: OpenAI API key is required. Set it with --openai-api-key or OPENAI_API_KEY env var.")
        return
    
    # Patch the kubectl command execution
    with patch("src.tools.kubectl_tool.KubectlClient.run_command", side_effect=mock_kubectl_command):
        try:
            # Initialize the agent
            agent = RAGK8sAgent(
                openai_api_key=args.openai_api_key,
                openai_model=args.openai_model
            )
            
            logger.info(f"Running agent with mock data using model: {args.openai_model}")
            
            # Run a single monitoring cycle
            result = agent.monitor_once()
            
            logger.info("Monitoring completed")
            print("\n=== Monitoring Result ===")
            print(result)
            
        except Exception as e:
            logger.error(f"Error running agent: {str(e)}")
            raise


if __name__ == "__main__":
    main() 