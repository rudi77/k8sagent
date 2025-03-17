"""
Test script to verify imports.
"""

try:
    import smolagents
    print(f"SmolAgents version: {smolagents.__version__}")
    
    from src.models.monitoring_agent import RAGK8sAgent, analyze_cluster_state
    print("RAGK8sAgent and analyze_cluster_state imported successfully")
    
    from src.tools.kubectl_tool import kubectl_tools
    print(f"kubectl_tools imported successfully, contains {len(kubectl_tools)} tools")
    
    from src.tools.notification_tool import notification_tools
    print(f"notification_tools imported successfully, contains {len(notification_tools)} tools")
    
    from src.database.vector_store import vector_store_tools
    print(f"vector_store_tools imported successfully, contains {len(vector_store_tools)} tools")
    
    print("\nAll imports successful!")
    print("Note: Skipping RAGK8sAgent initialization as it requires a valid Kubernetes configuration.")
except Exception as e:
    print(f"Error: {str(e)}") 