"""
FastAPI Backend for K3s-Sentinel Dashboard.
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import os
import logging
from datetime import datetime

app = FastAPI(title="K3s-Sentinel API")

# Enable CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global reference to the agent instance
agent_instance = None

class ConfigUpdate(BaseModel):
    kubeconfig_path: Optional[str] = None
    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None
    llm_api_key: Optional[str] = None
    poll_interval: Optional[int] = None

@app.get("/api/v1/status")
async def get_status():
    if not agent_instance:
        return {"status": "starting"}
    
    return {
        "status": "running" if agent_instance.is_running else "stopped",
        "agent_name": agent_instance.settings.agent_name,
        "k3s_connected": agent_instance.telemetry_collector._initialized if agent_instance.telemetry_collector else False,
        "llm_ready": agent_instance.analysis_core.llm_manager is not None if agent_instance.analysis_core else False,
        "version": "1.0.0"
    }

@app.get("/api/v1/topology")
async def get_topology():
    if not agent_instance or not agent_instance.context_engine:
        return {"nodes": [], "edges": []}
    
    graph = agent_instance.context_engine.topology_graph
    nodes = []
    edges = []
    
    for node_id, node in graph.items():
        # Map resource types to colors/icons in frontend
        nodes.append({
            "id": node_id,
            "type": "resourceNode",
            "data": {
                "label": node.name,
                "kind": node.resource_type,
                "namespace": node.namespace,
                "status": node.properties.get("status", "Unknown"),
                "properties": {k: str(v) for k, v in node.properties.items() if k != "relationships"}
            },
            "position": {"x": 0, "y": 0} # Frontend will handle layout
        })
        
        for rel_id in node.relationships:
            edges.append({
                "id": f"e-{node_id}-{rel_id}",
                "source": node_id,
                "target": rel_id,
                "animated": True
            })
            
    return {"nodes": nodes, "edges": edges}

@app.get("/api/v1/incidents")
async def get_incidents():
    if not agent_instance or not agent_instance.context_engine:
        return []
    
    # Convert IncidentRecord to dict and handle datetime
    incidents = []
    for inc in agent_instance.context_engine.incidents:
        inc_dict = {
            "incident_id": inc.incident_id,
            "timestamp": inc.timestamp.isoformat(),
            "symptoms": inc.symptoms,
            "root_cause": inc.root_cause,
            "resolution": inc.resolution,
            "affected_resources": inc.affected_resources,
            "log_snippets": inc.log_snippets,
            "severity": "Warning" # Default or extract from record
        }
        incidents.append(inc_dict)
    
    return sorted(incidents, key=lambda x: x["timestamp"], reverse=True)

@app.get("/api/v1/config")
async def get_config():
    if not agent_instance:
        return {}
    
    s = agent_instance.settings
    return {
        "kubeconfig_path": s.k3s_config_path,
        "llm_provider": s.llm.provider,
        "llm_model": s.llm.model,
        "poll_interval": s.poll_interval,
        "namespace": s.namespace
    }

@app.post("/api/v1/config")
async def update_config(config: ConfigUpdate):
    if not agent_instance:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    s = agent_instance.settings
    logger = logging.getLogger("sentinel.api")
    
    if config.kubeconfig_path:
        logger.info(f"Updating kubeconfig path to: {config.kubeconfig_path}")
        s.k3s_config_path = config.kubeconfig_path
        try:
            await agent_instance.telemetry_collector.initialize()
        except Exception as e:
            logger.error(f"Failed to re-initialize telemetry: {e}")
            raise HTTPException(status_code=400, detail=f"Invalid kubeconfig: {str(e)}")
    
    if config.llm_provider:
        s.llm.provider = config.llm_provider
    
    if config.llm_model:
        s.llm.model = config.llm_model
        
    if config.llm_api_key:
        s.llm.api_key = config.llm_api_key
        if agent_instance.analysis_core:
            await agent_instance.analysis_core.initialize()
            
    if config.poll_interval:
        s.poll_interval = config.poll_interval
            
    return {"status": "success", "message": "Configuration updated successfully"}

# Static files will be served from dist if it exists
if os.path.exists("frontend/dist"):
    app.mount("/", StaticFiles(directory="frontend/dist", html=True), name="static")
