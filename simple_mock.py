"""
Simplified script to run the K8s monitoring agent with mock data.
This version doesn't rely on the settings module.
"""

import os
import argparse
from unittest.mock import patch
from dotenv import load_dotenv

from smolagents import CodeAgent, tool, LiteLLMModel

# Load environment variables from .env file
load_dotenv()

# Get API key from environment
api_key = os.environ.get("OPENAI_API_KEY")
if not api_key:
    api_key = input("Enter your OpenAI API key: ")

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


# Define kubectl tools
@tool
def get_nodes() -> str:
    """Get the status of all nodes in the Kubernetes cluster."""
    return MOCK_NODES


@tool
def get_pods() -> str:
    """Get the status of all pods in the Kubernetes cluster."""
    return MOCK_PODS


@tool
def get_events() -> str:
    """Get recent events in the Kubernetes cluster."""
    return MOCK_EVENTS


@tool
def analyze_cluster_state() -> str:
    """
    Analyze the current state of the Kubernetes cluster.
    This is a helper tool that gathers information from multiple kubectl commands.
    """
    try:
        # Get nodes, pods, and events
        nodes_output = get_nodes()
        pods_output = get_pods()
        events_output = get_events()
        
        return f"""
=== Kubernetes Cluster State ===

=== Nodes ===
{nodes_output}

=== Pods ===
{pods_output}

=== Events ===
{events_output}
"""
    except Exception as e:
        error_msg = f"Error analyzing cluster state: {str(e)}"
        print(error_msg)
        return error_msg


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Run simplified K8s monitoring agent with mock data"
    )
    
    parser.add_argument(
        "--model",
        type=str,
        help="OpenAI model to use",
        default="gpt-4o-mini"
    )
    
    return parser.parse_args()


def main():
    """Run the agent with mock data."""
    args = parse_args()
    
    try:
        # Initialize LiteLLM model for SmolAgents
        model = LiteLLMModel(
            model_id=args.model,
            api_key=api_key
        )
        
        # Create the agent with tools
        agent = CodeAgent(
            tools=[get_nodes, get_pods, get_events, analyze_cluster_state],
            model=model,
            max_steps=5
        )
        
        print(f"Running agent with mock data using model: {args.model}")
        
        # Generate the analysis prompt
        prompt = """
Analyze the Kubernetes cluster state and identify any issues or potential problems.
Follow these steps:

1. First, use the analyze_cluster_state tool to get the current state of the cluster.
2. Identify any critical issues that need immediate attention.
3. Suggest potential solutions based on the available information.

Remember to be thorough in your analysis and provide clear explanations of your reasoning.
"""
        
        # Run the agent
        result = agent.run(prompt)
        
        print("\n=== Monitoring Result ===")
        print(result)
        
    except Exception as e:
        print(f"Error running agent: {str(e)}")
        raise


if __name__ == "__main__":
    main() 