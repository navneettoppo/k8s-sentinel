"""
Telemetry Collector for K3s-Sentinel Agent.

This module collects telemetry data from K3s cluster including:
- Kubernetes events
- Pod logs
- Node metrics
- Cluster resources
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum

from kubernetes import client, config
from kubernetes.client.rest import ApiException


class EventSeverity(Enum):
    """Severity levels for cluster events."""
    NORMAL = "Normal"
    WARNING = "Warning"
    ERROR = "Error"
    CRITICAL = "Critical"


@dataclass
class ClusterEvent:
    """Represents a Kubernetes event with additional context."""
    name: str
    namespace: str
    event_type: str
    reason: str
    message: str
    involved_object_kind: str
    involved_object_name: str
    first_timestamp: datetime
    last_timestamp: datetime
    count: int
    severity: EventSeverity = EventSeverity.NORMAL
    source_component: str = ""
    source_host: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary."""
        return {
            "name": self.name,
            "namespace": self.namespace,
            "event_type": self.event_type,
            "reason": self.reason,
            "message": self.message,
            "involved_object_kind": self.involved_object_kind,
            "involved_object_name": self.involved_object_name,
            "first_timestamp": self.first_timestamp.isoformat(),
            "last_timestamp": self.last_timestamp.isoformat(),
            "count": self.count,
            "severity": self.severity.value,
            "source_component": self.source_component,
            "source_host": self.source_host,
            "metadata": self.metadata
        }


@dataclass
class PodLog:
    """Represents container logs from a pod."""
    pod_name: str
    namespace: str
    container_name: str
    timestamp: datetime
    log_lines: List[str]
    previous_logs: Optional[List[str]] = None
    exit_code: Optional[int] = None


@dataclass
class NodeMetrics:
    """Represents node resource metrics."""
    node_name: str
    timestamp: datetime
    cpu_usage_percent: float
    memory_usage_percent: float
    memory_usage_bytes: int
    memory_limit_bytes: int
    disk_usage_percent: float
    disk_available_bytes: int
    network_rx_bytes: int = 0
    network_tx_bytes: int = 0


class TelemetryCollector:
    """
    Collects telemetry data from K3s cluster.

    Monitors events, logs, and metrics to provide comprehensive
    cluster observability for root cause analysis.
    """

    def __init__(self, settings):
        """Initialize the telemetry collector."""
        self.logger = logging.getLogger(__name__)
        self.settings = settings

        self.core_v1 = None
        self.custom_objects_api = None
        self.events_api = None
        self._initialized = False
        self._event_buffer: List[ClusterEvent] = []

    async def initialize(self):
        """Initialize Kubernetes client connections."""
        try:
            # Try to load in-cluster config first, then local config
            try:
                config.load_incluster_config()
                self.logger.info("Loaded in-cluster Kubernetes configuration")
            except config.ConfigException:
                config.load_kube_config(
                    config_file=self.settings.k3s_config_path,
                    context=self.settings.k3s_context
                )
                self.logger.info("Loaded local Kubernetes configuration")

            self.core_v1 = client.CoreV1Api()
            self.custom_objects_api = client.CustomObjectsApi()
            self.events_api = client.EventsV1Api()

            # Test connection
            self.core_v1.list_namespace(limit=1)
            self._initialized = True
            self.logger.info("Telemetry collector initialized successfully")

        except Exception as e:
            self.logger.error(f"Failed to initialize Kubernetes client: {e}")
            raise

    async def start(self):
        """Start collecting telemetry data."""
        if not self._initialized:
            await self.initialize()

        self.logger.info("Starting telemetry collection...")
        # Start background collection tasks
        asyncio.create_task(self._collect_events_periodically())

    async def stop(self):
        """Stop telemetry collection."""
        self.logger.info("Stopping telemetry collection...")
        self._initialized = False

    async def _collect_events_periodically(self):
        """Periodically collect events from the cluster."""
        while self._initialized:
            try:
                events = await self._fetch_events()
                self._event_buffer.extend(events)

                # Keep only recent events in buffer
                if len(self._event_buffer) > self.settings.event_window_size:
                    self._event_buffer = self._event_buffer[-self.settings.event_window_size:]

            except Exception as e:
                self.logger.error(f"Error collecting events: {e}")

            await asyncio.sleep(self.settings.poll_interval)

    async def get_events(self) -> List[ClusterEvent]:
        """Get recent cluster events."""
        return self._event_buffer.copy()

    async def _fetch_events(self, namespace: str = None) -> List[ClusterEvent]:
        """Fetch events from Kubernetes API."""
        events = []

        try:
            if namespace:
                event_list = self.core_v1.list_namespaced_event(
                    namespace=namespace,
                    field_selector="type=Warning"
                )
            else:
                event_list = self.core_v1.list_event_for_all_namespaces(
                    field_selector="type=Warning"
                )

            for event in event_list.items:
                severity = self._determine_severity(event)
                cluster_event = ClusterEvent(
                    name=event.metadata.name,
                    namespace=event.metadata.namespace,
                    event_type=event.type,
                    reason=event.reason,
                    message=event.message,
                    involved_object_kind=event.involved_object.kind,
                    involved_object_name=event.involved_object.name,
                    first_timestamp=event.first_timestamp or datetime.now(),
                    last_timestamp=event.last_timestamp or datetime.now(),
                    count=event.count or 1,
                    severity=severity,
                    source_component=event.source.component if event.source else "",
                    source_host=event.source.host if event.source else ""
                )
                events.append(cluster_event)

        except ApiException as e:
            self.logger.error(f"Error fetching events: {e}")

        return events

    def _determine_severity(self, event) -> EventSeverity:
        """Determine event severity based on event reason."""
        warning_reasons = {
            "FailedScheduling", "BackOff", "Failed", "Unhealthy",
            "Killing", "FailedCreate", "FailedUpdate", "Evicted"
        }

        critical_reasons = {
            "NodeNotReady", "NodeMemoryPressure", "NodeDiskPressure",
            "SystemOOM", "KernelDeadlock"
        }

        reason = event.reason or ""

        if reason in critical_reasons:
            return EventSeverity.CRITICAL
        elif reason in warning_reasons or event.type == "Warning":
            return EventSeverity.WARNING
        else:
            return EventSeverity.NORMAL

    async def get_pod_logs(self, pod_name: str, namespace: str,
                          container_name: str = None,
                          previous: bool = False) -> PodLog:
        """Fetch logs from a specific pod."""
        try:
            # Get container names if not specified
            if not container_name:
                pod = self.core_v1.read_namespaced_pod(pod_name, namespace)
                container_name = pod.spec.containers[0].name

            logs = self.core_v1.read_namespaced_pod_log(
                name=pod_name,
                namespace=namespace,
                container=container_name,
                tail_lines=self.settings.log_lines_to_fetch,
                previous=previous
            )

            # Get previous logs if container restarted
            previous_logs = None
            exit_code = None
            if previous:
                try:
                    previous_logs = self.core_v1.read_namespaced_pod_log(
                        name=pod_name,
                        namespace=namespace,
                        container=container_name,
                        tail_lines=self.settings.log_lines_to_fetch,
                        previous=True
                    )
                except:
                    pass

            # Get exit code from container status
            try:
                pod = self.core_v1.read_namespaced_pod(pod_name, namespace)
                for container_status in (pod.status.container_statuses or []):
                    if container_status.name == container_name:
                        exit_code = container_status.last_state.terminated.exit_code
                        break
            except:
                pass

            return PodLog(
                pod_name=pod_name,
                namespace=namespace,
                container_name=container_name,
                timestamp=datetime.now(),
                log_lines=logs.split('\n') if logs else [],
                previous_logs=previous_logs.split('\n') if previous_logs else None,
                exit_code=exit_code
            )

        except ApiException as e:
            self.logger.error(f"Error fetching logs for pod {pod_name}: {e}")
            raise

    async def get_node_metrics(self, node_name: str = None) -> List[NodeMetrics]:
        """Fetch node metrics from metrics-server."""
        metrics = []

        try:
            if node_name:
                # Get specific node metrics
                node = self.core_v1.read_node(node_name)
                # Note: In production, integrate with metrics-server API
                # This is a placeholder for the actual implementation
                metric = NodeMetrics(
                    node_name=node_name,
                    timestamp=datetime.now(),
                    cpu_usage_percent=0.0,
                    memory_usage_percent=0.0,
                    memory_usage_bytes=0,
                    memory_limit_bytes=0,
                    disk_usage_percent=0.0,
                    disk_available_bytes=0
                )
                metrics.append(metric)
            else:
                # Get all node metrics
                nodes = self.core_v1.list_node()
                for node in nodes.items:
                    metric = NodeMetrics(
                        node_name=node.metadata.name,
                        timestamp=datetime.now(),
                        cpu_usage_percent=0.0,
                        memory_usage_percent=0.0,
                        memory_usage_bytes=0,
                        memory_limit_bytes=0,
                        disk_usage_percent=0.0,
                        disk_available_bytes=0
                    )
                    metrics.append(metric)

        except ApiException as e:
            self.logger.error(f"Error fetching node metrics: {e}")

        return metrics

    async def get_resource_relationships(self, namespace: str = None) -> Dict[str, Any]:
        """
        Build a dependency graph of cluster resources.

        Returns a dictionary mapping resource relationships:
        Service -> Deployment -> Pod -> PVC -> PV -> Node
        """
        relationships = {
            "services": {},
            "deployments": {},
            "pods": {},
            "pvcs": {},
            "nodes": {}
        }

        try:
            # Get all namespaces or specific namespace
            if namespace:
                namespaces = [namespace]
            else:
                ns_list = self.core_v1.list_namespace()
                namespaces = [ns.metadata.name for ns in ns_list.items]

            for ns in namespaces:
                # Get services
                services = self.core_v1.list_namespaced_service(ns)
                for svc in services.items:
                    relationships["services"][f"{ns}/{svc.metadata.name}"] = {
                        "selector": svc.spec.selector,
                        "type": svc.spec.type,
                        "cluster_ip": svc.spec.cluster_ip,
                        "ports": [p.port for p in (svc.spec.ports or [])]
                    }

                # Get deployments
                try:
                    deployments = self.custom_objects_api.list_namespaced_custom_object(
                        group="apps",
                        version="v1",
                        namespace=ns,
                        plural="deployments"
                    )
                    for dep in deployments.get("items", []):
                        relationships["deployments"][f"{ns}/{dep['metadata']['name']}"] = {
                            "replicas": dep["spec"].get("replicas", 0),
                            "selector": dep["spec"].get("selector", {}),
                            "template": dep["spec"].get("template", {})
                        }
                except:
                    pass

                # Get pods
                pods = self.core_v1.list_namespaced_pod(ns)
                for pod in pods.items:
                    relationships["pods"][f"{ns}/{pod.metadata.name}"] = {
                        "node_name": pod.spec.node_name,
                        "status": pod.status.phase,
                        "host_ip": pod.status.host_ip,
                        "pod_ip": pod.status.pod_ip,
                        "labels": pod.metadata.labels,
                        "volumes": [v.name for v in (pod.spec.volumes or [])]
                    }

                # Get PVCs
                pvcs = self.core_v1.list_namespaced_persistent_volume_claim(ns)
                for pvc in pvcs.items:
                    relationships["pvcs"][f"{ns}/{pvc.metadata.name}"] = {
                        "status": pvc.status.phase,
                        "volume_name": pvc.spec.volume_name,
                        "storage_class": pvc.spec.storage_class_name,
                        "access_modes": pvc.spec.access_modes,
                        "capacity": pvc.status.capacity
                    }

            # Get nodes
            nodes = self.core_v1.list_node()
            for node in nodes.items:
                relationships["nodes"][node.metadata.name] = {
                    "labels": node.metadata.labels,
                    "conditions": [c.type for c in (node.status.conditions or [])],
                    "addresses": [{t: a.address for t, a in zip(
                        [type(a.type) for a in (node.status.addresses or [])],
                        node.status.addresses
                    )}]
                }

        except ApiException as e:
            self.logger.error(f"Error fetching resource relationships: {e}")

        return relationships
