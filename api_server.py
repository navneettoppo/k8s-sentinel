"""
K3s-Sentinel API Server

REST API server for the K3s-Sentinel dashboard.
Provides endpoints for cluster management, telemetry, and configuration.
"""

import os
import asyncio
import logging
import yaml
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from kubernetes import client, config
from kubernetes.client.rest import ApiException

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get the directory where this script is located
BASE_DIR = Path(__file__).parent.absolute()
DASHBOARD_DIST_DIR = BASE_DIR / "dashboard" / "dist"

# FastAPI app
app = FastAPI(
    title="K3s-Sentinel API",
    description="API for K3s Cluster Root Cause Analysis",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for dashboard (if exists)
if DASHBOARD_DIST_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(DASHBOARD_DIST_DIR)), name="static")
    logger.info(f"Serving static files from {DASHBOARD_DIST_DIR}")

# Global state
kubeconfig_path: Optional[str] = None
kubeconfig_valid: bool = False


# Pydantic Models
class KubeconfigValidateRequest(BaseModel):
    kubeconfig_path: str = Field(..., description="Path to kubeconfig file")


class KubeconfigValidateResponse(BaseModel):
    valid: bool
    message: str
    cluster_name: Optional[str] = None
    cluster_version: Optional[str] = None


class ClusterInfo(BaseModel):
    name: str
    version: str
    nodes: int
    pods: int
    services: int
    namespaces: int


class NodeInfo(BaseModel):
    name: str
    status: str
    cpu: float
    memory: float
    disk: float
    network_rx: float
    network_tx: float
    age: str


class PodInfo(BaseModel):
    name: str
    namespace: str
    status: str
    restarts: int
    age: str
    node: str
    ip: str
    containers: int


class ServiceInfo(BaseModel):
    name: str
    namespace: str
    type: str
    cluster_ip: str
    ports: List[str]
    selector: Dict[str, str]


class AlertInfo(BaseModel):
    id: str
    type: str
    severity: str
    message: str
    resource: str
    timestamp: str
    root_cause: Optional[str] = None
    suggested_fix: Optional[str] = None
    confidence: Optional[float] = None


class LLMConfig(BaseModel):
    provider: str
    api_key: Optional[str] = None
    model: str
    temperature: float = 0.7
    max_tokens: int = 2000


class AlertChannelConfig(BaseModel):
    slack_enabled: bool = False
    slack_webhook_url: Optional[str] = None
    teams_enabled: bool = False
    teams_webhook_url: Optional[str] = None
    email_enabled: bool = False
    telegram_enabled: bool = False
    grafana_enabled: bool = False
    prometheus_enabled: bool = False
    pagerduty_enabled: bool = False


# Helper functions
def load_kubeconfig(path: str) -> bool:
    """Load and validate kubeconfig from path."""
    global kubeconfig_path, kubeconfig_valid

    try:
        # Expand path
        expanded_path = os.path.expanduser(os.path.expandvars(path))

        if not os.path.exists(expanded_path):
            logger.error(f"Kubeconfig file not found: {expanded_path}")
            kubeconfig_valid = False
            return False

        # Try to load the config
        config.load_kube_config(config_file=expanded_path)
        kubeconfig_path = expanded_path
        kubeconfig_valid = True
        logger.info(f"Successfully loaded kubeconfig from: {expanded_path}")
        return True

    except Exception as e:
        logger.error(f"Failed to load kubeconfig: {e}")
        kubeconfig_valid = False
        return False


def get_k8s_client() -> client.CoreV1Api:
    """Get Kubernetes client with current config."""
    if not kubeconfig_valid or kubeconfig_path is None:
        raise HTTPException(status_code=401, detail="Not connected to cluster")

    load_kubeconfig(kubeconfig_path)
    return client.CoreV1Api()


# API Endpoints

@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "ok", "service": "K3s-Sentinel API"}


@app.get("/api/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "cluster_connected": kubeconfig_valid
    }


# Kubeconfig Endpoints

@app.post("/api/cluster/validate", response_model=KubeconfigValidateResponse)
async def validate_kubeconfig(request: KubeconfigValidateRequest):
    """Validate kubeconfig file and return cluster info."""
    expanded_path = os.path.expanduser(os.path.expandvars(request.kubeconfig_path))

    if not os.path.exists(expanded_path):
        return KubeconfigValidateResponse(
            valid=False,
            message=f"File not found: {expanded_path}"
        )

    try:
        # Try to load the config
        config.load_kube_config(config_file=expanded_path)

        # Get cluster info
        v1 = client.CoreV1Api()
        v1Api = client.VersionApi()

        # Get cluster name from context
        contexts, current_context = config.list_kube_config_contexts(config_file=expanded_path)
        context = next((c for c in contexts if c['name'] == current_context), None)
        cluster_name = context.get('context', {}).get('cluster', 'unknown') if context else 'unknown'

        # Get server version
        version_info = v1Api.get_code()

        return KubeconfigValidateResponse(
            valid=True,
            message="Kubeconfig is valid",
            cluster_name=cluster_name,
            cluster_version=f"v{version_info.git_version}"
        )

    except ApiException as e:
        return KubeconfigValidateResponse(
            valid=False,
            message=f"Kubernetes API error: {str(e)}"
        )
    except Exception as e:
        return KubeconfigValidateResponse(
            valid=False,
            message=f"Failed to validate: {str(e)}"
        )


@app.post("/api/cluster/connect")
async def connect_cluster(request: KubeconfigValidateRequest):
    """Connect to cluster using kubeconfig."""
    expanded_path = os.path.expanduser(os.path.expandvars(request.kubeconfig_path))

    if not os.path.exists(expanded_path):
        raise HTTPException(status_code=404, detail="Kubeconfig file not found")

    try:
        config.load_kube_config(config_file=expanded_path)

        # Verify connection
        v1 = client.CoreV1Api()
        v1.pod_namespace_list()

        return {
            "status": "connected",
            "kubeconfig_path": expanded_path
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/cluster/disconnect")
async def disconnect_cluster():
    """Disconnect from cluster."""
    global kubeconfig_valid, kubeconfig_path
    kubeconfig_valid = False
    kubeconfig_path = None
    return {"status": "disconnected"}


@app.get("/api/cluster/info", response_model=ClusterInfo)
async def get_cluster_info():
    """Get cluster information."""
    try:
        v1 = get_k8s_client()
        apps_v1 = client.AppsV1Api()
        networking_v1 = client.NetworkingV1Api()

        # Count resources
        nodes = v1.list_node()
        all_pods = v1.list_pod_for_all_namespaces()
        services = networking_v1.list_service_for_all_namespaces(watch=False)
        namespaces = v1.list_namespace()

        # Count deployments
        deployments = apps_v1.list_deployment_for_all_namespaces()

        # Get cluster version
        version_api = client.VersionApi()
        version = version_api.get_code()

        return ClusterInfo(
            name="k3s-cluster",
            version=f"v{version.git_version}",
            nodes=len(nodes.items),
            pods=len(all_pods.items),
            services=len(services.items),
            namespaces=len(namespaces.items)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/cluster/nodes", response_model=List[NodeInfo])
async def get_nodes():
    """Get all nodes with metrics."""
    try:
        v1 = get_k8s_client()
        nodes = v1.list_node()

        result = []
        for node in nodes.items:
            # Get node metrics from conditions
            conditions = {c.type: c.status for c in node.status.conditions}
            ready = conditions.get('Ready', 'Unknown')

            # Calculate approximate resource usage (mock for demo)
            cpu = node.status.usage.get('cpu', client.V1Quantity(string_value="0"))
            memory = node.status.usage.get('memory', client.V1Quantity(string_value="0"))

            result.append(NodeInfo(
                name=node.metadata.name,
                status="Ready" if ready == "True" else "NotReady",
                cpu=50.0,  # Mock - would need metrics-server for real data
                memory=60.0,
                disk=40.0,
                network_rx=1000.0,
                network_tx=500.0,
                age=_calculate_age(node.metadata.creation_timestamp)
            ))

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/cluster/pods", response_model=List[PodInfo])
async def get_pods(namespace: Optional[str] = None):
    """Get all pods."""
    try:
        v1 = get_k8s_client()

        if namespace:
            pods = v1.list_namespaced_pod(namespace)
        else:
            pods = v1.list_pod_for_all_namespaces()

        result = []
        for pod in pods.items:
            container_count = len(pod.spec.containers)
            restart_count = sum(cs.restart_count for cs in pod.status.container_statuses or [])

            result.append(PodInfo(
                name=pod.metadata.name,
                namespace=pod.metadata.namespace,
                status=pod.status.phase,
                restarts=restart_count,
                age=_calculate_age(pod.metadata.creation_timestamp),
                node=pod.spec.node_name or "Unscheduled",
                ip=pod.status.pod_ip or "Pending",
                containers=container_count
            ))

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/cluster/services", response_model=List[ServiceInfo])
async def get_services(namespace: Optional[str] = None):
    """Get all services."""
    try:
        networking_v1 = client.NetworkingV1Api()

        if namespace:
            services = networking_v1.list_namespaced_service(namespace)
        else:
            services = networking_v1.list_service_for_all_namespaces()

        result = []
        for svc in services.items:
            ports = [str(p.port) + "/" + p.protocol for p in svc.spec.ports]

            result.append(ServiceInfo(
                name=svc.metadata.name,
                namespace=svc.metadata.namespace,
                type=svc.spec.type,
                cluster_ip=svc.spec.cluster_ip,
                ports=ports,
                selector=svc.spec.selector or {}
            ))

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/alerts", response_model=List[AlertInfo])
async def get_alerts():
    """Get recent alerts with root cause analysis."""
    # This would integrate with the analysis core
    # For now, return mock data based on cluster state

    try:
        v1 = get_k8s_client()
        pods = v1.list_pod_for_all_namespaces()

        alerts = []
        alert_id = 1

        for pod in pods.items:
            if pod.status.phase == "Failed" or pod.status.phase == "Unknown":
                alerts.append(AlertInfo(
                    id=f"alert-{alert_id}",
                    type="pod_failed",
                    severity="critical",
                    message=f"Pod {pod.metadata.name} is in {pod.status.phase} state",
                    resource=f"{pod.metadata.namespace}/{pod.metadata.name}",
                    timestamp=datetime.now().isoformat(),
                    root_cause="Pod encountered an unrecoverable error",
                    suggested_fix="Check pod logs and events for more details",
                    confidence=0.95
                ))
                alert_id += 1

            elif pod.status.phase == "Pending":
                alerts.append(AlertInfo(
                    id=f"alert-{alert_id}",
                    type="pod_pending",
                    severity="warning",
                    message=f"Pod {pod.metadata.name} has been pending for extended time",
                    resource=f"{pod.metadata.namespace}/{pod.metadata.name}",
                    timestamp=datetime.now().isoformat(),
                    root_cause="Insufficient cluster resources or scheduling constraints not met",
                    suggested_fix="Check node resources and pod affinity rules",
                    confidence=0.80
                ))
                alert_id += 1

            # Check for CrashLoopBackOff
            if pod.status.container_statuses:
                for cs in pod.status.container_statuses:
                    if cs.state and cs.state.waiting and cs.state.waiting.reason == "CrashLoopBackOff":
                        alerts.append(AlertInfo(
                            id=f"alert-{alert_id}",
                            type="pod_crash",
                            severity="error",
                            message=f"Container {cs.name} in pod {pod.metadata.name} is crashing",
                            resource=f"{pod.metadata.namespace}/{pod.metadata.name}",
                            timestamp=datetime.now().isoformat(),
                            root_cause=cs.state.waiting.message or "Container repeatedly failing",
                            suggested_fix="Check application logs for crash details",
                            confidence=0.90
                        ))
                        alert_id += 1

        return alerts[:20]  # Return top 20 alerts
    except Exception as e:
        # Return empty list if we can't connect
        return []


def _calculate_age(timestamp) -> str:
    """Calculate age string from timestamp."""
    if timestamp is None:
        return "Unknown"

    delta = datetime.now() - timestamp.replace(tzinfo=None)
    seconds = delta.total_seconds()

    if seconds < 60:
        return f"{int(seconds)}s"
    elif seconds < 3600:
        return f"{int(seconds / 60)}m"
    elif seconds < 86400:
        return f"{int(seconds / 3600)}h"
    else:
        return f"{int(seconds / 86400)}d"


# Serve frontend index.html for non-API routes (SPA support)
@app.get("/{full_path:path}")
async def serve_frontend(full_path: str):
    """Serve the frontend index.html for any non-API routes (SPA support)."""
    # Skip API routes
    if full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="API endpoint not found")

    # Serve index.html for SPA routes
    index_path = DASHBOARD_DIST_DIR / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))

    raise HTTPException(status_code=404, detail="Page not found")


# Start server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
