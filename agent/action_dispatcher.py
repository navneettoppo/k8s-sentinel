"""
Action Dispatcher for K3s-Sentinel Agent.

This module handles actions based on analysis results:
- Alert notifications (Slack, Email, Webhook)
- Custom Resource updates
- Remediation suggestions
- Incident recording
"""

import asyncio
import logging
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import aiohttp
import yaml

from agent.analysis_core import AnalysisResult


class AlertPriority(Enum):
    """Alert priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Alert:
    """Represents an alert to be sent."""
    title: str
    description: str
    priority: AlertPriority
    affected_resource: str
    root_cause: str
    confidence: float
    suggested_fix: str
    evidence: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert alert to dictionary."""
        return {
            "title": self.title,
            "description": self.description,
            "priority": self.priority.value,
            "affected_resource": self.affected_resource,
            "root_cause": self.root_cause,
            "confidence": self.confidence,
            "suggested_fix": self.suggested_fix,
            "evidence": self.evidence,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }


class ActionDispatcher:
    """
    Dispatcher for handling analysis results and taking actions.

    Supports:
    - Webhook notifications
    - Slack alerts
    - Email notifications
    - Custom Resource Definition updates
    - Incident logging
    """

    def __init__(self, settings):
        """Initialize the action dispatcher."""
        self.logger = logging.getLogger(__name__)
        self.settings = settings

        # Incident history
        self.incident_history: List[Alert] = []

        # HTTP session for async requests
        self.session: Optional[aiohttp.ClientSession] = None

    async def initialize(self):
        """Initialize the action dispatcher."""
        self.session = aiohttp.ClientSession()
        self.logger.info("Action dispatcher initialized")

    async def dispatch(self, analysis_result: AnalysisResult):
        """
        Dispatch actions based on analysis result.

        Args:
            analysis_result: The result from root cause analysis
        """
        if not analysis_result:
            return

        # Create alert
        alert = self._create_alert(analysis_result)

        # Store in history
        self.incident_history.append(alert)
        self.logger.info(f"Dispatching alert: {alert.title}")

        # Send notifications based on configuration
        tasks = []

        if self.settings.alert_webhook_url:
            tasks.append(self._send_webhook(alert))

        if self.settings.alert_slack_enabled and self.settings.alert_slack_webhook:
            tasks.append(self._send_slack(alert))

        if self.settings.alert_email_enabled and self.settings.alert_email_to:
            tasks.append(self._send_email(alert))

        # Execute all notifications concurrently
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    def _create_alert(self, result: AnalysisResult) -> Alert:
        """Create an alert from analysis result."""
        # Determine priority based on severity and confidence
        priority = AlertPriority.LOW
        if result.severity.value == "Critical":
            priority = AlertPriority.CRITICAL
        elif result.severity.value == "Error":
            priority = AlertPriority.HIGH
        elif result.severity.value == "Warning":
            priority = AlertPriority.MEDIUM

        title = f"[{priority.value.upper()}] {result.symptom_type.value}: {result.affected_resource}"

        description = f"""
Root Cause Analysis for {result.affected_resource}

Symptom: {result.symptom_type.value}
Severity: {result.severity.value}

Root Cause: {result.root_cause}
Confidence: {result.confidence:.1%}

Evidence:
{chr(10).join(f"- {e}" for e in result.evidence)}

Suggested Fix: {result.suggested_fix}
"""

        return Alert(
            title=title,
            description=description,
            priority=priority,
            affected_resource=result.affected_resource,
            root_cause=result.root_cause,
            confidence=result.confidence,
            suggested_fix=result.suggested_fix,
            evidence=result.evidence,
            metadata={
                "symptom_type": result.symptom_type.value,
                "related_resources": result.related_resources,
                "analysis": result.raw_analysis
            }
        )

    async def _send_webhook(self, alert: Alert):
        """Send alert to webhook."""
        if not self.session or not self.settings.alert_webhook_url:
            return

        try:
            payload = alert.to_dict()
            payload["agent"] = "k3s-sentinel"

            async with self.session.post(
                self.settings.alert_webhook_url,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status == 200:
                    self.logger.info(f"Webhook sent successfully: {alert.title}")
                else:
                    self.logger.warning(f"Webhook returned status {response.status}")

        except Exception as e:
            self.logger.error(f"Error sending webhook: {e}")

    async def _send_slack(self, alert: Alert):
        """Send alert to Slack."""
        if not self.session or not self.settings.alert_slack_webhook:
            return

        try:
            # Format message for Slack
            color = {
                AlertPriority.LOW: "#36a64f",
                AlertPriority.MEDIUM: "#ff9800",
                AlertPriority.HIGH: "#f44336",
                AlertPriority.CRITICAL: "#d32f2f"
            }.get(alert.priority, "#808080")

            payload = {
                "attachments": [
                    {
                        "color": color,
                        "title": alert.title,
                        "text": alert.description,
                        "fields": [
                            {"title": "Resource", "value": alert.affected_resource, "short": True},
                            {"title": "Confidence", "value": f"{alert.confidence:.1%}", "short": True},
                            {"title": "Root Cause", "value": alert.root_cause, "short": False},
                            {"title": "Suggested Fix", "value": alert.suggested_fix, "short": False}
                        ],
                        "footer": "K3s-Sentinel",
                        "ts": int(alert.timestamp.timestamp())
                    }
                ]
            }

            async with self.session.post(
                self.settings.alert_slack_webhook,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status == 200:
                    self.logger.info(f"Slack alert sent: {alert.title}")
                else:
                    self.logger.warning(f"Slack returned status {response.status}")

        except Exception as e:
            self.logger.error(f"Error sending Slack alert: {e}")

    async def _send_email(self, alert: Alert):
        """Send alert via email."""
        # Note: Email requires SMTP configuration
        # This is a placeholder for email implementation
        self.logger.info(f"Email alert (placeholder): {alert.title}")

    async def _update_custom_resource(self, alert: Alert):
        """
        Update Custom Resource Definition with analysis results.

        This allows external systems to query analysis results
        through the Kubernetes API.
        """
        # Placeholder for CRD update logic
        # Would create/update a SentinelAnalysis CR
        self.logger.info(f"Custom resource update (placeholder): {alert.title}")

    async def close(self):
        """Close the action dispatcher and cleanup resources."""
        if self.session:
            await self.session.close()
        self.logger.info("Action dispatcher closed")

    def get_incident_history(
        self,
        resource: str = None,
        since: datetime = None
    ) -> List[Alert]:
        """
        Get incident history.

        Args:
            resource: Filter by resource name
            since: Filter by timestamp

        Returns:
            List of matching alerts
        """
        incidents = self.incident_history

        if resource:
            incidents = [i for i in incidents if resource in i.affected_resource]

        if since:
            incidents = [i for i in incidents if i.timestamp >= since]

        return incidents

    def generate_report(self, format: str = "json") -> str:
        """
        Generate incident report.

        Args:
            format: Output format (json, yaml, markdown)

        Returns:
            Formatted report string
        """
        if format == "json":
            return json.dumps(
                [alert.to_dict() for alert in self.incident_history],
                indent=2
            )

        elif format == "yaml":
            return yaml.dump(
                [alert.to_dict() for alert in self.incident_history],
                default_flow_style=False
            )

        elif format == "markdown":
            return self._generate_markdown_report()

        return str(self.incident_history)

    def _generate_markdown_report(self) -> str:
        """Generate markdown format report."""
        lines = [
            "# K3s-Sentinel Incident Report",
            "",
            f"Generated: {datetime.now().isoformat()}",
            f"Total Incidents: {len(self.incident_history)}",
            ""
        ]

        for i, alert in enumerate(self.incident_history, 1):
            lines.extend([
                f"## {i}. {alert.title}",
                "",
                f"**Time:** {alert.timestamp.isoformat()}",
                f"**Priority:** {alert.priority.value}",
                f"**Resource:** {alert.affected_resource}",
                f"**Root Cause:** {alert.root_cause}",
                f"**Confidence:** {alert.confidence:.1%}",
                "",
                "**Evidence:**",
                *[f"- {e}" for e in alert.evidence],
                "",
                f"**Suggested Fix:** {alert.suggested_fix}",
                "",
                "---",
                ""
            ])

        return "\n".join(lines)
