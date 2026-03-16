# K3s Sentinel Dashboard - React + Chakra UI

React version of the K3s Sentinel dashboard with Chakra UI components.

## Installation

```bash
cd Kiro-K3s-sentinel/frontend
npm install
```

## Running

```bash
npm start
# Open http://localhost:3000
```

## Features

- **Chakra UI** - Modern component library with dark mode
- **React** - Full React application
- **Tabs** - Switch between Nodes, Pods, ConfigMaps, Secrets, ServiceAccounts, Events, CronJobs, Jobs
- **Pod Logs** - View container logs in modal
- **Export PDF** - Download RCA reports
- **Real-time Stats** - Auto-refresh every 30 seconds

## API Connection

Update `src/App.js` to change API base URL:
```javascript
const API_BASE = 'http://localhost:8000/api';
```

## Build for Production

```bash
npm run build
# Output in build/ folder
```
