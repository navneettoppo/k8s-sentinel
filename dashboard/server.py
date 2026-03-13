"""
FastAPI server for K3s Sentinel Dashboard
Provides REST API + WebSocket for real-time updates
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from contextlib import asynccontextmanager

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import Settings

logger = logging.getLogger(__name__)

# Global state
settings = Settings()
agent_instance = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global agent_instance
    # Initialize agent on startup
    try:
        from main import K3sSentinelAgent
        agent_instance = K3sSentinelAgent()
        logger.info("Dashboard connected to K3s-Sentinel agent")
    except Exception as e:
        logger.warning(f"Could not initialize agent: {e}")
    yield
    # Cleanup
    if agent_instance:
        await agent_instance.stop()

app = FastAPI(title="K3s Sentinel Dashboard", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount dashboard static files
dashboard_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=dashboard_dir), name="static")

# Connection manager for WebSocket
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass

manager = ConnectionManager()

# Pydantic models
class NodeInfo(BaseModel):
    name: str
    status: str
    roles: list[str]
    cpu: str
    memory: str
    cpu_usage: float = 0
    memory_usage: float = 0

class AlertInfo(BaseModel):
    id: str
    title: str
    severity: str
    resource: str
    message: str
    timestamp: str
    resolved: bool = False

class TopologyNode(BaseModel):
    id: str
    type: str
    name: str
    status: str
    parents: list[str] = []
    children: list[str] = []

class ActionResult(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None

# API Routes
@app.get("/")
async def root():
    from fastapi.responses import FileResponse
    return FileResponse(dashboard_dir / "index.html")

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@app.get("/api/stats")
async def get_stats():
    """Get cluster statistics"""
    try:
        if agent_instance and agent_instance.context_engine:
            stats = await agent_instance.context_engine.get_cluster_stats()
            return stats
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
    return {"nodes": 0, "pods": 0, "alerts": 0, "healthy": 0}

@app.get("/api/nodes")
async def get_nodes(namespace: Optional[str] = None):
    """Get cluster nodes"""
    try:
        if agent_instance and agent_instance.telemetry_collector:
            nodes = await agent_instance.telemetry_collector.get_nodes()
            return {"nodes": nodes}
    except Exception as e:
        logger.error(f"Error getting nodes: {e}")
    return {"nodes": []}

@app.get("/api/pods")
async def get_pods(namespace: Optional[str] = None):
    """Get cluster pods"""
    try:
        if agent_instance and agent_instance.telemetry_collector:
            pods = await agent_instance.telemetry_collector.get_pods(namespace)
            return {"pods": pods}
    except Exception as e:
        logger.error(f"Error getting pods: {e}")
    return {"pods": []}

@app.get("/api/alerts")
async def get_alerts(limit: int = 20):
    """Get recent alerts"""
    try:
        if agent_instance and agent_instance.alert_dispatcher:
            alerts = await agent_instance.alert_dispatcher.get_recent_alerts(limit)
            return {"alerts": alerts}
    except Exception as e:
        logger.error(f"Error getting alerts: {e}")
    return {"alerts": []}

@app.get("/api/topology")
async def get_topology():
    """Get resource topology graph"""
    try:
        if agent_instance and agent_instance.context_engine:
            topology = await agent_instance.context_engine.get_topology()
            return topology
    except Exception as e:
        logger.error(f"Error getting topology: {e}")
    return {"nodes": [], "edges": []}

@app.post("/api/actions/scan")
async def scan_cluster():
    """Trigger a cluster scan"""
    try:
        if agent_instance:
            await agent_instance.context_engine.update_topology()
            return ActionResult(success=True, message="Scan completed", data={})
        return ActionResult(success=False, message="Agent not initialized")
    except Exception as e:
        return ActionResult(success=False, message=str(e))

@app.post("/api/actions/clear-cache")
async def clear_cache():
    """Clear agent cache"""
    try:
        if agent_instance:
            await agent_instance.context_engine.clear_cache()
            return ActionResult(success=True, message="Cache cleared", data={})
        return ActionResult(success=False, message="Agent not initialized")
    except Exception as e:
        return ActionResult(success=False, message=str(e))

@app.post("/api/actions/export")
async def export_report():
    """Export analysis report"""
    try:
        if agent_instance:
            report = await agent_instance.context_engine.export_report()
            return ActionResult(success=True, message="Report exported", data=report)
        return ActionResult(success=False, message="Agent not initialized")
    except Exception as e:
        return ActionResult(success=False, message=str(e))

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for real-time updates"""
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Handle incoming messages if needed
            message = json.loads(data)
            if message.get("type") == "ping":
                await websocket.send_json({"type": "pong", "timestamp": datetime.utcnow().isoformat()})
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Background task to broadcast updates
async def broadcast_updates():
    while True:
        try:
            if agent_instance:
                stats = await get_stats()
                await manager.broadcast({"type": "stats", "data": stats})
        except Exception as e:
            logger.error(f"Broadcast error: {e}")
        await asyncio.sleep(10)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
