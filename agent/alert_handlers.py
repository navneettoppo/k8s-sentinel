"""
Alert Handlers for K3s-Sentinel Agent.

Supports multiple alerting channels:
- Slack
- Microsoft Teams
- Email/SMTP
- Telegram
- Grafana
- Prometheus Alertmanager
- PagerDuty
- OpsGenie
- Discord
- Mattermost
- Webex
- SMS (Twilio)
- Custom webhooks
"""

import asyncio
import logging
import json
import base64
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import aiohttp

from agent.analysis_core import AnalysisResult, EventSeverity


class AlertPriority(Enum):
    """Alert priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


SEVERITY_TO_PRIORITY = {
    "Normal": AlertPriority.LOW,
    "Warning": AlertPriority.MEDIUM,
    "Error": AlertPriority.HIGH,
    "Critical": AlertPriority.CRITICAL,
}


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
    evidence: List[str]
    timestamp: datetime
    metadata: Dict[str, Any]
    severity: EventSeverity

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


class BaseAlertHandler:
    """Base class for alert handlers."""

    def __init__(self, settings, logger=None):
        self.settings = settings
        self.logger = logger or logging.getLogger(self.__class__.__name__)
        self.session: Optional[aiohttp.ClientSession] = None

    async def initialize(self):
        """Initialize the handler."""
        if self.session is None:
            self.session = aiohttp.ClientSession()

    async def cleanup(self):
        """Cleanup resources."""
        if self.session:
            await self.session.close()

    async def send(self, alert: Alert) -> bool:
        """Send alert. Returns True if successful."""
        raise NotImplementedError


class SlackHandler(BaseAlertHandler):
    """Slack alert handler."""

    async def send(self, alert: Alert) -> bool:
        if not self.settings.alerts.slack_enabled or not self.settings.alerts.slack_webhook_url:
            return False

        try:
            color = {
                AlertPriority.LOW: "#36a64f",
                AlertPriority.MEDIUM: "#ff9800",
                AlertPriority.HIGH: "#f44336",
                AlertPriority.CRITICAL: "#d32f2f"
            }.get(alert.priority, "#808080")

            payload = {
                "username": self.settings.alerts.slack_username,
                "attachments": [{
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
                }]
            }

            async with self.session.post(
                self.settings.alerts.slack_webhook_url,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status == 200:
                    self.logger.info(f"Slack alert sent: {alert.title}")
                    return True
                else:
                    self.logger.warning(f"Slack returned status {response.status}")
                    return False

        except Exception as e:
            self.logger.error(f"Error sending Slack alert: {e}")
            return False


class TeamsHandler(BaseAlertHandler):
    """Microsoft Teams alert handler."""

    async def send(self, alert: Alert) -> bool:
        if not self.settings.alerts.teams_enabled or not self.settings.alerts.teams_webhook_url:
            return False

        try:
            theme_color = {
                AlertPriority.LOW: "36a64f",
                AlertPriority.MEDIUM: "ff9800",
                AlertPriority.HIGH: "f44336",
                AlertPriority.CRITICAL: "d32f2f"
            }.get(alert.priority, "808080")

            payload = {
                "@type": "MessageCard",
                "@context": "http://schema.org/extensions",
                "themeColor": theme_color,
                "summary": alert.title,
                "sections": [{
                    "activityTitle": alert.title,
                    "facts": [
                        {"name": "Resource:", "value": alert.affected_resource},
                        {"name": "Root Cause:", "value": alert.root_cause},
                        {"name": "Confidence:", "value": f"{alert.confidence:.1%}"},
                        {"name": "Suggested Fix:", "value": alert.suggested_fix}
                    ],
                    "markdown": True
                }]
            }

            async with self.session.post(
                self.settings.alerts.teams_webhook_url,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status in [200, 201]:
                    self.logger.info(f"Teams alert sent: {alert.title}")
                    return True
                else:
                    self.logger.warning(f"Teams returned status {response.status}")
                    return False

        except Exception as e:
            self.logger.error(f"Error sending Teams alert: {e}")
            return False


class TelegramHandler(BaseAlertHandler):
    """Telegram alert handler."""

    async def send(self, alert: Alert) -> bool:
        if not self.settings.alerts.telegram_enabled:
            return False

        if not self.settings.alerts.telegram_bot_token or not self.settings.alerts.telegram_chat_id:
            return False

        try:
            message = f"*{alert.title}*\n\n"
            message += f"*Resource:* {alert.affected_resource}\n"
            message += f"*Root Cause:* {alert.root_cause}\n"
            message += f"*Confidence:* {alert.confidence:.1%}\n"
            message += f"*Suggested Fix:* {alert.suggested_fix}"

            payload = {
                "chat_id": self.settings.alerts.telegram_chat_id,
                "text": message,
                "parse_mode": self.settings.alerts.telegram_parse_mode
            }

            url = f"https://api.telegram.org/bot{self.settings.alerts.telegram_bot_token}/sendMessage"

            async with self.session.post(
                url,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status == 200:
                    self.logger.info(f"Telegram alert sent: {alert.title}")
                    return True
                else:
                    self.logger.warning(f"Telegram returned status {response.status}")
                    return False

        except Exception as e:
            self.logger.error(f"Error sending Telegram alert: {e}")
            return False


class EmailHandler(BaseAlertHandler):
    """Email/SMTP alert handler."""

    async def send(self, alert: Alert) -> bool:
        if not self.settings.alerts.email_enabled or not self.settings.alerts.email_to:
            return False

        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart

            msg = MIMEMultipart()
            msg["From"] = self.settings.alerts.email_from or self.settings.alerts.email_username
            msg["To"] = ", ".join(self.settings.alerts.email_to)
            msg["Subject"] = alert.title

            body = f"""
K3s-Sentinel Alert

{alert.description}

Resource: {alert.affected_resource}
Root Cause: {alert.root_cause}
Confidence: {alert.confidence:.1%}
Suggested Fix: {alert.suggested_fix}
"""
            msg.attach(MIMEText(body, "plain"))

            with smtplib.SMTP(
                self.settings.alerts.email_smtp_host,
                self.settings.alerts.email_smtp_port
            ) as server:
                if self.settings.alerts.email_use_tls:
                    server.starttls()
                if self.settings.alerts.email_username and self.settings.alerts.email_password:
                    server.login(
                        self.settings.alerts.email_username,
                        self.settings.alerts.email_password
                    )
                server.send_message(msg)

            self.logger.info(f"Email alert sent: {alert.title}")
            return True

        except Exception as e:
            self.logger.error(f"Error sending email alert: {e}")
            return False


class GrafanaHandler(BaseAlertHandler):
    """Grafana alert handler."""

    async def send(self, alert: Alert) -> bool:
        if not self.settings.alerts.grafana_enabled:
            return False

        if not self.settings.alerts.grafana_url or not self.settings.alerts.grafana_api_key:
            return False

        try:
            headers = {
                "Authorization": f"Bearer {self.settings.alerts.grafana_api_key}",
                "Content-Type": "application/json"
            }

            # Map priority to Grafana severity
            severity_map = {
                AlertPriority.CRITICAL: "critical",
                AlertPriority.HIGH: "error",
                AlertPriority.MEDIUM: "warning",
                AlertPriority.LOW: "info"
            }

            payload = {
                "text": alert.title,
                "tags": self.settings.alerts.grafana_annotation_tags + ["rca", alert.affected_resource],
                "alertType": severity_map.get(alert.priority, "info"),
                "source": "K3s-Sentinel"
            }

            # Add dashboard link if configured
            if self.settings.alerts.grafana_dashboard_id:
                payload["dashboardId"] = self.settings.alerts.grafana_dashboard_id

            url = f"{self.settings.alerts.grafana_url}/api/annotations"

            async with self.session.post(
                url,
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status in [200, 201, 204]:
                    self.logger.info(f"Grafana annotation created: {alert.title}")
                    return True
                else:
                    self.logger.warning(f"Grafana returned status {response.status}")
                    return False

        except Exception as e:
            self.logger.error(f"Error sending Grafana alert: {e}")
            return False


class PrometheusHandler(BaseAlertHandler):
    """Prometheus Alertmanager alert handler."""

    async def send(self, alert: Alert) -> bool:
        if not self.settings.alerts.prometheus_enabled or not self.settings.alerts.prometheus_url:
            return False

        try:
            severity_map = {
                AlertPriority.CRITICAL: "critical",
                AlertPriority.HIGH: "high",
                AlertPriority.MEDIUM: "medium",
                AlertPriority.LOW: "low"
            }

            # Create Prometheus alert format
            alerts = [{
                "labels": {
                    "alertname": alert.title,
                    "severity": severity_map.get(alert.priority, "info"),
                    "source": "k3s-sentinel",
                    "resource": alert.affected_resource,
                    **self.settings.alerts.prometheus_alert_labels
                },
                "annotations": {
                    "summary": alert.title,
                    "description": alert.description,
                    "root_cause": alert.root_cause,
                    "suggested_fix": alert.suggested_fix
                },
                "startsAt": alert.timestamp.isoformat() + "Z"
            }]

            payload = {"alerts": alerts}

            url = f"{self.settings.alerts.prometheus_url}/api/v1/alerts"

            async with self.session.post(
                url,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status in [200, 201]:
                    self.logger.info(f"Prometheus alert sent: {alert.title}")
                    return True
                else:
                    self.logger.warning(f"Prometheus returned status {response.status}")
                    return False

        except Exception as e:
            self.logger.error(f"Error sending Prometheus alert: {e}")
            return False


class PagerDutyHandler(BaseAlertHandler):
    """PagerDuty alert handler."""

    async def send(self, alert: Alert) -> bool:
        if not self.settings.alerts.pagerduty_enabled or not self.settings.alerts.pagerduty_integration_key:
            return False

        try:
            severity = self.settings.alerts.pagerduty_severity_map.get(
                alert.priority.value, "medium"
            )

            payload = {
                "routing_key": self.settings.alerts.pagerduty_integration_key,
                "event_action": "trigger",
                "payload": {
                    "summary": alert.title,
                    "severity": severity,
                    "source": "k3s-sentinel",
                    "custom_details": {
                        "resource": alert.affected_resource,
                        "root_cause": alert.root_cause,
                        "confidence": alert.confidence,
                        "suggested_fix": alert.suggested_fix,
                        "evidence": alert.evidence
                    }
                }
            }

            url = "https://events.pagerduty.com/v2/enqueue"

            async with self.session.post(
                url,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status == 202:
                    self.logger.info(f"PagerDuty alert sent: {alert.title}")
                    return True
                else:
                    self.logger.warning(f"PagerDuty returned status {response.status}")
                    return False

        except Exception as e:
            self.logger.error(f"Error sending PagerDuty alert: {e}")
            return False


class OpsGenieHandler(BaseAlertHandler):
    """OpsGenie alert handler."""

    async def send(self, alert: Alert) -> bool:
        if not self.settings.alerts.opsgenie_enabled or not self.settings.alerts.opsgenie_api_key:
            return False

        try:
            priority = self.settings.alerts.opsgenie_priority_map.get(
                alert.priority.value, "P3"
            )

            payload = {
                "message": alert.title,
                "priority": priority,
                "tags": ["k3s-sentinel", alert.affected_resource],
                "description": alert.description,
                "details": {
                    "resource": alert.affected_resource,
                    "root_cause": alert.root_cause,
                    "confidence": alert.confidence,
                    "suggested_fix": alert.suggested_fix
                }
            }

            headers = {
                "Authorization": f"GenieKey {self.settings.alerts.opsgenie_api_key}",
                "Content-Type": "application/json"
            }

            url = "https://api.opsgenie.com/v2/alerts"

            async with self.session.post(
                url,
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status in [200, 201, 202]:
                    self.logger.info(f"OpsGenie alert sent: {alert.title}")
                    return True
                else:
                    self.logger.warning(f"OpsGenie returned status {response.status}")
                    return False

        except Exception as e:
            self.logger.error(f"Error sending OpsGenie alert: {e}")
            return False


class DiscordHandler(BaseAlertHandler):
    """Discord alert handler."""

    async def send(self, alert: Alert) -> bool:
        if not self.settings.alerts.discord_enabled or not self.settings.alerts.discord_webhook_url:
            return False

        try:
            color = {
                AlertPriority.LOW: 3066993,
                AlertPriority.MEDIUM: 16776960,
                AlertPriority.HIGH: 15158332,
                AlertPriority.CRITICAL: 10038562
            }.get(alert.priority, 8421504)

            embed = {
                "title": alert.title,
                "description": alert.description[:2000],
                "color": color,
                "fields": [
                    {"name": "Resource", "value": alert.affected_resource, "inline": True},
                    {"name": "Confidence", "value": f"{alert.confidence:.1%}", "inline": True},
                    {"name": "Root Cause", "value": alert.root_cause[:1000]},
                    {"name": "Suggested Fix", "value": alert.suggested_fix[:1000]}
                ],
                "footer": {"text": "K3s-Sentinel"},
                "timestamp": alert.timestamp.isoformat()
            }

            payload = {"embeds": [embed]}

            async with self.session.post(
                self.settings.alerts.discord_webhook_url,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status in [200, 201, 204]:
                    self.logger.info(f"Discord alert sent: {alert.title}")
                    return True
                else:
                    self.logger.warning(f"Discord returned status {response.status}")
                    return False

        except Exception as e:
            self.logger.error(f"Error sending Discord alert: {e}")
            return False


class MattermostHandler(BaseAlertHandler):
    """Mattermost alert handler."""

    async def send(self, alert: Alert) -> bool:
        if not self.settings.alerts.mattermost_enabled or not self.settings.alerts.mattermost_webhook_url:
            return False

        try:
            payload = {
                "username": self.settings.alerts.mattermost_username,
                "text": f"**{alert.title}**\n\n{alert.description[:1500]}"
            }

            async with self.session.post(
                self.settings.alerts.mattermost_webhook_url,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status == 200:
                    self.logger.info(f"Mattermost alert sent: {alert.title}")
                    return True
                else:
                    self.logger.warning(f"Mattermost returned status {response.status}")
                    return False

        except Exception as e:
            self.logger.error(f"Error sending Mattermost alert: {e}")
            return False


class WebexHandler(BaseAlertHandler):
    """Webex alert handler."""

    async def send(self, alert: Alert) -> bool:
        if not self.settings.alerts.webex_enabled or not self.settings.alerts.webex_webhook_url:
            return False

        try:
            payload = {
                "markdown": f"## {alert.title}\n\n{alert.description[:1500]}"
            }

            async with self.session.post(
                self.settings.alerts.webex_webhook_url,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status == 200:
                    self.logger.info(f"Webex alert sent: {alert.title}")
                    return True
                else:
                    self.logger.warning(f"Webex returned status {response.status}")
                    return False

        except Exception as e:
            self.logger.error(f"Error sending Webex alert: {e}")
            return False


class TwilioSMSHandler(BaseAlertHandler):
    """Twilio SMS alert handler."""

    async def send(self, alert: Alert) -> bool:
        if not self.settings.alerts.sms_enabled:
            return False

        if not all([
            self.settings.alerts.sms_twilio_account_sid,
            self.settings.alerts.sms_twilio_auth_token,
            self.settings.alerts.sms_twilio_from_number,
            self.settings.alerts.sms_to_numbers
        ]):
            return False

        try:
            # Twilio API requires Basic Auth
            auth = base64.b64encode(
                f"{self.settings.alerts.sms_twilio_account_sid}:{self.settings.alerts.sms_twilio_auth_token}".encode()
            ).decode()

            message = f"K3s-Sentinel: {alert.title}\n{alert.affected_resource}: {alert.root_cause[:100]}"

            for to_number in self.settings.alerts.sms_to_numbers:
                payload = {
                    "To": to_number,
                    "From": self.settings.alerts.sms_twilio_from_number,
                    "Body": message
                }

                url = f"https://api.twilio.com/2010-04-01/Accounts/{self.settings.alerts.sms_twilio_account_sid}/Messages.json"

                headers = {"Authorization": f"Basic {auth}"}

                async with self.session.post(
                    url,
                    headers=headers,
                    data=payload,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status != 201:
                        self.logger.warning(f"Twilio SMS failed to {to_number}: {response.status}")

            self.logger.info(f"Twilio SMS alerts sent: {alert.title}")
            return True

        except Exception as e:
            self.logger.error(f"Error sending Twilio SMS: {e}")
            return False


class CustomWebhookHandler(BaseAlertHandler):
    """Custom webhook alert handler."""

    async def send(self, alert: Alert) -> bool:
        if not self.settings.alerts.webhook_enabled or not self.settings.alerts.webhook_url:
            return False

        try:
            payload = alert.to_dict()
            payload["agent"] = "k3s-sentinel"

            # Apply custom template if provided
            if self.settings.alerts.webhook_template:
                # Simple template substitution
                template = self.settings.alerts.webhook_template
                payload = json.loads(template.format(**payload))

            headers = {
                "Content-Type": "application/json",
                **self.settings.alerts.webhook_headers
            }

            async with self.session.post(
                self.settings.alerts.webhook_url,
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status == 200:
                    self.logger.info(f"Custom webhook alert sent: {alert.title}")
                    return True
                else:
                    self.logger.warning(f"Custom webhook returned status {response.status}")
                    return False

        except Exception as e:
            self.logger.error(f"Error sending custom webhook alert: {e}")
            return False


class CustomAlertHandler(BaseAlertHandler):
    """Handler for custom configured alert endpoints."""

    def __init__(self, settings, config: Dict[str, Any], logger=None):
        super().__init__(settings, logger)
        self.config = config

    async def send(self, alert: Alert) -> bool:
        try:
            payload = alert.to_dict()
            payload["agent"] = "k3s-sentinel"

            # Apply custom template if provided
            template = self.config.get("template")
            if template:
                payload = json.loads(template.format(**payload))

            headers = {
                "Content-Type": "application/json",
                **self.config.get("headers", {})
            }

            url = self.config.get("url")
            if not url:
                return False

            async with self.session.post(
                url,
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status in [200, 201, 202]:
                    self.logger.info(f"Custom alert sent to {self.config.get('name', 'unknown')}: {alert.title}")
                    return True
                else:
                    self.logger.warning(f"Custom alert returned status {response.status}")
                    return False

        except Exception as e:
            self.logger.error(f"Error sending custom alert: {e}")
            return False


class AlertDispatcher:
    """Dispatcher for managing all alert handlers."""

    def __init__(self, settings):
        self.logger = logging.getLogger(__name__)
        self.settings = settings
        self.handlers: List[BaseAlertHandler] = []
        self.alert_history: Dict[str, datetime] = {}  # For cooldown tracking

    async def initialize(self):
        """Initialize all alert handlers."""
        self.logger.info("Initializing alert handlers...")

        # Create all handlers based on settings
        handlers_to_create = [
            (SlackHandler, self.settings.alerts.slack_enabled),
            (TeamsHandler, self.settings.alerts.teams_enabled),
            (TelegramHandler, self.settings.alerts.telegram_enabled),
            (EmailHandler, self.settings.alerts.email_enabled),
            (GrafanaHandler, self.settings.alerts.grafana_enabled),
            (PrometheusHandler, self.settings.alerts.prometheus_enabled),
            (PagerDutyHandler, self.settings.alerts.pagerduty_enabled),
            (OpsGenieHandler, self.settings.alerts.opsgenie_enabled),
            (DiscordHandler, self.settings.alerts.discord_enabled),
            (MattermostHandler, self.settings.alerts.mattermost_enabled),
            (WebexHandler, self.settings.alerts.webex_enabled),
            (TwilioSMSHandler, self.settings.alerts.sms_enabled),
            (CustomWebhookHandler, self.settings.alerts.webhook_enabled),
        ]

        for handler_class, enabled in handlers_to_create:
            if enabled:
                try:
                    handler = handler_class(self.settings, self.logger)
                    await handler.initialize()
                    self.handlers.append(handler)
                    self.logger.info(f"Initialized {handler_class.__name__}")
                except Exception as e:
                    self.logger.error(f"Failed to initialize {handler_class.__name__}: {e}")

        # Add custom alert handlers
        for custom_config in self.settings.alerts.custom_alerts:
            try:
                handler = CustomAlertHandler(self.settings, custom_config, self.logger)
                await handler.initialize()
                self.handlers.append(handler)
                self.logger.info(f"Initialized custom alert handler: {custom_config.get('name', 'unknown')}")
            except Exception as e:
                self.logger.error(f"Failed to initialize custom alert handler: {e}")

        self.logger.info(f"Initialized {len(self.handlers)} alert handlers")

    async def dispatch(self, analysis_result: AnalysisResult) -> bool:
        """Dispatch alert to all enabled handlers."""
        if not self.settings.alerts.enabled:
            return False

        # Check severity threshold
        severity_order = ["debug", "info", "warning", "error", "critical"]
        min_severity = self.settings.alerts.min_severity.lower()
        if severity_order.index(analysis_result.severity.value.lower()) < severity_order.index(min_severity):
            self.logger.debug(f"Alert severity {analysis_result.severity.value} below threshold {min_severity}")
            return False

        # Create alert object
        alert = self._create_alert(analysis_result)

        # Check cooldown (rate limiting)
        alert_key = f"{alert.affected_resource}:{alert.root_cause}"
        if alert_key in self.alert_history:
            time_since_last = (datetime.now() - self.alert_history[alert_key]).total_seconds()
            if time_since_last < self.settings.alerts.alert_cooldown_seconds:
                self.logger.debug(f"Alert {alert_key} in cooldown period")
                return False

        # Update alert history
        self.alert_history[alert_key] = datetime.now()

        # Send to all handlers
        tasks = [handler.send(alert) for handler in self.handlers]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        success_count = sum(1 for r in results if r is True)
        self.logger.info(f"Alert dispatched to {success_count}/{len(self.handlers)} handlers")

        return success_count > 0

    def _create_alert(self, result: AnalysisResult) -> Alert:
        """Create alert from analysis result."""
        # Determine priority based on severity
        priority = SEVERITY_TO_PRIORITY.get(result.severity.value, AlertPriority.MEDIUM)

        if result.confidence > 0.9:
            # Boost priority for high confidence
            if priority == AlertPriority.MEDIUM:
                priority = AlertPriority.HIGH
            elif priority == AlertPriority.HIGH:
                priority = AlertPriority.CRITICAL

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
            timestamp=result.timestamp,
            metadata={
                "symptom_type": result.symptom_type.value,
                "related_resources": result.related_resources,
                "analysis": result.raw_analysis
            },
            severity=result.severity
        )

    async def close(self):
        """Cleanup all handlers."""
        for handler in self.handlers:
            await handler.cleanup()
        self.logger.info("Alert handlers closed")
