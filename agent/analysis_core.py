"""
Analysis Core for K3s-Sentinel Agent.

This module provides the AI-powered root cause analysis:
- Symptom detection and classification
- Causality tracing using dependency graph
- LLM-powered analysis and synthesis
- Root cause identification with confidence scores
"""

import asyncio
import logging
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json

from agent.telemetry_collector import ClusterEvent, EventSeverity
from agent.context_engine import ContextEngine, ResourceNode
from agent.llm_providers import LLMManager


class SymptomType(Enum):
    """Types of symptoms that can be detected."""
    POD_CRASH = "pod_crash"
    POD_EVICTED = "pod_evicted"
    POD_PENDING = "pod_pending"
    SERVICE_UNAVAILABLE = "service_unavailable"
    NODE_NOT_READY = "node_not_ready"
    NODE_RESOURCE_PRESSURE = "node_resource_pressure"
    NETWORK_ISSUE = "network_issue"
    STORAGE_ISSUE = "storage_issue"
    PROBE_FAILURE = "probe_failure"
    CONFIG_ERROR = "config_error"


@dataclass
class AnalysisResult:
    """Result of root cause analysis."""
    symptom_type: SymptomType
    affected_resource: str
    severity: EventSeverity
    root_cause: str
    confidence: float  # 0.0 to 1.0
    evidence: List[str] = field(default_factory=list)
    related_resources: List[str] = field(default_factory=list)
    dependency_path: List[ResourceNode] = field(default_factory=list)
    suggested_fix: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    raw_analysis: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return {
            "symptom_type": self.symptom_type.value,
            "affected_resource": self.affected_resource,
            "severity": self.severity.value,
            "root_cause": self.root_cause,
            "confidence": self.confidence,
            "evidence": self.evidence,
            "related_resources": self.related_resources,
            "suggested_fix": self.suggested_fix,
            "timestamp": self.timestamp.isoformat(),
            "analysis": self.raw_analysis
        }


@dataclass
class SymptomDescriptor:
    """Descriptor for a detected symptom."""
    symptom_type: SymptomType
    resource_kind: str
    resource_name: str
    namespace: str
    status: str
    message: str
    event: Optional[ClusterEvent] = None


class AnalysisCore:
    """
    AI-powered analysis core for root cause determination.

    Uses a combination of:
    - Rule-based symptom detection
    - Dependency graph traversal
    - Vector similarity search (RAG)
    - LLM-powered synthesis
    """

    def __init__(self, settings, context_engine: ContextEngine):
        """Initialize the analysis core."""
        self.logger = logging.getLogger(__name__)
        self.settings = settings
        self.context_engine = context_engine

        # LLM manager for multiple providers
        self.llm_manager: Optional[LLMManager] = None

        # Symptom detection patterns
        self._initialize_patterns()

    def _initialize_patterns(self):
        """Initialize detection patterns for various symptoms."""
        # Status-based patterns
        self.status_patterns = {
            SymptomType.POD_CRASH: ["CrashLoopBackOff", "Error", "Terminated"],
            SymptomType.POD_EVICTED: ["Evicted"],
            SymptomType.POD_PENDING: ["Pending", "FailedScheduling"],
            SymptomType.NODE_NOT_READY: ["NodeNotReady", "NodeStatusUnknown"],
            SymptomType.NODE_RESOURCE_PRESSURE: [
                "DiskPressure", "MemoryPressure", "PIDPressure", "NetworkPressure"
            ],
            SymptomType.PROBE_FAILURE: ["Unhealthy", "LivenessProbeFailed", "ReadinessProbeFailed"],
            SymptomType.CONFIG_ERROR: [
                "CreateContainerConfigError", "ImagePullBackOff", "InvalidImageName"
            ]
        }

        # Event reason patterns
        self.event_reason_patterns = {
            "OOMKilled": SymptomType.POD_CRASH,
            "BackOff": SymptomType.POD_CRASH,
            "FailedScheduling": SymptomType.POD_PENDING,
            "Evicted": SymptomType.POD_EVICTED,
            "NodeNotReady": SymptomType.NODE_NOT_READY,
            "NodeMemoryPressure": SymptomType.NODE_RESOURCE_PRESSURE,
            "NodeDiskPressure": SymptomType.NODE_RESOURCE_PRESSURE,
            "Unhealthy": SymptomType.PROBE_FAILURE,
            "FailedMount": SymptomType.STORAGE_ISSUE
        }

        # Log patterns for common issues
        self.log_patterns = {
            "exit_code_137": r"exit code 137|OOMKilled",
            "exit_code_1": r"exit code 1",
            "connection_refused": r"connection refused|ECONNREFUSED",
            "timeout": r"timeout|timed out",
            "not_found": r"not found|404|No such file",
            "permission_denied": r"permission denied|EACCES",
            "out_of_memory": r"out of memory|OOM"
        }

    async def initialize(self):
        """Initialize the analysis core."""
        self.logger.info("Analysis core initialized")

        # Initialize LLM manager with configured providers
        if self.settings.llm.provider:
            self.llm_manager = LLMManager(self.settings)
            await self.llm_manager.initialize()
            self.logger.info(f"LLM manager initialized with provider: {self.settings.llm.provider}")

    async def _initialize_llm(self):
        """Initialize LLM client (legacy method, now uses manager)."""
        if self.llm_manager:
            await self.llm_manager.initialize()

    async def analyze_event(self, event: ClusterEvent) -> Optional[AnalysisResult]:
        """
        Analyze a cluster event to determine root cause.

        Args:
            event: The cluster event to analyze

        Returns:
            AnalysisResult if root cause identified, None otherwise
        """
        if not event:
            return None

        # Detect symptom type from event
        symptom = self._detect_symptom(event)

        if not symptom:
            return None

        self.logger.info(f"Detected symptom: {symptom.symptom_type.value} for {symptom.resource_name}")

        # Gather context
        context = await self._gather_context(symptom)

        # Search knowledge base
        knowledge_results = self.context_engine.search_knowledge(
            f"{symptom.symptom_type.value} {symptom.message}",
            top_k=3
        )

        # Analyze and determine root cause
        root_cause_analysis = await self._analyze_root_cause(
            symptom, context, knowledge_results
        )

        return root_cause_analysis

    def _detect_symptom(self, event: ClusterEvent) -> Optional[SymptomDescriptor]:
        """Detect the type of symptom from an event."""
        # Map event reason to symptom type
        symptom_type = self.event_reason_patterns.get(event.reason)

        if not symptom_type:
            # Check event message for patterns
            for reason, stype in self.event_reason_patterns.items():
                if reason.lower() in event.message.lower():
                    symptom_type = stype
                    break

        if not symptom_type:
            # Check status for known patterns
            for stype, patterns in self.status_patterns.items():
                for pattern in patterns:
                    if pattern.lower() in event.message.lower():
                        symptom_type = stype
                        break

        if not symptom_type:
            return None

        return SymptomDescriptor(
            symptom_type=symptom_type,
            resource_kind=event.involved_object_kind,
            resource_name=event.involved_object_name,
            namespace=event.namespace,
            status=event.reason,
            message=event.message,
            event=event
        )

    async def _gather_context(self, symptom: SymptomDescriptor) -> Dict[str, Any]:
        """Gather additional context for the symptom."""
        context = {
            "symptom": symptom,
            "logs": [],
            "metrics": {},
            "related_events": [],
            "dependency_path": []
        }

        # Get dependency path from context engine
        resource_id = f"pod/{symptom.namespace}/{symptom.resource_name}"
        path = self.context_engine.get_resource_path(resource_id)
        context["dependency_path"] = path

        # Add related resources
        for node in path:
            context["related_resources"] = [n.id for n in path]

        return context

    async def _analyze_root_cause(
        self,
        symptom: SymptomDescriptor,
        context: Dict[str, Any],
        knowledge_results: List[str]
    ) -> AnalysisResult:
        """
        Analyze and determine the root cause of a symptom.

        Uses knowledge base + context to determine root cause.
        """
        root_cause = ""
        confidence = 0.0
        evidence = []
        suggested_fix = ""

        # Apply rule-based analysis first
        rule_result = self._apply_rules(symptom, context)

        if rule_result:
            root_cause = rule_result["root_cause"]
            confidence = rule_result["confidence"]
            evidence = rule_result["evidence"]
            suggested_fix = rule_result["suggested_fix"]
        else:
            # Use knowledge base + LLM for complex cases
            if knowledge_results or self.llm_client:
                llm_result = await self._llm_analysis(symptom, context, knowledge_results)
                if llm_result:
                    root_cause = llm_result["root_cause"]
                    confidence = llm_result["confidence"]
                    evidence = llm_result["evidence"]
                    suggested_fix = llm_result["suggested_fix"]

        # If still no result, use generic analysis
        if not root_cause:
            root_cause = f"Unknown issue with {symptom.resource_name}"
            confidence = 0.1
            suggested_fix = "Further investigation required"

        # Determine severity
        severity = EventSeverity.WARNING
        if confidence > 0.8 or symptom.symptom_type in [
            SymptomType.NODE_NOT_READY,
            SymptomType.NODE_RESOURCE_PRESSURE
        ]:
            severity = EventSeverity.ERROR

        return AnalysisResult(
            symptom_type=symptom.symptom_type,
            affected_resource=f"{symptom.namespace}/{symptom.resource_name}",
            severity=severity,
            root_cause=root_cause,
            confidence=confidence,
            evidence=evidence,
            related_resources=context.get("related_resources", []),
            dependency_path=context.get("dependency_path", []),
            suggested_fix=suggested_fix,
            raw_analysis={
                "symptom": symptom.__dict__,
                "knowledge_results": knowledge_results,
                "context": {k: str(v) for k, v in context.items()}
            }
        )

    def _apply_rules(
        self,
        symptom: SymptomDescriptor,
        context: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Apply rule-based analysis for common issues."""
        result = None

        # Check exit codes in logs
        log_text = " ".join(context.get("logs", []))

        if symptom.symptom_type == SymptomType.POD_CRASH:
            if "exit code 137" in log_text.lower() or "oomkilled" in log_text.lower():
                result = {
                    "root_cause": "Container terminated due to Out of Memory (OOM)",
                    "confidence": 0.95,
                    "evidence": [
                        "Exit code 137 indicates SIGKILL (128 + 9)",
                        "Container exceeded memory limit or node had memory pressure"
                    ],
                    "suggested_fix": "Increase memory limits in pod spec or optimize application memory usage"
                }

            elif "exit code 1" in log_text.lower():
                result = {
                    "root_cause": "Application error - container exited with code 1",
                    "confidence": 0.7,
                    "evidence": ["Exit code 1 indicates generic application error"],
                    "suggested_fix": "Check application logs for error messages and stack traces"
                }

        elif symptom.symptom_type == SymptomType.POD_EVICTED:
            if "diskpressure" in symptom.message.lower():
                result = {
                    "root_cause": "Pod evicted due to node disk pressure",
                    "confidence": 0.95,
                    "evidence": ["NodeDiskPressure condition detected"],
                    "suggested_fix": "Clean up disk space on node: remove unused images, clear logs, check /var/lib/rancher/k3s"
                }
            elif "memorypressure" in symptom.message.lower():
                result = {
                    "root_cause": "Pod evicted due to node memory pressure",
                    "confidence": 0.95,
                    "evidence": ["NodeMemoryPressure condition detected"],
                    "suggested_fix": "Add more nodes or reduce memory usage on the node"
                }

        elif symptom.symptom_type == SymptomType.CONFIG_ERROR:
            if "configmap" in symptom.message.lower() or "secret" in symptom.message.lower():
                result = {
                    "root_cause": "Missing ConfigMap or Secret referenced by pod",
                    "confidence": 0.9,
                    "evidence": ["CreateContainerConfigError with ConfigMap/Secret reference"],
                    "suggested_fix": "Verify ConfigMap/Secret exists in the namespace"
                }
            elif "image" in symptom.message.lower():
                result = {
                    "root_cause": "Failed to pull container image",
                    "confidence": 0.9,
                    "evidence": ["ImagePullBackOff or similar image error"],
                    "suggested_fix": "Verify image name, tag, and registry credentials"
                }

        elif symptom.symptom_type == SymptomType.NODE_RESOURCE_PRESSURE:
            if "diskpressure" in symptom.message.lower():
                result = {
                    "root_cause": "Node has insufficient disk space",
                    "confidence": 0.95,
                    "evidence": ["NodeDiskPressure condition"],
                    "suggested_fix": "Clean up /var/lib/rancher/k3s, /var/log, and unused container images"
                }
            elif "memorypressure" in symptom.message.lower():
                result = {
                    "root_cause": "Node has insufficient memory",
                    "confidence": 0.95,
                    "evidence": ["NodeMemoryPressure condition"],
                    "suggested_fix": "Add more nodes or reduce memory consumption on the node"
                }

        return result

    async def _llm_analysis(
        self,
        symptom: SymptomDescriptor,
        context: Dict[str, Any],
        knowledge_results: List[str]
    ) -> Optional[Dict[str, Any]]:
        """
        Use LLM to analyze complex cases.

        Uses the LLM manager to call configured providers
        (OpenAI, Anthropic, Gemini, Azure OpenAI, Ollama, etc.)
        """
        if not self.llm_manager:
            return None

        # Build prompt
        prompt = self._build_analysis_prompt(symptom, context, knowledge_results)

        try:
            # Call LLM using the manager (supports multiple providers with fallback)
            response = await self.llm_manager.generate(
                prompt,
                temperature=self.settings.llm.temperature,
                max_tokens=self.settings.llm.max_tokens,
                system_prompt=self.settings.llm.system_prompt
            )

            if response:
                return self._parse_llm_response(response.content)

            return None

        except Exception as e:
            self.logger.error(f"Error in LLM analysis: {e}")

        return None

    def _build_analysis_prompt(
        self,
        symptom: SymptomDescriptor,
        context: Dict[str, Any],
        knowledge_results: List[str]
    ) -> str:
        """Build prompt for LLM analysis."""
        # Build context string
        path_str = "\n".join([
            f"- {node.resource_type}: {node.namespace}/{node.name}"
            for node in context.get("dependency_path", [])
        ])

        knowledge_str = "\n".join([
            f"- {kb}"
            for kb in knowledge_results
        ])

        prompt = f"""Analyze the following Kubernetes issue and determine the root cause:

SYMPTOM:
- Type: {symptom.symptom_type.value}
- Resource: {symptom.resource_kind} {symptom.namespace}/{symptom.resource_name}
- Status: {symptom.status}
- Message: {symptom.message}

DEPENDENCY PATH (from symptom to potential root cause):
{path_str}

RELEVANT KNOWLEDGE:
{knowledge_str}

Based on the above information:
1. Identify the most likely root cause
2. Provide a confidence score (0.0-1.0)
3. List the evidence supporting this conclusion
4. Suggest a fix

Respond in JSON format:
{{
    "root_cause": "...",
    "confidence": 0.0,
    "evidence": ["...", "..."],
    "suggested_fix": "..."
}}"""

        return prompt

    def _parse_llm_response(self, response: str) -> Optional[Dict[str, Any]]:
        """Parse LLM response into structured result."""
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            self.logger.error("Failed to parse LLM response")
            return None

    async def analyze_logs(
        self,
        pod_name: str,
        namespace: str,
        log_lines: List[str]
    ) -> Dict[str, Any]:
        """
        Analyze pod logs for issues.

        Args:
            pod_name: Name of the pod
            namespace: Namespace of the pod
            log_lines: Log lines to analyze

        Returns:
            Analysis results from log analysis
        """
        log_text = "\n".join(log_lines)
        findings = []

        # Check for common patterns
        for pattern_name, pattern in self.log_patterns.items():
            if re.search(pattern, log_text, re.IGNORECASE):
                findings.append({
                    "pattern": pattern_name,
                    "description": f"Found pattern: {pattern_name}"
                })

        return {
            "pod_name": pod_name,
            "namespace": namespace,
            "findings": findings,
            "log_preview": log_lines[-10:] if len(log_lines) > 10 else log_lines
        }
