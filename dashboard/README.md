# K3s-Sentinel Dashboard

Modern React dashboard for K3s-Sentinel - AI-powered K3s cluster root cause analysis.

## Features

- **Cluster Overview**: Real-time monitoring of nodes, pods, and services
- **Root Cause Analysis**: AI-powered RCA with symptom-to-cause tracing
- **Alert Management**: View and manage cluster alerts with severity levels
- **Settings**: Configure LLM providers, alert channels, and cluster connections
- **Dark Theme**: Beautiful Dribbble-inspired dark UI with green/orange accents

## Quick Start

The dashboard is part of the K3s-Sentinel project. See the [main project README](../README.md) for instructions.

```bash
cd /workspace/k3s-sentinel
cp .env.example .env
./start.sh
```

Then access the dashboard at: http://localhost:3000 (frontend) or http://localhost:8000 (backend with embedded dashboard)

## Development

```bash
cd dashboard
pnpm install
pnpm dev
pnpm build
```

## Tech Stack

- **React 18** with TypeScript
- **Vite** for build tooling
- **Tailwind CSS** for styling
- **Framer Motion** for animations
- **React Router** for navigation
- **Lucide React** for icons
- **Sonner** for toast notifications
- **Recharts** for data visualization

## Project Structure

```
src/
├── components/
│   ├── layout/       # Sidebar, Header
│   ├── dashboard/    # Dashboard components
│   ├── alerts/        # Alert components
│   └── settings/     # Settings components
├── context/          # React contexts
├── hooks/             # Custom hooks
├── pages/             # Page components
├── services/          # API services
├── types/             # TypeScript types
└── utils/             # Utility functions
```

## API Integration

The dashboard integrates with the K3s-Sentinel backend API:

- `http://localhost:8000/api/health` - Health check
- `http://localhost:8000/api/cluster/info` - Cluster information
- `http://localhost:8000/api/cluster/nodes` - Node list
- `http://localhost:8000/api/cluster/pods` - Pod list
- `http://localhost:8000/api/cluster/services` - Service list
- `http://localhost:8000/api/alerts` - Alert list

## License

MIT License
