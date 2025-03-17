"""
Main entry point for the Kubernetes monitoring agent.
"""

import argparse
import sys
from typing import Optional

from src.config.settings import settings
from src.models.monitoring_agent import RAGK8sAgent
from src.utils.logging import logger


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Kubernetes Monitoring Agent with ReAct and RAG"
    )
    
    parser.add_argument(
        "--context",
        type=str,
        help="Kubernetes context to use",
        default=settings.kubernetes_context
    )
    
    parser.add_argument(
        "--namespace",
        type=str,
        help="Kubernetes namespace to monitor",
        default=settings.kubernetes_namespace
    )
    
    parser.add_argument(
        "--interval",
        type=int,
        help="Monitoring interval in seconds",
        default=settings.monitoring_interval
    )
    
    parser.add_argument(
        "--openai-model",
        type=str,
        help="OpenAI model to use",
        default=settings.openai_model
    )
    
    parser.add_argument(
        "--single-run",
        action="store_true",
        help="Run a single monitoring cycle and exit"
    )
    
    return parser.parse_args()


def main(args: Optional[argparse.Namespace] = None):
    """
    Main function to run the monitoring agent.
    
    Args:
        args: Command line arguments
    """
    if args is None:
        args = parse_args()
    
    try:
        # Initialize the monitoring agent
        agent = RAGK8sAgent(
            kubernetes_context=args.context,
            openai_model=args.openai_model,
            monitoring_interval=args.interval
        )
        
        # Log startup information
        logger.info(
            f"Starting Kubernetes monitoring agent:\n"
            f"- Context: {args.context}\n"
            f"- Namespace: {args.namespace}\n"
            f"- Interval: {args.interval}s\n"
            f"- OpenAI Model: {args.openai_model}\n"
            f"- Mode: {'Single run' if args.single_run else 'Continuous monitoring'}"
        )
        
        # Run the agent
        if args.single_run:
            result = agent.monitor_once()
            logger.info(f"Monitoring result: {result}")
        else:
            agent.monitor_loop()
    
    except KeyboardInterrupt:
        logger.info("Monitoring agent stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main() 