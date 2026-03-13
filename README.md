# K3s-Sentinel: AI Agent for K3s Cluster Root Cause Analysis

K3s-Sentinel is an intelligent observability agent designed specifically for K3s clusters. It monitors cluster health, detects anomalies, and uses AI-powered analysis to trace symptoms back to their root causes.

## Features

- **Real-time Monitoring**: Collects Kubernetes events, logs, and metrics
- **Dependency Graph**: Builds dynamic topology of cluster resources
- **AI-Powered Analysis**: Uses rule-based + LLM-powered root cause analysis
- **RAG Integration**: Leverages K3s troubleshooting knowledge base
- **Multi-channel Alerts**: Supports Slack, webhooks, and email notifications
- **K3s-specific**: Built specifically for K3s components (Traefik, Local Path Provisioner, etc.)

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      K3s-Sentinel                            │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  Telemetry   │  │   Context    │  │    Action     │     │
│  │  Collector   │──│   Engine     │──│   Dispatcher  │     │
│  │              │  │              │  │               │     │
│  │  - Events    │  │  - Topology  │  │  - Alerts     │     │
│  │  - Logs      │  │  - Vector DB │  │  - Webhooks   │     │
│  │  - Metrics   │  │  - History   │  │  - Reports    │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│          │                 │                                 │
│          └────────┬────────┘                                 │
│                   ▼                                          │
│          ┌──────────────┐                                     │
│          │ Analysis Core│                                     │
│          │              │                                     │
│          │ - Symptom   │                                     │
│          │   Detection │                                     │
│          │ - RCA      │                                     │
│          │ - LLM      │                                     │
│          └──────────────┘                                     │
└─────────────────────────────────────────────────────────────┘
```

## Installation

### Prerequisites

- Python 3.9+
- Kubernetes/K3s cluster
- kubectl configured

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Configuration

1. Copy the example configuration:

```bash
cp config/settings.example.py config/settings.py
```

2. Edit `config/settings.py` with your settings:

```python
# LLM Configuration
llm_provider = "openai"  # or "anthropic", "local"
llm_api_key = "your-api-key"

# Alert Configuration
alert_slack_webhook = "https://hooks.slack.com/services/..."
alert_webhook_url = "https://your-webhook.com/alerts"
```

### Running

#### Standalone Mode

```bash
# Set environment variables
export LLM_API_KEY="your-api-key"
export SLACK_WEBHOOK_URL="your-webhook"

# Run the agent
python main.py
```

#### In-Cluster Mode (Kubernetes)

```yaml
# deployment.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: sentinel-system
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: sentinel
  namespace: sentinel-system
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: sentinel
subjects:
- kind: ServiceAccount
  name: sentinel
  namespace: sentinel-system
roleRef:
  kind: ClusterRole
  name: cluster-admin
  apiGroup: rbac.authorization.k8s.io
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: sentinel
  namespace: sentinel-system
spec:
  replicas: 1
  selector:
    matchLabels:
      app: sentinel
  template:
    metadata:
      labels:
        app: sentinel
    spec:
      serviceAccountName: sentinel
      containers:
      - name: sentinel
        image: k3s-sentinel:latest
        env:
        - name: LLM_API_KEY
          valueFrom:
            secretKeyRef:
              name: sentinel-secrets
              key: llm-api-key
        resources:
          limits:
            cpu: 500m
            memory: 512Mi
```

## Usage

### Command Line Options

```bash
python main.py --help

Options:
  --config PATH    Configuration file path
  --log-level      Log level (DEBUG, INFO, WARNING, ERROR)
  --namespace      Kubernetes namespace to monitor
```

### API Usage

```python
from agent.telemetry_collector import TelemetryCollector
from agent.context_engine import ContextEngine
from agent.analysis_core import AnalysisCore
from config.settings import Settings

# Initialize
settings = Settings()
collector = TelemetryCollector(settings)
context = ContextEngine(settings)
analysis = AnalysisCore(settings, context)

# Collect and analyze
events = await collector.get_events()
for event in events:
    result = await analysis.analyze_event(event)
    if result:
        print(f"Root cause: {result.root_cause}")
```

## Supported Issue Types

K3s-Sentinel can detect and analyze:

- **Pod Issues**: CrashLoopBackOff, Evicted, Pending, ImagePullBackOff
- **Node Issues**: NotReady, DiskPressure, MemoryPressure
- **Network Issues**: Service unavailable, Ingress errors
- **Storage Issues**: PVC pending, mount failures
- **Configuration Issues**: ConfigMap/Secret missing, invalid specs

## Root Cause Analysis

The agent traces issues through the dependency graph:

```
Service → Deployment → Pod → PVC → Node
   │          │         │      │     │
   └──────────┴─────────┴──────┴─────┘
                   │
            Symptom (Effect)
                   │
                   ▼
            Root Cause
```

## Configuration Options

| Option | Description | Default |
|--------|-------------|---------|
| `llm_provider` | LLM provider (openai/anthropic/local) | openai |
| `llm_model` | Model to use | gpt-4 |
| `poll_interval` | Event polling interval (seconds) | 10 |
| `log_lines_to_fetch` | Number of log lines to retrieve | 100 |
| `cpu_limit` | CPU limit for agent | 500m |
| `memory_limit` | Memory limit for agent | 512Mi |

## Alert Integration

### Slack

```python
alert_slack_enabled = True
alert_slack_webhook = "https://hooks.slack.com/services/..."
```

### Webhook

```python
alert_webhook_url = "https://your-webhook.com/alerts"
```

### Custom

Extend `ActionDispatcher` to add custom alert handlers.

## Troubleshooting

### Agent Not Receiving Events

1. Check RBAC permissions:
```bash
kubectl auth can-i get events --as=system:serviceaccount:sentinel-system:sentinel
```

2. Verify kubeconfig is correct:
```bash
kubectl config current-context
```

### LLM Analysis Not Working

1. Verify API key is set:
```bash
echo $LLM_API_KEY
```

2. Check network connectivity to LLM provider

## Development

### Running Tests

```bash
pytest tests/
```

### Code Style

```bash
black agent/ config/ utils/
mypy agent/
```

## License

MIT License

## Contributing

Contributions are welcome! Please read our contributing guidelines before submitting PRs.
