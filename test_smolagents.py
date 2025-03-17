"""
Simple test script for SmolAgents.
"""

import os
from dotenv import load_dotenv
from smolagents import CodeAgent, tool, LiteLLMModel

# Load environment variables from .env file
load_dotenv()

# Get API key from environment
api_key = os.environ.get("OPENAI_API_KEY")
if not api_key:
    api_key = input("Enter your OpenAI API key: ")

# Define a simple tool
@tool
def hello_world(name: str) -> str:
    """
    Say hello to someone.
    
    Args:
        name: The name of the person to greet
        
    Returns:
        str: A greeting message
    """
    return f"Hello, {name}!"

def main():
    # Initialize the model
    model = LiteLLMModel(
        model_id="gpt-3.5-turbo",
        api_key=api_key
    )
    
    # Create the agent
    agent = CodeAgent(
        tools=[hello_world],
        model=model,
        max_steps=3
    )
    
    # Run the agent
    prompt = "Please say hello to John."
    print(f"Running agent with prompt: '{prompt}'")
    
    result = agent.run(prompt)
    
    print("\n=== Result ===")
    print(result)

if __name__ == "__main__":
    main() 