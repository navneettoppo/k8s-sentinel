# K3s-Sentinel: AI Agent for K3s Cluster Root Cause Analysis

K3s-Sentinel is an intelligent observability agent designed specifically for K3s clusters. It monitors cluster health, detects anomalies, and uses AI-powered analysis to trace symptoms back to their root causes.

## Quick Start

### 1. Clone or Navigate to Project

```bash
cd /workspace/k3s-sentinel
```

### 2. Configure Environment

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your settings
nano .env
```

**Required Settings:**
- `LLM_API_KEY` - Your LLM API key (OpenAI, Anthropic, etc.)

**Optional Settings:**
- `LLM_PROVIDER` - Provider: openai, anthropic, gemini, azure_openai, ollama
- `LLM_MODEL` - Model to use (default: gpt-4)
- Alert channels: Slack, Teams, Email, Webhooks, etc.

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Start K3s-Sentinel

K3s-Sentinel supports multiple interfaces:

**Terminal UI (TUI)** - Full interactive terminal interface:
```bash
python main.py --tui
# or
python main.py --tui --kubeconfig ~/.kube/config
```

**API Server Only:**
```bash
python main.py --api
# or
./start.sh --backend
```

**Dashboard (Web UI):**
```bash
./start.sh
```

### 5. Access Endpoints

| Service | URL | Description |
|---------|-----|-------------|
| **Dashboard** | http://localhost:3000 | Web UI for cluster monitoring |
| **Backend API** | http://localhost:8000 | REST API for cluster operations |
| **API Docs** | http://localhost:8000/docs | Interactive API documentation | |

## Features

- **Real-time Monitoring**: Collects Kubernetes events, logs, and metrics
- **Dependency Graph**: Builds dynamic topology of cluster resources
- **AI-Powered Analysis**: Uses rule-based + LLM-powered root cause analysis
- **RAG Integration**: Leverages K3s troubleshooting knowledge base
- **Multi-channel Alerts**: Supports Slack, Teams, Email, Webhooks, and more
- **K3s-specific**: Built specifically for K3s components (Traefik, Local Path Provisioner, etc.)
- **Terminal UI (TUI)**: Full-featured keyboard-driven terminal interface for cluster management

## Terminal UI (TUI)

The K3s-Sentinel Terminal UI provides a full-featured, keyboard-driven interface for managing K3s clusters.

### Starting the TUI

```bash
# Start with auto-detected kubeconfig
python main.py --tui

# Start with specific kubeconfig
python main.py --tui --kubeconfig ~/.kube/config

# Start with specific namespace
python main.py --tui --namespace default

# Set custom refresh interval (seconds)
python main.py --tui --refresh 15
```

### TUI Panels

The TUI is divided into three main panels:

| Panel | Location | Description |
|-------|----------|-------------|
| **Clusters** | Left | Kubernetes contexts and cluster information |
| **Namespaces** | Left | Namespace selector |
| **Resources** | Center | Pods, services, deployments, nodes, PVCs |
| **Logs** | Center | Pod/container logs viewer |
| **Events** | Right | Cluster events timeline |
| **Alerts** | Right | Active alerts with RCA information |

### Keyboard Shortcuts

#### Navigation

| Key | Action |
|-----|--------|
| `Tab` / `Shift+Tab` | Cycle panels |
| `↑` / `j` | Navigate up in list |
| `↓` / `k` | Navigate down in list |
| `Enter` | Select / drill-down |
| `Esc` / `q` | Back / quit / close |
| `1`-`6` | Switch to panel (1:Clusters, 2:Namespaces, 3:Resources, 4:Logs, 5:Events, 6:Alerts) |

#### Resource Actions

| Key | Action |
|-----|--------|
| `d` | Describe selected resource |
| `l` | View logs for selected pod |
| `e` | Exec into container (shell) |
| `D` | Delete resource |
| `r` | Restart pod |
| `s` | Scale deployment |

#### View & Filter

| Key | Action |
|-----|--------|
| `f` | Filter resources |
| `n` | Change namespace |
| `c` | Switch context |
| `y` | View resource YAML |
| `/` | Fuzzy search |
| `R` | Refresh data |

#### Global

| Key | Action |
|-----|--------|
| `?` | Show help overlay |
| `Ctrl+C` | Force quit |

### Help Overlay

Press `?` to display all keyboard shortcuts with descriptions. Press `Esc` or `q` to close the overlay.

### Kubeconfig Path Resolution

The TUI resolves kubeconfig paths in the following order:

1. CLI flag: `--kubeconfig` / `-k`
2. Environment variable: `KUBECONFIG`
3. Default path: `~/.kube/config`
4. K3s default: `/etc/rancher/k3s/k3s.yaml`

Selected paths are persisted to `~/.config/k3s-sentinel/config.toml`.

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

## API Endpoints

### Cluster Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Health check |
| GET | `/api/health` | Detailed health status |
| POST | `/api/cluster/validate` | Validate kubeconfig |
| POST | `/api/cluster/connect` | Connect to cluster |
| POST | `/api/cluster/disconnect` | Disconnect from cluster |
| GET | `/api/cluster/info` | Get cluster information |
| GET | `/api/cluster/nodes` | List all nodes |
| GET | `/api/cluster/pods` | List all pods |
| GET | `/api/cluster/services` | List all services |

### Alerts

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/alerts` | Get recent alerts with RCA |

### Example API Usage

```bash
# Check health
curl http://localhost:8000/api/health

# Get cluster info
curl http://localhost:8000/api/cluster/info

# Validate kubeconfig
curl -X POST http://localhost:8000/api/cluster/validate \
  -H "Content-Type: application/json" \
  -d '{"kubeconfig_path": "/path/to/kubeconfig"}'

# Get alerts
curl http://localhost:8000/api/alerts
```

## Configuration

All configuration is managed through the `.env` file. Copy `.env.example` to `.env` and customize:

### LLM Configuration

```env
LLM_PROVIDER=openai
LLM_API_KEY=your-api-key-here
LLM_MODEL=gpt-4
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=2000
```

### Alert Configuration

```env
ALERTS_ENABLED=true
ALERT_MIN_SEVERITY=warning
ALERT_COOLDOWN_SECONDS=300

# Slack
SLACK_ENABLED=false
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...

# Teams
TEAMS_ENABLED=false
TEAMS_WEBHOOK_URL=https://outlook.office.com/webhook/...

# Email
EMAIL_ENABLED=false
EMAIL_SMTP_HOST=smtp.gmail.com
EMAIL_USERNAME=your-email@gmail.com
EMAIL_PASSWORD=your-password
```

### Agent Settings

```env
KUBECONFIG_PATH=~/.kube/config
POLL_INTERVAL=10
LOG_LEVEL=INFO
```

## Prerequisites

- **Python 3.9+**
- **Kubernetes/K3s cluster** (optional, for full functionality)
- **kubectl** configured (optional, for cluster operations)

## Installation

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Setup Virtual Environment (Optional)

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
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

## Troubleshooting

### Agent Not Receiving Events

1. Check RBAC permissions:
```bash
kubectl auth can-i get events
```

2. Verify kubeconfig is correct:
```bash
kubectl config current-context
```

### LLM Analysis Not Working

1. Verify API key is set:
```bash
grep LLM_API_KEY .env
```

2. Check network connectivity to LLM provider

### Dashboard Not Loading

1. Check if backend is running:
```bash
curl http://localhost:8000/api/health
```

2. Check dashboard logs:
```bash
tail -f logs/frontend.log
```

## License

MIT License

## Contributing

Contributions are welcome! Please read our contributing guidelines before submitting PRs.
