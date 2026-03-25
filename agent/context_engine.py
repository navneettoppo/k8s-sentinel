"""
Context Engine for K3s-Sentinel Agent.

This module provides the context and memory capabilities:
- Dynamic dependency graph (topology mapping)
- Vector database for RAG (Retrieval-Augmented Generation)
- Historical incident storage
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import json

# Try to import optional dependencies
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

try:
    import chromadb
    from chromadb.config import Settings as ChromaSettings
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False


@dataclass
class ResourceNode:
    """Represents a node in the resource dependency graph."""
    resource_type: str  # service, deployment, pod, pvc, node, etc.
    name: str
    namespace: str
    labels: Dict[str, str] = field(default_factory=dict)
    properties: Dict[str, Any] = field(default_factory=dict)
    relationships: Set[str] = field(default_factory=set)  # IDs of related resources

    @property
    def id(self) -> str:
        """Unique identifier for this resource."""
        return f"{self.resource_type}/{self.namespace}/{self.name}"


@dataclass
class IncidentRecord:
    """Represents a historical incident for learning."""
    incident_id: str
    timestamp: datetime
    symptoms: List[str]
    root_cause: str
    resolution: str
    affected_resources: List[str]
    log_snippets: List[str] = field(default_factory=list)
    metrics_snapshot: Dict[str, Any] = field(default_factory=dict)


class ContextEngine:
    """
    Context Engine for maintaining cluster state and knowledge.

    Provides:
    - Live dependency graph of cluster resources
    - Vector database for storing K3s troubleshooting knowledge
    - Historical incident records for learning
    """

    def __init__(self, settings):
        """Initialize the context engine."""
        self.logger = logging.getLogger(__name__)
        self.settings = settings

        # Resource dependency graph
        self.topology_graph: Dict[str, ResourceNode] = {}

        # Vector database for RAG
        self.vector_db = None
        self.embedding_model = None

        # Historical incidents
        self.incidents: List[IncidentRecord] = []

        # Initialize components
        self._initialize_vector_db()
        self._load_knowledge_base()

    def _initialize_vector_db(self):
        """Initialize vector database for RAG."""
        if not CHROMA_AVAILABLE:
            self.logger.warning("ChromaDB not available, RAG disabled")
            return

        try:
            # Initialize ChromaDB
            db_path = Path(self.settings.vector_db_path)
            db_path.mkdir(parents=True, exist_ok=True)

            self.vector_db = chromadb.PersistentClient(
                path=str(db_path),
                settings=ChromaSettings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )

            # Create or get collection
            self.collection = self.vector_db.get_or_create_collection(
                name="k3s-knowledge",
                metadata={"description": "K3s troubleshooting knowledge base"}
            )

            self.logger.info("Vector database initialized")

            # Initialize embedding model
            if SENTENCE_TRANSFORMERS_AVAILABLE:
                self.embedding_model = SentenceTransformer(
                    self.settings.embedding_model
                )
                self.logger.info(f"Embedding model loaded: {self.settings.embedding_model}")

        except Exception as e:
            self.logger.error(f"Error initializing vector database: {e}")
            self.vector_db = None

    def _load_knowledge_base(self):
        """Load K3s-specific troubleshooting knowledge into vector DB."""
        if not self.vector_db or not self.embedding_model:
            return

        # Check if knowledge base is empty
        if self.collection.count() > 0:
            self.logger.info("Knowledge base already loaded")
            return

        # K3s-specific knowledge base
        knowledge_items = [
            {
                "content": "CrashLoopBackOff: Container restarting repeatedly. Check logs with 'kubectl logs' and 'kubectl describe pod'. Common causes: OOMKilled (exit code 137), application error, liveness probe failure.",
                "category": "pod_status"
            },
            {
                "content": "Evicted: Pod was evicted from node. Check node conditions with 'kubectl describe node'. Common causes: DiskPressure, MemoryPressure, NodeStarvation.",
                "category": "pod_status"
            },
            {
                "content": "CreateContainerConfigError: Container configuration error. Check if ConfigMap or Secret exists with 'kubectl get configmap' and 'kubectl describe pod'. Verify image name is correct.",
                "category": "pod_status"
            },
            {
                "content": "FailedScheduling: Pod cannot be scheduled. Check 'kubectl describe pod' for events. Common causes: insufficient CPU/memory, node taints, PVC not bound.",
                "category": "scheduling"
            },
            {
                "content": "Unhealthy: Readiness or liveness probe failed. Check probe configuration and application status. Verify service endpoints with 'kubectl get endpoints'.",
                "category": "probes"
            },
            {
                "content": "Exit Code 137: Container killed by OOMKilled. Increase memory limits in pod spec. Check node memory pressure with 'kubectl describe node'.",
                "category": "exit_codes"
            },
            {
                "content": "Exit Code 1: General application error. Check application logs for stack traces or error messages.",
                "category": "exit_codes"
            },
            {
                "content": "ImagePullBackOff: Cannot pull container image. Check image name, tag, and registry credentials. Verify network access to registry.",
                "category": "images"
            },
            {
                "content": "K3s Traefik ingress issues: Check Traefik logs with 'kubectl logs -n kube-system -l app=traefik'. Verify Ingress resource has correct backend configuration.",
                "category": "k3s_components"
            },
            {
                "content": "K3s local-path-provisioner: Check PVC status and StorageClass. Verify /var/lib/rancher/k3s/storage exists on nodes.",
                "category": "k3s_components"
            },
            {
                "content": "K3s service load balancer: Check klipper-lb pods in kube-system. Verify Service type is LoadBalancer.",
                "category": "k3s_components"
            },
            {
                "content": "NodeDiskPressure: Node has insufficient disk space. Clean up /var/lib/rancher/k3s, /var/log, and unused images.",
                "category": "node_issues"
            },
            {
                "content": "NodeMemoryPressure: Node has insufficient memory. Check pod memory usage and consider adding more nodes.",
                "category": "node_issues"
            },
            {
                "content": "NodeNotReady: Node is not ready. Check kubelet status on node with 'systemctl status k3s'. Review node events.",
                "category": "node_issues"
            }
        ]

        # Add knowledge to vector store
        for i, item in enumerate(knowledge_items):
            try:
                embedding = self.embedding_model.encode(item["content"])
                self.collection.add(
                    ids=[f"kb_{i}"],
                    embeddings=[embedding.tolist()],
                    documents=[item["content"]],
                    metadatas=[{"category": item["category"]}]
                )
            except Exception as e:
                self.logger.error(f"Error adding knowledge item {i}: {e}")

        self.logger.info(f"Loaded {len(knowledge_items)} knowledge base items")

    async def initialize(self):
        """Initialize the context engine."""
        self.logger.info("Context engine initialized")

    async def update_topology(self, resource_map: Dict[str, Any] = None):
        """
        Update the resource dependency graph.

        Args:
            resource_map: Dictionary of resource relationships from telemetry collector
        """
        if not resource_map:
            return

        # Clear existing graph
        self.topology_graph.clear()

        # Build graph from resource map
        for resource_type, resources in resource_map.items():
            if not resources:
                continue

            for name, properties in resources.items():
                namespace = properties.get("namespace", "default")
                node = ResourceNode(
                    resource_type=resource_type,
                    name=name.split("/")[-1] if "/" in name else name,
                    namespace=namespace,
                    labels=properties.get("labels", {}),
                    properties=properties
                )

                # Add relationships
                if resource_type == "pods":
                    # Link pod to node
                    if properties.get("node_name"):
                        node.relationships.add(f"node/{properties['node_name']}")

                    # Link pod to PVCs
                    for volume in properties.get("volumes", []):
                        node.relationships.add(f"pvc/{volume}")

                elif resource_type == "services":
                    # Link service to pods via selector
                    selector = properties.get("selector", {})
                    # This would need pod info to complete the link

                self.topology_graph[node.id] = node

    def search_knowledge(self, query: str, top_k: int = 3) -> List[str]:
        """
        Search the knowledge base for relevant information.

        Args:
            query: Search query
            top_k: Number of results to return

        Returns:
            List of relevant knowledge items
        """
        if not self.vector_db or not self.embedding_model:
            return []

        try:
            # Encode query
            query_embedding = self.embedding_model.encode(query)

            # Search vector store
            results = self.collection.query(
                query_embeddings=[query_embedding.tolist()],
                n_results=top_k
            )

            # Extract documents
            if results and results.get("documents"):
                return results["documents"][0]

        except Exception as e:
            self.logger.error(f"Error searching knowledge base: {e}")

        return []

    def add_incident(self, incident: IncidentRecord):
        """Add an incident record to history."""
        self.incidents.append(incident)
        self.logger.info(f"Added incident record: {incident.incident_id}")

    def get_related_resources(self, resource_id: str) -> List[ResourceNode]:
        """
        Get all resources related to a given resource.

        Args:
            resource_id: The resource ID to find relationships for

        Returns:
            List of related resource nodes
        """
        if resource_id not in self.topology_graph:
            return []

        node = self.topology_graph[resource_id]
        related = []

        for rel_id in node.relationships:
            if rel_id in self.topology_graph:
                related.append(self.topology_graph[rel_id])

        return related

    async def close(self):
        """Close the context engine and cleanup resources."""
        self.logger.info("Context engine closed")

    def get_resource_path(self, symptom_resource: str) -> List[ResourceNode]:
        """
        Trace the dependency path from a symptom resource to its dependencies.

        This is the core "trace back" functionality that traces from
        effect (symptom) to root cause.

        Args:
            symptom_resource: The resource showing symptoms

        Returns:
            List of resources in dependency order (symptom -> root cause)
        """
        path = []

        if symptom_resource not in self.topology_graph:
            return path

        # Start with the symptom resource
        visited = set()
        current_id = symptom_resource

        while current_id and current_id not in visited:
            if current_id not in self.topology_graph:
                break

            visited.add(current_id)
            node = self.topology_graph[current_id]
            path.append(node)

            # Find the next resource in the dependency chain
            # For a pod: pod -> node or pod -> pvc
            # For a service: service -> deployment -> pod -> node

            next_resource = None

            if node.resource_type == "pod":
                # Check if pod has PVCs
                if node.relationships:
                    for rel in node.relationships:
                        if rel.startswith("pvc/"):
                            next_resource = rel
                            break

                # If no PVC, check node
                if not next_resource:
                    for rel in node.relationships:
                        if rel.startswith("node/"):
                            next_resource = rel
                            break

            elif node.resource_type == "service":
                # Find associated pods
                for res_id, res in self.topology_graph.items():
                    if res.resource_type == "pods":
                        # Check if pod matches service selector
                        # This is simplified; in reality would check labels
                        if res.namespace == node.namespace:
                            next_resource = res_id
                            break

            current_id = next_resource

        return path

    def explain_relationship(self, from_resource: str, to_resource: str) -> str:
        """
        Explain the relationship between two resources.

        Args:
            from_resource: Source resource
            to_resource: Target resource

        Returns:
            Human-readable explanation of the relationship
        """
        if from_resource not in self.topology_graph or to_resource not in self.topology_graph:
            return "No relationship found"

        from_node = self.topology_graph[from_resource]
        to_node = self.topology_graph[to_resource]

        # Determine relationship type
        if from_node.resource_type == "pod" and to_node.resource_type == "node":
            return f"Pod '{from_node.name}' is scheduled on Node '{to_node.name}'"

        if from_node.resource_type == "pod" and "pvc" in to_node.resource_type:
            return f"Pod '{from_node.name}' uses PVC '{to_node.name}'"

        if from_node.resource_type == "service" and to_node.resource_type == "pod":
            return f"Service '{from_node.name}' routes traffic to Pod '{to_node.name}'"

        return f"Resource '{from_node.name}' relates to '{to_node.name}'"
