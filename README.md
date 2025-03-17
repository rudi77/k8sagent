# ReAct-Kubernetes-Monitoring-Agent

An intelligent Kubernetes monitoring agent that uses ReAct framework with RAG (Retrieval-Augmented Generation) and ChromaDB for automated cluster monitoring and problem resolution.

## Features

- 🤖 Automated Kubernetes monitoring with kubectl
- 🧠 LLM-powered decision making using ReAct framework via SmolAgents
- 📚 Long-term memory with RAG using ChromaDB
- 🔄 Self-healing capabilities
- 📢 Multi-channel notifications (Slack, Teams, Email)

## Prerequisites

- Python 3.9+
- Kubernetes cluster and kubectl configured
- OpenAI API key or Azure OpenAI endpoint
- (Optional) Slack/Teams webhook URLs for notifications

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/k8sagent.git
cd k8sagent
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

## Project Structure

```
k8sagent/
├── src/
│   ├── tools/          # SmolAgents tools for kubectl and notifications
│   ├── models/         # RAGK8sAgent implementation
│   ├── database/       # ChromaDB vector store and tools
│   ├── utils/          # Helper functions
│   └── config/         # Configuration management
├── tests/              # Test files
├── requirements.txt    # Project dependencies
└── README.md          # Project documentation
```

## Usage

1. Start the monitoring agent:
```bash
python src/main.py
```

2. Run a single monitoring cycle:
```bash
python src/main.py --single-run
```

3. Customize the monitoring:
```bash
python src/main.py --context my-cluster --namespace monitoring --interval 600
```

## How It Works

The agent uses the SmolAgents framework to implement the ReAct (Reasoning + Acting) pattern:

1. **Reasoning**: The agent analyzes the Kubernetes cluster state using an LLM
2. **Acting**: Based on the analysis, it takes appropriate actions:
   - Searches for similar past issues in ChromaDB
   - Executes kubectl commands to resolve issues
   - Sends notifications when human intervention is needed
   - Stores new problems and solutions for future reference

## Configuration

The agent can be configured through environment variables or a configuration file. Key settings include:

- `OPENAI_API_KEY`: Your OpenAI API key
- `KUBERNETES_CONTEXT`: Kubernetes context to monitor
- `CHROMA_PERSIST_DIR`: Directory for ChromaDB persistence
- `NOTIFICATION_CHANNELS`: Enabled notification channels

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 