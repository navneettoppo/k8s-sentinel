"""
K3s-specific utilities and helpers for the Sentinel agent.

Provides K3s-specific functionality including:
- K3s component identification
- K3s-specific resource mapping
- Common K3s troubleshooting helpers
"""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum


class K3sComponent(Enum):
    """K3s system components."""
    TRAEFIK = "traefik"
    KILPER_LB = "klipper-lb"
    LOCAL_PATH_PROVISIONER = "local-path-provisioner"
    COREDNS = "coredns"
    METRICS_SERVER = "metrics-server"
    SVC_LB = "svc-lb"
    K3S_SERVER = "k3s-server"
    K3S_AGENT = "k3s-agent"


@dataclass
class K3sComponentInfo:
    """Information about a K3s component."""
    name: str
    namespace: str
    component_type: K3sComponent
    is_system_component: bool = True
    description: str = ""


class K3sHelper:
    """
    Helper class for K3s-specific operations.
    """

    # Default K3s system namespaces
    SYSTEM_NAMESPACES = [
        "kube-system",
        "kube-public",
        "kube-node-lease"
    ]

    # K3s default components and their typical locations
    DEFAULT_COMPONENTS = {
        "traefik": {
            "namespace": "kube-system",
            "labels": {"app.kubernetes.io/name": "traefik"},
            "description": "K3s default ingress controller"
        },
        "traefik-ingress-ingress": {
            "namespace": "kube-system",
            "labels": {"app.kubernetes.io/name": "traefik-ingress"},
            "description": "Traefik ingress routing"
        },
        "local-path-provisioner": {
            "namespace": "kube-system",
            "labels": {"app.kubernetes.io/name": "local-path-provisioner"},
            "description": "K3s default storage provisioner"
        },
        "local-path-storage": {
            "namespace": "local-path-storage",
            "labels": {"app.kubernetes.io/name": "local-path-storage"},
            "description": "Local storage operator"
        },
        "coredns": {
            "namespace": "kube-system",
            "labels": {"k8s-app": "kube-dns"},
            "description": "K3s DNS service"
        },
        "metrics-server": {
            "namespace": "kube-system",
            "labels": {"k8s-app": "metrics-server"},
            "description": "K3s metrics aggregation"
        },
        "svclb-traefik": {
            "namespace": "kube-system",
            "labels": {"app.kubernetes.io/name": "svclb-traefik"},
            "description": "Load balancer for Traefik"
        }
    }

    def __init__(self):
        """Initialize K3s helper."""
        self.logger = logging.getLogger(__name__)

    @staticmethod
    def is_k3s_system_namespace(namespace: str) -> bool:
        """Check if namespace is a K3s system namespace."""
        return namespace in K3sHelper.SYSTEM_NAMESPACES

    @staticmethod
    def is_k3s_component(name: str, labels: Dict[str, str]) -> bool:
        """
        Check if a resource is a K3s system component.

        Args:
            name: Resource name
            labels: Resource labels

        Returns:
            True if resource is a K3s component
        """
        # Check against known components
        for component, info in K3sHelper.DEFAULT_COMPONENTS.items():
            if component in name.lower():
                return True

            # Check labels
            for key, value in info["labels"].items():
                if labels.get(key) == value:
                    return True

        return False

    def identify_component_type(
        self,
        name: str,
        namespace: str,
        labels: Dict[str, str]
    ) -> Optional[K3sComponent]:
        """
        Identify the type of K3s component.

        Args:
            name: Component name
            namespace: Component namespace
            labels: Component labels

        Returns:
            K3sComponent type or None
        """
        name_lower = name.lower()
        labels_str = str(labels).lower()

        if "traefik" in name_lower or "ingress" in labels_str:
            return K3sComponent.TRAEFIK

        if "klipper" in name_lower or "svclb" in name_lower:
            return K3sComponent.KILPER_LB

        if "local-path" in name_lower:
            return K3sComponent.LOCAL_PATH_PROVISIONER

        if "coredns" in name_lower or "dns" in name_lower:
            return K3sComponent.COREDNS

        if "metrics" in name_lower:
            return K3sComponent.METRICS_SERVER

        if "svc-lb" in name_lower:
            return K3sComponent.SVC_LB

        return None

    @staticmethod
    def get_default_storage_path() -> str:
        """
        Get the default K3s storage path.

        Returns:
            Default storage path on K3s nodes
        """
        return "/var/lib/rancher/k3s/storage"

    @staticmethod
    def get_k3s_data_dir() -> str:
        """
        Get the K3s data directory.

        Returns:
            K3s data directory path
        """
        return "/var/lib/rancher/k3s"

    @staticmethod
    def get_k3s_manifests_dir() -> str:
        """
        Get the K3s manifests directory.

        Returns:
            K3s manifests directory path
        """
        return "/var/lib/rancher/k3s/server/manifests"

    @staticmethod
    def get_containerd_socket() -> str:
        """
        Get the containerd socket path.

        Returns:
            Path to containerd socket
        """
        return "/run/k3s/containerd/containerd.sock"

    @staticmethod
    def get_k3s_version() -> str:
        """
        Get K3s version from the cluster.

        Returns:
            K3s version string
        """
        # Would query kubectl or k3s --version
        return "unknown"

    @staticmethod
    def get_kubeconfig_path() -> str:
        """
        Get default kubeconfig path for K3s.

        Returns:
            Path to kubeconfig
        """
        return "/etc/rancher/k3s/k3s.yaml"

    def analyze_traefik_issue(
        self,
        pod_logs: List[str],
        service_endpoints: List[str]
    ) -> Dict[str, Any]:
        """
        Analyze Traefik ingress issues.

        Args:
            pod_logs: Traefik pod logs
            service_endpoints: Available service endpoints

        Returns:
            Analysis results
        """
        issues = []
        recommendations = []

        log_text = "\n".join(pod_logs)

        # Check for backend connection issues
        if "connection refused" in log_text.lower():
            issues.append("Traefik cannot connect to backend service")
            recommendations.append("Verify backend service is running and has endpoints")

        # Check for routing issues
        if "404" in log_text or "route not found" in log_text.lower():
            issues.append("No matching route found")
            recommendations.append("Check Ingress resource configuration")

        # Check for certificate issues
        if "certificate" in log_text.lower():
            issues.append("TLS certificate issue")
            recommendations.append("Verify TLS certificate is valid and properly configured")

        # Check for backend health
        if not service_endpoints:
            issues.append("No healthy backend endpoints")
            recommendations.append("Check backend service and pod status")

        return {
            "component": "traefik",
            "issues_found": issues,
            "recommendations": recommendations,
            "requires_attention": len(issues) > 0
        }

    def analyze_storage_issue(
        self,
        pvc_status: str,
        node_conditions: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze storage issues related to local-path-provisioner.

        Args:
            pvc_status: PVC status
            node_conditions: Node conditions

        Returns:
            Analysis results
        """
        issues = []
        recommendations = []

        # Check PVC status
        if pvc_status == "Pending":
            issues.append("PVC is pending")
            recommendations.append("Check if local-path-provisioner is running")

        elif pvc_status == "Lost":
            issues.append("PVC volume is lost")
            recommendations.append("Check node health and storage path")

        # Check node conditions
        if node_conditions.get("DiskPressure"):
            issues.append("Node has disk pressure")
            recommendations.append("Clean up disk space on affected node")

        return {
            "component": "local-path-provisioner",
            "issues_found": issues,
            "recommendations": recommendations,
            "requires_attention": len(issues) > 0
        }

    def get_k3s_health_status(self) -> Dict[str, Any]:
        """
        Get overall K3s cluster health status.

        Returns:
            Health status information
        """
        # Placeholder - would integrate with actual K3s health checks
        return {
            "cluster_healthy": True,
            "components": {},
            "warnings": [],
            "critical_issues": []
        }


# Singleton instance
k3s_helper = K3sHelper()
