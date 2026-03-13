# K3s Sentinel Dashboard

Web-based clickops interface for K3s Sentinel.

## Quick Start

```bash
# Install dependencies
pip install fastapi uvicorn pydantic

# Start dashboard
python dashboard/server.py

# Open browser
open http://localhost:8000
```

## Features

- **Real-time Stats**: Nodes, pods, alerts monitoring
- **Node Status**: CPU/memory usage per node
- **Alerts Panel**: Recent alerts with severity levels
- **Topology Graph**: Resource dependency visualization
- **Quick Actions**: Scan, Clear Cache, Export Report
- **Auto-refresh**: Updates every 30 seconds
- **WebSocket**: Live updates without page refresh

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Dashboard UI |
| `/api/health` | GET | Health check |
| `/api/stats` | GET | Cluster statistics |
| `/api/nodes` | GET | List nodes |
| `/api/pods` | GET | List pods |
| `/api/alerts` | GET | Recent alerts |
| `/api/topology` | GET | Resource topology |
| `/api/actions/scan` | POST | Trigger cluster scan |
| `/api/actions/clear-cache` | POST | Clear agent cache |
| `/api/actions/export` | POST | Export report |
| `/ws` | WS | WebSocket for real-time updates |

## Tech Stack

- **Backend**: FastAPI + WebSocket
- **Frontend**: htmx + Tailwind CSS (CDN)
- **No build step required**

## Configuration

Dashboard reads from existing `config/settings.py`. No additional config needed.
