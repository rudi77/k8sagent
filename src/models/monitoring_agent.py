"""
Main monitoring agent class that integrates all components for Kubernetes monitoring.
Uses SmolAgents framework for ReAct-based decision making.
"""

import json
import time
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from openai import OpenAI
from smolagents import CodeAgent, LiteLLMModel, tool

from src.config.settings import settings
from src.database.vector_store import VectorStore, vector_store_tools
from src.tools.kubectl_tool import KubectlClient, kubectl_tools
from src.tools.notification_tool import NotificationClient, notification_tools
from src.utils.logging import logger


@tool
def analyze_cluster_state(agent: Any) -> str:
    """
    Analyze the current state of the Kubernetes cluster.
    This is a helper tool that gathers information from multiple kubectl commands.
    
    Args:
        agent: The RAGK8sAgent instance
        
    Returns:
        str: A formatted string containing information about nodes, pods, and events
    """
    try:
        # Get nodes, pods, and events
        nodes_output = kubectl_tools[1]()  # get_nodes
        pods_output = kubectl_tools[2]()   # get_pods
        events_output = kubectl_tools[3]() # get_events
        
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
        logger.error(error_msg)
        return error_msg


class RAGK8sAgent:
    """
    Main agent class that monitors Kubernetes clusters using ReAct framework.
    Integrates kubectl operations, ChromaDB for memory, and notifications.
    """
    
    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        openai_model: Optional[str] = None,
        kubernetes_context: Optional[str] = None,
        notification_channels: Optional[List[str]] = None,
        monitoring_interval: Optional[int] = None
    ):
        """
        Initialize the monitoring agent.
        
        Args:
            openai_api_key: OpenAI API key
            openai_model: OpenAI model to use
            kubernetes_context: Kubernetes context
            notification_channels: Notification channels to use
            monitoring_interval: Monitoring interval in seconds
        """
        # Initialize settings
        self.openai_api_key = openai_api_key or settings.openai_api_key
        self.openai_model = openai_model or settings.openai_model
        self.monitoring_interval = monitoring_interval or settings.monitoring_interval
        
        # Initialize LiteLLM model for SmolAgents
        self.model = LiteLLMModel(
            model_id=self.openai_model,
            api_key=self.openai_api_key,
            api_base=settings.openai_api_base
        )
        
        # Initialize helper clients
        self.kubectl_client = KubectlClient(
            context=kubernetes_context or settings.kubernetes_context
        )
        
        # Combine all tools
        self.tools = kubectl_tools + notification_tools + vector_store_tools + [analyze_cluster_state]
        
        # Create the agent
        self.agent = CodeAgent(
            tools=self.tools,
            model=self.model,
            max_steps=10,  # Limit steps per analysis
            planning_interval=3  # Plan every 3 steps
        )
        
        logger.info("RAGK8sAgent initialized successfully")
    
    def generate_analysis_prompt(self) -> str:
        """Generate a prompt for the agent to analyze the cluster state."""
        return """
Analyze the Kubernetes cluster state and identify any issues or potential problems.
Follow these steps:

1. First, use the analyze_cluster_state tool with the agent parameter to get the current state of the cluster.
2. Identify any critical issues that need immediate attention.
3. Check for similar past issues using find_similar_problems.
4. Suggest potential solutions based on the available information.
5. If a solution is found, execute it using kubectl_exec.
6. If the issue requires human intervention, send a notification.
7. Store the problem and solution for future reference using add_problem.

Remember to be thorough in your analysis and provide clear explanations of your reasoning.
"""
    
    def monitor_once(self) -> str:
        """Run a single monitoring cycle and return the result."""
        try:
            # Generate the analysis prompt
            prompt = self.generate_analysis_prompt()
            
            # Run the agent
            result = self.agent.run(prompt)
            
            return result
        except Exception as e:
            error_msg = f"Error in monitoring cycle: {str(e)}"
            logger.error(error_msg)
            return error_msg
    
    def monitor_loop(self):
        """Start the monitoring loop."""
        logger.info(f"Starting monitoring loop with {self.monitoring_interval}s interval")
        
        while True:
            try:
                # Run a monitoring cycle
                result = self.monitor_once()
                logger.info(f"Monitoring cycle completed: {result}")
                
                # Wait for the next cycle
                time.sleep(self.monitoring_interval)
            
            except KeyboardInterrupt:
                logger.info("Monitoring loop interrupted by user")
                break
            
            except Exception as e:
                logger.error(f"Error in monitoring loop: {str(e)}")
                # Try to send a notification about the error
                try:
                    notification_tools[0](
                        message=f"❌ Monitoring agent encountered an error:\n{str(e)}",
                        title="Monitoring Error",
                        severity="error"
                    )
                except:
                    pass
                
                # Wait before retrying
                time.sleep(self.monitoring_interval) 