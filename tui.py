"""
Full-Featured Terminal UI (TUI) for K3s-Sentinel.

Provides an interactive terminal interface for K3s cluster management
using the textual framework.
"""

import asyncio
import os
import sys
from datetime import datetime
from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.widgets import (
    Header, Footer, Static, Button, DataTable, Log, Input,
    TabbedContent, Tab, Label, Sparkline
)
from textual.widgets.data_table import Row, Column
from textual import on
from textual.events import Key
from textual.message import Message
from textual.binding import Binding

try:
    from kubernetes import client, config
    from kubernetes.client.rest import ApiException
    KUBERNETES_AVAILABLE = True
except ImportError:
    KUBERNETES_AVAILABLE = False


# Color palette for the TUI
COLORS = {
    "primary": "#27aeef",
    "secondary": "#87bc45",
    "accent": "#ef9b20",
    "error": "#ea5545",
    "warning": "#edbf33",
    "success": "#27ae60",
    "text": "#ffffff",
    "text-dim": "#aaaaaa",
    "surface": "#1a1a2e",
    "surface-light": "#16213e",
}


@dataclass
class ResourceItem:
    """Represents a cluster resource."""
    name: str
    namespace: str
    status: str
    age: str
    extra: Dict[str, str] = None

    def __post_init__(self):
        if self.extra is None:
            self.extra = {}


@dataclass
class ClusterEvent:
    """Represents a cluster event."""
    timestamp: str
    namespace: str
    event_type: str
    reason: str
    message: str
    object: str


class AlertItem:
    """Represents an alert with RCA information."""
    def __init__(self, id: str, severity: str, message: str, resource: str,
                 root_cause: Optional[str] = None, suggested_fix: Optional[str] = None):
        self.id = id
        self.severity = severity
        self.message = message
        self.resource = resource
        self.root_cause = root_cause
        self.suggested_fix = suggested_fix


class HelpOverlay(Container):
    """Help overlay showing all keyboard shortcuts."""

    CSS = """
    HelpOverlay {
        align: center middle;
        background: $surface-darken-3;
        width: 100%;
        height: 100%;
    }

    #help-container {
        width: 70%;
        height: 80%;
        background: $surface;
        border: solid $primary;
        padding: 2;
    }

    #help-title {
        height: 3;
        content-align: center middle;
        text-style: bold;
        color: $primary;
    }

    #help-content {
        height: 1fr;
        overflow-y: scroll;
    }
    """

    BINDINGS = [
        ("escape", "close", "Close"),
        ("q", "close", "Close"),
        ("?", "close", "Close"),
    ]

    def compose(self) -> ComposeResult:
        with Vertical(id="help-container"):
            yield Static("KEYBOARD SHORTCUTS", id="help-title")
            with VerticalScroll(id="help-content"):
                yield Static(self._get_help_text())

    def _get_help_text(self) -> str:
        return """
NAVIGATION
  Tab / Shift+Tab    Cycle between panels
  ↑ / j             Navigate up in list
  ↓ / k             Navigate down in list
  Enter             Select / drill-down
  Esc / q           Back / quit / close

ACTIONS
  d                 Describe selected resource
  l                 View logs
  e                 Exec into container (shell)
  D                 Delete resource
  r                 Restart pod
  s                 Scale deployment

VIEW & FILTER
  f                 Filter resources
  n                 Change namespace
  c                 Switch context
  y                 View resource YAML
  ?                 Show this help
  /                 Fuzzy search
  R                 Refresh data

GLOBAL
  Ctrl+C            Force quit
  1-6               Switch to panel (1:Clusters, 2:Namespaces, 3:Resources, 4:Logs, 5:Events, 6:Alerts)
        """


class ClusterPanel(Vertical):
    """Panel for displaying cluster contexts and information."""

    CSS = """
    ClusterPanel {
        height: 100%;
        padding: 1;
    }

    #cluster-info {
        height: auto;
        padding: 1;
        background: $surface-light;
        border: solid $primary;
        margin-bottom: 1;
    }

    #context-list {
        height: 1fr;
    }
    """

    def compose(self) -> ComposeResult:
        yield Static("CLUSTERS", id="panel-title")
        yield Static(id="cluster-info")
        yield DataTable(id="context-list")

    def on_mount(self) -> None:
        table = self.query_one("#context-list", DataTable)
        table.add_columns("Context", "Cluster", "User", "Active")
        table.focus()


class NamespacePanel(Vertical):
    """Panel for namespace selection."""

    CSS = """
    NamespacePanel {
        height: 100%;
        padding: 1;
    }
    """

    def compose(self) -> ComposeResult:
        yield Static("NAMESPACES", id="panel-title")
        yield DataTable(id="namespace-list")

    def on_mount(self) -> None:
        table = self.query_one("#namespace-list", DataTable)
        table.add_columns("Namespace", "Status", "Age")
        table.focus()


class ResourcePanel(Vertical):
    """Panel for displaying cluster resources (pods, services, etc.)."""

    CSS = """
    ResourcePanel {
        height: 100%;
        padding: 1;
    }

    #resource-tabs {
        height: 3;
    }

    #resource-filter {
        height: 3;
        padding: 1;
    }
    """

    RESOURCE_TYPES = ["pods", "services", "deployments", "nodes", "pvcs", "configmaps", "secrets"]

    def compose(self) -> ComposeResult:
        yield Static("RESOURCES", id="panel-title")
        with Horizontal(id="resource-tabs"):
            for rt in self.RESOURCE_TYPES:
                yield Button(rt.capitalize(), id=f"btn-{rt}", variant="default")
        yield Input(placeholder="Filter resources... (press Enter)", id="resource-filter")
        yield DataTable(id="resource-list")

    def on_mount(self) -> None:
        table = self.query_one("#resource-list", DataTable)
        table.add_columns("Name", "Namespace", "Status", "Age", "Extra")
        table.focus()


class LogsPanel(Vertical):
    """Panel for viewing pod/container logs."""

    CSS = """
    LogsPanel {
        height: 100%;
        padding: 1;
    }

    #log-controls {
        height: 3;
        padding: 1;
    }

    #log-view {
        height: 1fr;
        border: solid $primary;
        background: $surface-darken-1;
    }
    """

    def compose(self) -> ComposeResult:
        yield Static("LOGS", id="panel-title")
        with Horizontal(id="log-controls"):
            yield Input(placeholder="Namespace", id="log-namespace")
            yield Input(placeholder="Pod name", id="log-pod")
            yield Input(placeholder="Container", id="log-container")
            yield Button("Fetch", id="btn-fetch-logs")
            yield Button("Previous", id="btn-prev-logs")
        yield Log(id="log-view")

    def on_mount(self) -> None:
        log = self.query_one("#log-view", Log)
        log.focus()


class EventsPanel(Vertical):
    """Panel for displaying cluster events timeline."""

    CSS = """
    EventsPanel {
        height: 100%;
        padding: 1;
    }
    """

    def compose(self) -> ComposeResult:
        yield Static("EVENTS", id="panel-title")
        yield DataTable(id="events-list")

    def on_mount(self) -> None:
        table = self.query_one("#events-list", DataTable)
        table.add_columns("Time", "Namespace", "Type", "Reason", "Object", "Message")
        table.focus()


class AlertsPanel(Vertical):
    """Panel for displaying alerts with RCA."""

    CSS = """
    AlertsPanel {
        height: 100%;
        padding: 1;
    }
    """

    def compose(self) -> ComposeResult:
        yield Static("ALERTS", id="panel-title")
        yield DataTable(id="alerts-list")

    def on_mount(self) -> None:
        table = self.query_one("#alerts-list", DataTable)
        table.add_columns("ID", "Severity", "Message", "Resource", "Root Cause")
        table.focus()


class DetailPanel(Vertical):
    """Panel for showing resource details, YAML, describe output."""

    CSS = """
    DetailPanel {
        height: 100%;
        padding: 1;
        background: $surface-light;
    }

    #detail-header {
        height: auto;
        padding: 1;
        background: $primary;
    }

    #detail-content {
        height: 1fr;
        overflow-y: auto;
        padding: 1;
    }
    """

    def compose(self) -> ComposeResult:
        yield Static("DETAIL", id="detail-header")
        yield Log(id="detail-content")


class K3sSentinelTUI(App):
    """
    Full-featured Terminal UI for K3s-Sentinel.

    Provides interactive access to K3s cluster resources with
    keyboard navigation and actions.
    """

    CSS = """
    Screen {
        background: $surface;
    }

    #main-container {
        height: 100%;
        layout: horizontal;
    }

    #left-panel {
        width: 30%;
        height: 100%;
        border: solid $primary;
        background: $surface-lighten-1;
    }

    #center-panel {
        width: 40%;
        height: 100%;
        border: solid $secondary;
    }

    #right-panel {
        width: 30%;
        height: 100%;
        border: solid $accent;
    }

    #status-bar {
        height: 3;
        background: $surface-darken-2;
        padding: 0 2;
        content-align: center middle;
    }

    .panel {
        height: 100%;
    }

    #header-title {
        height: 3;
        background: $primary;
        content-align: center middle;
        text-style: bold;
    }

    VerticalScroll {
        height: 1fr;
    }
    """

    TITLE = "K3s-Sentinel TUI"

    BINDINGS = [
        # Navigation
        ("tab", "cycle_panel", "Next Panel"),
        ("shift+tab", "cycle_panel_rev", "Prev Panel"),
        ("escape", "back", "Back"),
        ("q", "quit", "Quit"),

        # Resource actions
        ("d", "describe", "Describe"),
        ("l", "view_logs", "Logs"),
        ("e", "exec_shell", "Exec"),
        ("D", "delete_resource", "Delete"),
        ("r", "restart_pod", "Restart"),
        ("s", "scale_deployment", "Scale"),

        # View controls
        ("f", "filter", "Filter"),
        ("n", "change_namespace", "Namespace"),
        ("c", "switch_context", "Context"),
        ("y", "view_yaml", "YAML"),
        ("?", "show_help", "Help"),
        ("/", "search", "Search"),
        ("R", "refresh", "Refresh"),

        # Panel shortcuts
        ("1", "panel_clusters", "Clusters"),
        ("2", "panel_namespaces", "Namespaces"),
        ("3", "panel_resources", "Resources"),
        ("4", "panel_logs", "Logs"),
        ("5", "panel_events", "Events"),
        ("6", "panel_alerts", "Alerts"),
    ]

    def __init__(
        self,
        kubeconfig_path: Optional[str] = None,
        default_namespace: str = "default",
        refresh_interval: int = 30,
        theme: str = "dark"
    ):
        """Initialize TUI application."""
        super().__init__()
        self.kubeconfig_path = kubeconfig_path
        self.current_namespace = default_namespace
        self.refresh_interval = refresh_interval
        self.theme = theme

        # Kubernetes client
        self.core_v1 = None
        self.apps_v1 = None
        self.networking_v1 = None

        # State
        self.contexts: List[Dict[str, Any]] = []
        self.current_context: Optional[str] = None
        self.namespaces: List[str] = []
        self.resources: Dict[str, List[ResourceItem]] = {}
        self.events: List[ClusterEvent] = []
        self.alerts: List[AlertItem] = []
        self.selected_resource: Optional[ResourceItem] = None

        # Panel state
        self.active_panel = 0
        self.show_help = False
        self.filter_text = ""
        self.detail_view = False

        # Refresh task
        self._refresh_task = None

    def on_mount(self) -> None:
        """Handle app mount."""
        self._initialize_kubernetes()
        self._setup_panels()
        self._start_auto_refresh()

    def _initialize_kubernetes(self) -> None:
        """Initialize Kubernetes client."""
        if not KUBERNETES_AVAILABLE:
            self.notify("Kubernetes client not available", severity="error")
            return

        try:
            if self.kubeconfig_path:
                config.load_kube_config(config_file=self.kubeconfig_path)
            else:
                # Try in-cluster first, then default locations
                try:
                    config.load_incluster_config()
                except config.ConfigException:
                    config.load_kube_config()

            self.core_v1 = client.CoreV1Api()
            self.apps_v1 = client.AppsV1Api()
            self.networking_v1 = client.NetworkingV1Api()

            # Load contexts
            self._load_contexts()

            self.notify("Connected to cluster", severity="information")

        except Exception as e:
            self.notify(f"Failed to connect: {e}", severity="error")

    def _load_contexts(self) -> None:
        """Load available kubeconfig contexts."""
        try:
            contexts, current = config.list_kube_config_contexts(
                config_file=self.kubeconfig_path
            )
            self.contexts = contexts
            self.current_context = current
        except Exception as e:
            self.notify(f"Failed to load contexts: {e}", severity="error")

    def _setup_panels(self) -> None:
        """Setup panel content."""
        self._refresh_data()

    def _start_auto_refresh(self) -> None:
        """Start automatic data refresh."""
        if self._refresh_task:
            self._refresh_task.cancel()

        async def refresh_loop():
            while True:
                await asyncio.sleep(self.refresh_interval)
                await self._async_refresh()

        self._refresh_task = asyncio.create_task(refresh_loop())

    async def _async_refresh(self) -> None:
        """Async refresh data."""
        self._refresh_data()

    def _refresh_data(self) -> None:
        """Refresh all panel data."""
        self._load_namespaces()
        self._load_resources()
        self._load_events()
        self._load_alerts()
        self._update_status_bar()

    def _load_namespaces(self) -> None:
        """Load cluster namespaces."""
        if not self.core_v1:
            return

        try:
            ns_list = self.core_v1.list_namespace()
            self.namespaces = [ns.metadata.name for ns in ns_list.items]
            self._update_namespace_panel()
        except ApiException as e:
            self.notify(f"Failed to load namespaces: {e}", severity="error")

    def _load_resources(self) -> None:
        """Load cluster resources."""
        if not self.core_v1:
            return

        try:
            # Load pods
            pods = self.core_v1.list_pod_for_all_namespaces()
            self.resources["pods"] = [
                ResourceItem(
                    name=pod.metadata.name,
                    namespace=pod.metadata.namespace,
                    status=str(pod.status.phase),
                    age=self._calculate_age(pod.metadata.creation_timestamp),
                    extra={"Node": pod.spec.node_name or "Unscheduled"}
                )
                for pod in pods.items
            ]

            # Load services
            svcs = self.networking_v1.list_service_for_all_namespaces()
            self.resources["services"] = [
                ResourceItem(
                    name=svc.metadata.name,
                    namespace=svc.metadata.namespace,
                    status=str(svc.spec.type),
                    age=self._calculate_age(svc.metadata.creation_timestamp),
                    extra={"ClusterIP": svc.spec.cluster_ip}
                )
                for svc in svcs.items
            ]

            # Load deployments
            try:
                deps = self.apps_v1.list_deployment_for_all_namespaces()
                self.resources["deployments"] = [
                    ResourceItem(
                        name=dep.metadata.name,
                        namespace=dep.metadata.namespace,
                        status=f"{dep.status.ready_replicas or 0}/{dep.status.replicas or 0}",
                        age=self._calculate_age(dep.metadata.creation_timestamp),
                        extra={"Selector": str(dep.spec.selector)}
                    )
                    for dep in deps.items
                ]
            except ApiException:
                pass

            # Load nodes
            nodes = self.core_v1.list_node()
            self.resources["nodes"] = [
                ResourceItem(
                    name=node.metadata.name,
                    namespace="",
                    status=self._get_node_status(node),
                    age=self._calculate_age(node.metadata.creation_timestamp),
                    extra={"Roles": self._get_node_roles(node)}
                )
                for node in nodes.items
            ]

            # Load PVCs
            pvcs = self.core_v1.list_persistent_volume_claim_for_all_namespaces()
            self.resources["pvcs"] = [
                ResourceItem(
                    name=pvc.metadata.name,
                    namespace=pvc.metadata.namespace,
                    status=str(pvc.status.phase),
                    age=self._calculate_age(pvc.metadata.creation_timestamp),
                    extra={"StorageClass": pvc.spec.storage_class_name or ""}
                )
                for pvc in pvcs.items
            ]

            self._update_resource_panel()

        except ApiException as e:
            self.notify(f"Failed to load resources: {e}", severity="error")

    def _load_events(self) -> None:
        """Load cluster events."""
        if not self.core_v1:
            return

        try:
            events = self.core_v1.list_event_for_all_namespaces(limit=100)
            self.events = [
                ClusterEvent(
                    timestamp=self._format_timestamp(event.last_timestamp),
                    namespace=event.metadata.namespace or "default",
                    event_type=event.type or "Normal",
                    reason=event.reason or "",
                    message=event.message or "",
                    object=f"{event.involved_object.kind}/{event.involved_object.name}"
                )
                for event in events.items
            ]
            self._update_events_panel()

        except ApiException as e:
            self.notify(f"Failed to load events: {e}", severity="error")

    def _load_alerts(self) -> None:
        """Load alerts from problem resources."""
        self.alerts = []

        if not self.resources.get("pods"):
            return

        for pod in self.resources["pods"]:
            # Check for problem states
            if pod.status == "Failed":
                self.alerts.append(AlertItem(
                    id=f"alert-{len(self.alerts)}",
                    severity="critical",
                    message=f"Pod {pod.name} is Failed",
                    resource=f"{pod.namespace}/{pod.name}",
                    root_cause="Pod encountered an unrecoverable error",
                    suggested_fix="Check pod events and logs"
                ))

            elif pod.status == "Pending":
                self.alerts.append(AlertItem(
                    id=f"alert-{len(self.alerts)}",
                    severity="warning",
                    message=f"Pod {pod.name} is Pending",
                    resource=f"{pod.namespace}/{pod.name}",
                    root_cause="Pod cannot be scheduled",
                    suggested_fix="Check node resources and affinity rules"
                ))

            elif "CrashLoopBackOff" in pod.status:
                self.alerts.append(AlertItem(
                    id=f"alert-{len(self.alerts)}",
                    severity="error",
                    message=f"Container in {pod.name} is crashing",
                    resource=f"{pod.namespace}/{pod.name}",
                    root_cause="Container repeatedly failing",
                    suggested_fix="Check application logs"
                ))

        self._update_alerts_panel()

    def _get_node_status(self, node) -> str:
        """Get node status string."""
        for condition in (node.status.conditions or []):
            if condition.type == "Ready":
                return "Ready" if condition.status == "True" else "NotReady"
        return "Unknown"

    def _get_node_roles(self, node) -> str:
        """Get node roles/labels."""
        labels = node.metadata.labels or {}
        roles = []
        if labels.get("node-role.kubernetes.io/master"):
            roles.append("master")
        if labels.get("node-role.kubernetes.io/worker"):
            roles.append("worker")
        if labels.get("node.kubernetes.io/example"):
            roles.append("example")
        return ",".join(roles) if roles else "none"

    def _calculate_age(self, timestamp) -> str:
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

    def _format_timestamp(self, timestamp) -> str:
        """Format timestamp for display."""
        if timestamp is None:
            return "Unknown"
        return timestamp.strftime("%H:%M:%S")

    def _update_status_bar(self) -> None:
        """Update status bar with current state."""
        status = self.query_one("#status-bar", Static)
        ctx = self.current_context or "No context"
        ns = self.current_namespace
        status.update(f"Context: {ctx} | Namespace: {ns} | Press ? for help")

    def _update_cluster_panel(self) -> None:
        """Update cluster/context panel."""
        panel = self.query_one("#left-panel #context-list", DataTable)
        panel.clear()

        for ctx in self.contexts:
            is_active = ctx["name"] == self.current_context
            ctx_info = ctx.get("context", {})
            panel.add_row(
                ctx["name"],
                ctx_info.get("cluster", "unknown"),
                ctx_info.get("user", "unknown"),
                " *" if is_active else ""
            )

        # Update cluster info
        info = self.query_one("#left-panel #cluster-info", Static)
        info.update(f"Current: {self.current_context or 'None'}")

    def _update_namespace_panel(self) -> None:
        """Update namespace panel."""
        panel = self.query_one("#namespace-list", DataTable)
        panel.clear()

        try:
            ns_list = self.core_v1.list_namespace()
            for ns in ns_list.items:
                status = "Active"
                age = self._calculate_age(ns.metadata.creation_timestamp)
                panel.add_row(ns.metadata.name, status, age)
        except ApiException:
            pass

    def _update_resource_panel(self) -> None:
        """Update resource panel."""
        panel = self.query_one("#resource-list", DataTable)
        panel.clear()

        resources = self.resources.get("pods", [])
        for res in resources:
            extra_str = " | ".join(f"{k}: {v}" for k, v in res.extra.items())
            panel.add_row(res.name, res.namespace, res.status, res.age, extra_str)

    def _update_events_panel(self) -> None:
        """Update events panel."""
        panel = self.query_one("#events-list", DataTable)
        panel.clear()

        for event in self.events[:50]:  # Limit to 50 events
            panel.add_row(
                event.timestamp,
                event.namespace,
                event.event_type,
                event.reason,
                event.object,
                event.message[:50]
            )

    def _update_alerts_panel(self) -> None:
        """Update alerts panel."""
        panel = self.query_one("#alerts-list", DataTable)
        panel.clear()

        for alert in self.alerts:
            panel.add_row(
                alert.id,
                alert.severity,
                alert.message[:40],
                alert.resource,
                alert.root_cause[:40] if alert.root_cause else ""
            )

    def _update_logs_panel(self, logs: str, is_previous: bool = False) -> None:
        """Update logs view."""
        log_view = self.query_one("#log-view", Log)
        prefix = "[PREVIOUS] " if is_previous else ""
        log_view.write_line(f"{prefix}{logs}")

    def compose(self) -> ComposeResult:
        """Create layout."""
        yield Header()

        with Horizontal(id="main-container"):
            # Left panel - Clusters/Namespaces
            with Vertical(id="left-panel"):
                yield ClusterPanel(id="clusters-panel")
                yield NamespacePanel(id="namespaces-panel")

            # Center panel - Resources
            with Vertical(id="center-panel"):
                yield ResourcePanel(id="resources-panel")

            # Right panel - Details/Alerts
            with Vertical(id="right-panel"):
                yield EventsPanel(id="events-panel")
                yield AlertsPanel(id="alerts-panel")

        yield Static(
            f"Context: {self.current_context or 'None'} | Namespace: {self.current_namespace} | Press ? for help",
            id="status-bar"
        )

        # Help overlay (hidden by default)
        yield HelpOverlay(id="help-overlay")

    def on_key(self, event: Key) -> None:
        """Handle global key events."""
        if self.show_help and event.key not in ["escape", "q", "?"]:
            return

        # Handle number keys for panel switching
        if event.key.isdigit():
            panel_num = int(event.key)
            if 1 <= panel_num <= 6:
                self.action_panel_clusters() if panel_num == 1 else None
                self.action_panel_namespaces() if panel_num == 2 else None
                self.action_panel_resources() if panel_num == 3 else None
                self.action_panel_logs() if panel_num == 4 else None
                self.action_panel_events() if panel_num == 5 else None
                self.action_panel_alerts() if panel_num == 6 else None

    # Actions

    def action_cycle_panel(self) -> None:
        """Cycle to next panel."""
        self.active_panel = (self.active_panel + 1) % 3

    def action_cycle_panel_rev(self) -> None:
        """Cycle to previous panel."""
        self.active_panel = (self.active_panel - 1) % 3

    def action_back(self) -> None:
        """Go back / close detail view."""
        if self.show_help:
            self.show_help = False
            self.query_one("#help-overlay", HelpOverlay).display = False
        elif self.detail_view:
            self.detail_view = False

    def action_quit(self) -> None:
        """Quit application."""
        self.exit()

    def action_show_help(self) -> None:
        """Toggle help overlay."""
        self.show_help = not self.show_help
        help_overlay = self.query_one("#help-overlay", HelpOverlay)
        help_overlay.display = self.show_help

    def action_refresh(self) -> None:
        """Refresh all data."""
        self._refresh_data()
        self.notify("Data refreshed", severity="information")

    def action_describe(self) -> None:
        """Describe selected resource."""
        table = self.query_one("#center-panel #resource-list", DataTable)
        selected = table.cursor_row

        if selected is not None and self.resources.get("pods"):
            if selected < len(self.resources["pods"]):
                pod = self.resources["pods"][selected]
                self._show_pod_describe(pod)

    def _show_pod_describe(self, pod: ResourceItem) -> None:
        """Show detailed pod information."""
        try:
            pod_obj = self.core_v1.read_namespaced_pod(pod.name, pod.namespace)
            output = []
            output.append(f"Name: {pod_obj.metadata.name}")
            output.append(f"Namespace: {pod_obj.metadata.namespace}")
            output.append(f"Priority: {pod_obj.spec.priority}")
            output.append(f"Node: {pod_obj.spec.node_name or 'Unscheduled'}")
            output.append(f"Status: {pod_obj.status.phase}")
            output.append(f"Start Time: {pod_obj.status.start_time}")
            output.append(f"IP: {pod_obj.status.pod_ip}")
            output.append(f"IPs: {pod_obj.status.podIPs}")
            output.append("")

            # Containers
            output.append("Containers:")
            for c in pod_obj.spec.containers:
                output.append(f"  {c.name}: {c.image}")

            # Events
            try:
                events = self.core_v1.list_namespaced_event(pod.namespace)
                pod_events = [e for e in events.items if e.involved_object.name == pod.name]
                if pod_events:
                    output.append("")
                    output.append("Events:")
                    for e in pod_events[:10]:
                        output.append(f"  {e.last_timestamp}: {e.reason} - {e.message}")
            except ApiException:
                pass

            self._show_detail_output("\n".join(output))

        except ApiException as e:
            self.notify(f"Failed to describe pod: {e}", severity="error")

    def _show_detail_output(self, output: str) -> None:
        """Show detail output in right panel."""
        right_panel = self.query_one("#right-panel")
        # Clear and show detail
        for child in right_panel.children:
            child.remove()

        with right_panel:
            yield DetailPanel(id="detail-panel")

        detail = self.query_one("#detail-panel", DetailPanel)
        header = detail.query_one("#detail-header", Static)
        content = detail.query_one("#detail-content", Log)
        header.update("DETAIL")
        content.clear()
        content.write_line(output)

    def action_view_logs(self) -> None:
        """View logs for selected pod."""
        table = self.query_one("#center-panel #resource-list", DataTable)
        selected = table.cursor_row

        if selected is not None and self.resources.get("pods"):
            if selected < len(self.resources["pods"]):
                pod = self.resources["pods"][selected]
                self._fetch_pod_logs(pod)

    def _fetch_pod_logs(self, pod: ResourceItem, previous: bool = False) -> None:
        """Fetch and display pod logs."""
        try:
            log = self.core_v1.read_namespaced_pod_log(
                pod.name,
                pod.namespace,
                tail_lines=100,
                previous=previous
            )

            # Switch to logs panel
            self.action_panel_logs()

            log_view = self.query_one("#log-view", Log)
            log_view.clear()
            log_view.write_line(f"=== Logs for {pod.namespace}/{pod.name} ===")
            log_view.write_line(log or "(no logs)")

        except ApiException as e:
            self.notify(f"Failed to fetch logs: {e}", severity="error")

    def action_exec_shell(self) -> None:
        """Exec into selected pod."""
        self.notify("Exec shell not available in TUI mode", severity="warning")

    def action_delete_resource(self) -> None:
        """Delete selected resource."""
        self.notify("Delete requires confirmation - not implemented in TUI", severity="warning")

    def action_restart_pod(self) -> None:
        """Restart selected pod."""
        table = self.query_one("#center-panel #resource-list", DataTable)
        selected = table.cursor_row

        if selected is not None and self.resources.get("pods"):
            if selected < len(self.resources["pods"]):
                pod = self.resources["pods"][selected]
                try:
                    # Delete pod to trigger restart
                    self.core_v1.delete_namespaced_pod(pod.name, pod.namespace)
                    self.notify(f"Pod {pod.name} deleted (will restart)", severity="information")
                    self._refresh_data()
                except ApiException as e:
                    self.notify(f"Failed to restart pod: {e}", severity="error")

    def action_scale_deployment(self) -> None:
        """Scale selected deployment."""
        self.notify("Scale deployment - specify replicas", severity="warning")

    def action_filter(self) -> None:
        """Filter resources."""
        input_field = self.query_one("#center-panel #resource-filter", Input)
        input_field.focus()

    def action_change_namespace(self) -> None:
        """Change namespace filter."""
        input_ns = Input(placeholder="Enter namespace name")
        self.notify("Namespace selector not yet implemented", severity="information")

    def action_switch_context(self) -> None:
        """Switch kubeconfig context."""
        if not self.contexts:
            self.notify("No contexts available", severity="warning")
            return

        # Just show current context for now
        self.notify(f"Current context: {self.current_context}", severity="information")

    def action_view_yaml(self) -> None:
        """View YAML for selected resource."""
        table = self.query_one("#center-panel #resource-list", DataTable)
        selected = table.cursor_row

        if selected is not None and self.resources.get("pods"):
            if selected < len(self.resources["pods"]):
                pod = self.resources["pods"][selected]
                self._show_pod_yaml(pod)

    def _show_pod_yaml(self, pod: ResourceItem) -> None:
        """Show pod YAML."""
        try:
            import yaml
            pod_obj = self.core_v1.read_namespaced_pod(pod.name, pod.namespace)
            pod_dict = self.core_v1.api_client.sanitize_for_serialization(pod_obj)
            yaml_str = yaml.dump(pod_dict, default_flow_style=False)
            self._show_detail_output(yaml_str)
        except ApiException as e:
            self.notify(f"Failed to get YAML: {e}", severity="error")

    def action_search(self) -> None:
        """Fuzzy search."""
        self.notify("Fuzzy search - type in resource panel", severity="information")

    # Panel switching actions

    def action_panel_clusters(self) -> None:
        """Switch to clusters panel."""
        self.query_one("#left-panel #context-list", DataTable).focus()

    def action_panel_namespaces(self) -> None:
        """Switch to namespaces panel."""
        self.query_one("#namespace-list", DataTable).focus()

    def action_panel_resources(self) -> None:
        """Switch to resources panel."""
        self.query_one("#center-panel #resource-list", DataTable).focus()

    def action_panel_logs(self) -> None:
        """Switch to logs panel."""
        self.query_one("#log-view", Log).focus()

    def action_panel_events(self) -> None:
        """Switch to events panel."""
        self.query_one("#events-list", DataTable).focus()

    def action_panel_alerts(self) -> None:
        """Switch to alerts panel."""
        self.query_one("#alerts-list", DataTable).focus()

    # Event handlers

    @on(DataTable.RowSelected)
    def on_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle row selection in data tables."""
        pass

    @on(Button.Pressed)
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        button_id = event.button.id

        if button_id == "btn-fetch-logs":
            ns_input = self.query_one("#log-namespace", Input).value
            pod_input = self.query_one("#log-pod", Input).value
            container_input = self.query_one("#log-container", Input).value

            if ns_input and pod_input:
                try:
                    log = self.core_v1.read_namespaced_pod_log(
                        pod_input,
                        ns_input,
                        container=container_input or None,
                        tail_lines=100
                    )
                    log_view = self.query_one("#log-view", Log)
                    log_view.clear()
                    log_view.write_line(log or "(no logs)")
                except ApiException as e:
                    self.notify(f"Failed to fetch logs: {e}", severity="error")

        elif button_id == "btn-prev-logs":
            ns_input = self.query_one("#log-namespace", Input).value
            pod_input = self.query_one("#log-pod", Input).value
            container_input = self.query_one("#log-container", Input).value

            if ns_input and pod_input:
                try:
                    log = self.core_v1.read_namespaced_pod_log(
                        pod_input,
                        ns_input,
                        container=container_input or None,
                        tail_lines=100,
                        previous=True
                    )
                    self._update_logs_panel(log, is_previous=True)
                except ApiException as e:
                    self.notify(f"Failed to fetch previous logs: {e}", severity="error")

        elif button_id and button_id.startswith("btn-"):
            resource_type = button_id[4:]  # Remove "btn-" prefix
            if resource_type in self.resources:
                table = self.query_one("#resource-list", DataTable)
                table.clear()
                for res in self.resources[resource_type]:
                    extra_str = " | ".join(f"{k}: {v}" for k, v in res.extra.items())
                    table.add_row(res.name, res.namespace, res.status, res.age, extra_str)

    @on(Input.Submitted)
    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle input submission."""
        input_id = event.input.id

        if input_id == "resource-filter":
            filter_text = event.value.lower()
            self.filter_text = filter_text
            self._apply_filter()

    def _apply_filter(self) -> None:
        """Apply filter to resources."""
        if not self.filter_text:
            return

        table = self.query_one("#resource-list", DataTable)
        # In a real implementation, we would filter the displayed rows
        self.notify(f"Filtering by: {self.filter_text}", severity="information")


def main():
    """Main entry point for TUI."""
    import argparse

    parser = argparse.ArgumentParser(description="K3s-Sentinel TUI")
    parser.add_argument("--kubeconfig", "-k", help="Path to kubeconfig")
    parser.add_argument("--namespace", "-n", default="default", help="Default namespace")
    parser.add_argument("--refresh", "-r", type=int, default=30, help="Refresh interval (seconds)")
    parser.add_argument("--theme", default="dark", choices=["dark", "light"], help="UI theme")

    args = parser.parse_args()

    app = K3sSentinelTUI(
        kubeconfig_path=args.kubeconfig,
        default_namespace=args.namespace,
        refresh_interval=args.refresh,
        theme=args.theme
    )
    app.run()


if __name__ == "__main__":
    main()