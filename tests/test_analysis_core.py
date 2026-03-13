"""
Tests for K3s-Sentinel Agent components.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from agent.telemetry_collector import (
    TelemetryCollector,
    ClusterEvent,
    EventSeverity
)
from agent.context_engine import ContextEngine, ResourceNode
from agent.analysis_core import (
    AnalysisCore,
    SymptomType,
    SymptomDescriptor,
    AnalysisResult
)
from config.settings import Settings


class TestTelemetryCollector:
    """Test cases for TelemetryCollector."""

    @pytest.fixture
    def settings(self):
        """Create test settings."""
        return Settings()

    @pytest.fixture
    def collector(self, settings):
        """Create telemetry collector instance."""
        return TelemetryCollector(settings)

    def test_event_severity_determination(self, collector):
        """Test event severity determination."""
        # Test warning severity
        mock_event = Mock()
        mock_event.type = "Warning"
        mock_event.reason = "BackOff"

        severity = collector._determine_severity(mock_event)
        assert severity == EventSeverity.WARNING

    def test_cluster_event_to_dict(self):
        """Test ClusterEvent serialization."""
        event = ClusterEvent(
            name="test-event",
            namespace="default",
            event_type="Warning",
            reason="BackOff",
            message="Back-off restarting failed container",
            involved_object_kind="Pod",
            involved_object_name="test-pod",
            first_timestamp=datetime.now(),
            last_timestamp=datetime.now(),
            count=1,
            severity=EventSeverity.WARNING
        )

        event_dict = event.to_dict()
        assert event_dict["name"] == "test-event"
        assert event_dict["namespace"] == "default"
        assert event_dict["severity"] == "Warning"


class TestContextEngine:
    """Test cases for ContextEngine."""

    @pytest.fixture
    def settings(self):
        """Create test settings."""
        return Settings(vector_db_path="/tmp/test_vector_db")

    @pytest.fixture
    def context_engine(self, settings):
        """Create context engine instance."""
        return ContextEngine(settings)

    @pytest.mark.asyncio
    async def test_initialize(self, context_engine):
        """Test context engine initialization."""
        await context_engine.initialize()
        assert context_engine is not None

    def test_resource_node_creation(self):
        """Test ResourceNode creation."""
        node = ResourceNode(
            resource_type="pod",
            name="test-pod",
            namespace="default",
            labels={"app": "test"},
            properties={"status": "Running"}
        )

        assert node.id == "pod/default/test-pod"
        assert node.resource_type == "pod"
        assert node.labels["app"] == "test"

    def test_get_related_resources(self, context_engine):
        """Test getting related resources."""
        # Create test nodes
        pod_node = ResourceNode(
            resource_type="pod",
            name="test-pod",
            namespace="default"
        )
        pod_node.relationships.add("node/node-1")

        node_node = ResourceNode(
            resource_type="node",
            name="node-1",
            namespace=""
        )

        context_engine.topology_graph[pod_node.id] = pod_node
        context_engine.topology_graph[node_node.id] = node_node

        related = context_engine.get_related_resources(pod_node.id)
        assert len(related) == 1
        assert related[0].name == "node-1"

    def test_explain_relationship(self, context_engine):
        """Test relationship explanation."""
        # Create test nodes
        pod_node = ResourceNode(
            resource_type="pod",
            name="test-pod",
            namespace="default"
        )
        pod_node.relationships.add("node/node-1")

        node_node = ResourceNode(
            resource_type="node",
            name="node-1",
            namespace=""
        )

        context_engine.topology_graph[pod_node.id] = pod_node
        context_engine.topology_graph[node_node.id] = node_node

        explanation = context_engine.explain_relationship(
            pod_node.id,
            node_node.id
        )
        assert "scheduled on" in explanation


class TestAnalysisCore:
    """Test cases for AnalysisCore."""

    @pytest.fixture
    def settings(self):
        """Create test settings."""
        return Settings()

    @pytest.fixture
    def mock_context_engine(self):
        """Create mock context engine."""
        mock = Mock(spec=ContextEngine)
        mock.search_knowledge = Mock(return_value=[])
        mock.get_resource_path = Mock(return_value=[])
        return mock

    @pytest.fixture
    def analysis_core(self, settings, mock_context_engine):
        """Create analysis core instance."""
        return AnalysisCore(settings, mock_context_engine)

    def test_symptom_type_detection(self, analysis_core):
        """Test symptom type detection from event reason."""
        # Test OOMKilled detection
        event = Mock()
        event.reason = "OOMKilled"
        event.message = "Container killed due to OOM"

        symptom = analysis_core._detect_symptom(event)
        assert symptom is not None
        assert symptom.symptom_type == SymptomType.POD_CRASH

    def test_failed_scheduling_detection(self, analysis_core):
        """Test FailedScheduling detection."""
        event = Mock()
        event.reason = "FailedScheduling"
        event.message = "0/3 nodes are available"

        symptom = analysis_core._detect_symptom(event)
        assert symptom is not None
        assert symptom.symptom_type == SymptomType.POD_PENDING

    def test_rule_based_analysis_crash(self, analysis_core):
        """Test rule-based analysis for pod crash."""
        symptom = SymptomDescriptor(
            symptom_type=SymptomType.POD_CRASH,
            resource_kind="Pod",
            resource_name="test-pod",
            namespace="default",
            status="CrashLoopBackOff",
            message="Container crashed with exit code 137"
        )

        context = {"logs": ["exit code 137", "OOMKilled"]}

        result = analysis_core._apply_rules(symptom, context)
        assert result is not None
        assert "OOM" in result["root_cause"]
        assert result["confidence"] > 0.9

    def test_rule_based_analysis_eviction(self, analysis_core):
        """Test rule-based analysis for eviction."""
        symptom = SymptomDescriptor(
            symptom_type=SymptomType.POD_EVICTED,
            resource_kind="Pod",
            resource_name="test-pod",
            namespace="default",
            status="Evicted",
            message="Pod evicted due to disk pressure"
        )

        context = {"logs": []}

        result = analysis_core._apply_rules(symptom, context)
        assert result is not None
        assert "disk pressure" in result["root_cause"].lower()
        assert result["confidence"] > 0.9


class TestIntegration:
    """Integration tests for the complete flow."""

    @pytest.mark.asyncio
    async def test_full_analysis_flow(self):
        """Test complete analysis flow."""
        settings = Settings()
        mock_context = Mock(spec=ContextEngine)
        mock_context.search_knowledge = Mock(return_value=[
            "CrashLoopBackOff: Container restarting. Check OOM.",
        ])
        mock_context.get_resource_path = Mock(return_value=[])

        # Create mock event
        mock_event = Mock(spec=ClusterEvent)
        mock_event.name = "test-event"
        mock_event.namespace = "default"
        mock_event.event_type = "Warning"
        mock_event.reason = "OOMKilled"
        mock_event.message = "Container killed due to OOM"
        mock_event.involved_object_kind = "Pod"
        mock_event.involved_object_name = "test-pod"
        mock_event.first_timestamp = datetime.now()
        mock_event.last_timestamp = datetime.now()
        mock_event.count = 1

        # Run analysis
        analysis_core = AnalysisCore(settings, mock_context)
        symptom = analysis_core._detect_symptom(mock_event)

        assert symptom is not None
        assert symptom.symptom_type == SymptomType.POD_CRASH


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
