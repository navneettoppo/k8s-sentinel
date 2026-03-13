"""
Configuration settings for K3s-Sentinel Agent.
Supports multiple LLM providers and comprehensive alerting options.
"""

import os
from typing import Optional, List, Dict, Any
from pathlib import Path
from dataclasses import dataclass, field


@dataclass
class LLMSettings:
    """LLM Provider Settings."""
    # Primary provider configuration
    provider: str = "openai"  # openai, anthropic, gemini, azure_openai, ollama, local, custom
    api_key: Optional[str] = None
    model: str = "gpt-4"
    temperature: float = 0.7
    max_tokens: int = 2000

    # OpenAI specific
    openai_organization: Optional[str] = None
    openai_base_url: Optional[str] = None

    # Anthropic specific
    anthropic_api_version: Optional[str] = None

    # Azure OpenAI specific
    azure_endpoint: Optional[str] = None
    azure_api_version: str = "2024-02-01"

    # Ollama specific
    ollama_base_url: str = "http://localhost:11434"

    # Custom API specific
    custom_base_url: Optional[str] = None

    # Local model specific
    local_model_path: Optional[str] = None
    local_device: str = "auto"

    # Fallback providers
    fallback_providers: List[Dict[str, Any]] = field(default_factory=list)

    # System prompt
    system_prompt: str = "You are a Kubernetes expert helping with root cause analysis. Analyze cluster issues and identify root causes with evidence and suggested fixes."


@dataclass
class AlertSettings:
    """Alert configuration settings."""
    # Enable/disable alerting
    enabled: bool = True

    # Minimum severity to alert
    min_severity: str = "warning"  # debug, info, warning, error, critical

    # Rate limiting
    alert_cooldown_seconds: int = 300  # Don't send duplicate alerts within this time
    max_alerts_per_hour: int = 100

    # Custom webhook (generic)
    webhook_enabled: bool = False
    webhook_url: Optional[str] = None
    webhook_headers: Dict[str, str] = field(default_factory=dict)
    webhook_template: Optional[str] = None

    # Slack
    slack_enabled: bool = False
    slack_webhook_url: Optional[str] = None
    slack_channel: Optional[str] = None
    slack_username: str = "K3s-Sentinel"

    # Microsoft Teams
    teams_enabled: bool = False
    teams_webhook_url: Optional[str] = None

    # Email/SMTP
    email_enabled: bool = False
    email_smtp_host: str = "smtp.gmail.com"
    email_smtp_port: int = 587
    email_use_tls: bool = True
    email_username: Optional[str] = None
    email_password: Optional[str] = None
    email_from: Optional[str] = None
    email_to: List[str] = field(default_factory=list)

    # Telegram
    telegram_enabled: bool = False
    telegram_bot_token: Optional[str] = None
    telegram_chat_id: Optional[str] = None
    telegram_parse_mode: str = "Markdown"

    # Grafana
    grafana_enabled: bool = False
    grafana_url: Optional[str] = None
    grafana_api_key: Optional[str] = None
    grafana_annotation_tags: List[str] = field(default_factory=lambda: ["k3s-sentinel", "rca"])
    grafana_dashboard_id: Optional[str] = None

    # Prometheus Alertmanager
    prometheus_enabled: bool = False
    prometheus_url: Optional[str] = None
    prometheus_alert_labels: Dict[str, str] = field(default_factory=lambda: {"source": "k3s-sentinel"})

    # PagerDuty
    pagerduty_enabled: bool = False
    pagerduty_integration_key: Optional[str] = None
    pagerduty_severity_map: Dict[str, str] = field(default_factory=lambda: {
        "critical": "critical",
        "error": "high",
        "warning": "medium",
        "info": "low"
    })

    # OpsGenie
    opsgenie_enabled: bool = False
    opsgenie_api_key: Optional[str] = None
    opsgenie_team_id: Optional[str] = None
    opsgenie_priority_map: Dict[str, str] = field(default_factory=lambda: {
        "critical": "P1",
        "error": "P2",
        "warning": "P3",
        "info": "P4"
    })

    # Discord
    discord_enabled: bool = False
    discord_webhook_url: Optional[str] = None

    # Mattermost
    mattermost_enabled: bool = False
    mattermost_webhook_url: Optional[str] = None
    mattermost_username: str = "K3s-Sentinel"

    # Webex
    webex_enabled: bool = False
    webex_webhook_url: Optional[str] = None

    # SMS (Twilio)
    sms_enabled: bool = False
    sms_twilio_account_sid: Optional[str] = None
    sms_twilio_auth_token: Optional[str] = None
    sms_twilio_from_number: Optional[str] = None
    sms_to_numbers: List[str] = field(default_factory=list)

    # Custom alert handlers (list of custom webhook configs)
    custom_alerts: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class Settings:
    """Configuration settings for K3s-Sentinel agent."""

    # Agent identification
    agent_name: str = "k3s-sentinel"
    namespace: str = "sentinel-system"

    # K3s connection settings
    k3s_config_path: str = os.path.expanduser("~/.kube/config")
    k3s_context: str = "default"
    k3s_metrics_enabled: bool = True
    k3s_events_enabled: bool = True
    k3s_logs_enabled: bool = True

    # LLM settings
    llm: LLMSettings = field(default_factory=LLMSettings)

    # Alternative direct access for backward compatibility
    @property
    def llm_provider(self) -> str:
        return self.llm.provider

    @llm_provider.setter
    def llm_provider(self, value: str):
        self.llm.provider = value

    @property
    def llm_api_key(self) -> Optional[str]:
        return self.llm.api_key

    @llm_api_key.setter
    def llm_api_key(self, value: Optional[str]):
        self.llm.api_key = value

    @property
    def llm_model(self) -> str:
        return self.llm.model

    @llm_model.setter
    def llm_model(self, value: str):
        self.llm.model = value

    # Backward compatibility properties
    @property
    def llm_temperature(self) -> float:
        return self.llm.temperature

    @property
    def llm_max_tokens(self) -> int:
        return self.llm.max_tokens

    @property
    def llm_local_model_path(self) -> Optional[str]:
        return self.llm.local_model_path

    @property
    def llm_azure_endpoint(self) -> Optional[str]:
        return self.llm.azure_endpoint

    @property
    def llm_azure_api_version(self) -> str:
        return self.llm.azure_api_version

    @property
    def llm_custom_base_url(self) -> Optional[str]:
        return self.llm.custom_base_url

    @property
    def llm_ollama_base_url(self) -> str:
        return self.llm.ollama_base_url

    @property
    def llm_fallback_providers(self) -> List[Dict[str, Any]]:
        return self.llm.fallback_providers

    # Alert settings
    alerts: AlertSettings = field(default_factory=AlertSettings)

    # Backward compatibility for alerts
    @property
    def alert_webhook_url(self) -> Optional[str]:
        return self.alerts.webhook_url

    @alert_webhook_url.setter
    def alert_webhook_url(self, value: Optional[str]):
        self.alerts.webhook_url = value
        self.alerts.webhook_enabled = bool(value)

    @property
    def alert_slack_enabled(self) -> bool:
        return self.alerts.slack_enabled

    @alert_slack_enabled.setter
    def alert_slack_enabled(self, value: bool):
        self.alerts.slack_enabled = value

    @property
    def alert_slack_webhook(self) -> Optional[str]:
        return self.alerts.slack_webhook_url

    @alert_slack_webhook.setter
    def alert_slack_webhook(self, value: Optional[str]):
        self.alerts.slack_webhook_url = value

    @property
    def alert_email_enabled(self) -> bool:
        return self.alerts.email_enabled

    @alert_email_enabled.setter
    def alert_email_enabled(self, value: bool):
        self.alerts.email_enabled = value

    @property
    def alert_email_to(self) -> List[str]:
        return self.alerts.email_to

    @alert_email_to.setter
    def alert_email_to(self, value: List[str]):
        self.alerts.email_to = value

    # Vector database settings
    vector_db_type: str = "chroma"  # Options: chroma, qdrant
    vector_db_path: str = "./data/vector_db"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"

    # Redis settings for real-time processing
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_enabled: bool = False

    # Analysis settings
    poll_interval: int = 10  # seconds
    event_window_size: int = 100
    log_lines_to_fetch: int = 100
    correlation_time_window: int = 300  # seconds

    # Resource constraints (important for K3s)
    cpu_limit: str = "500m"
    memory_limit: str = "512Mi"

    # Logging settings
    log_level: str = "INFO"
    log_file: Optional[str] = None

    # K3s-specific component mapping
    k3s_components: dict = field(default_factory=lambda: {
        "ingress": "traefik",
        "loadbalancer": "klipper-lb",
        "storage": "local-path-provisioner",
        "dns": "coredns",
        "servicelb": "svc-lb",
        "metrics": "metrics-server"
    })

    # Known error patterns
    error_patterns: dict = field(default_factory=lambda: {
        "CrashLoopBackOff": {
            "description": "Container is restarting repeatedly",
            "common_causes": ["OOMKilled", "Application error", "Liveness probe failure"]
        },
        "Evicted": {
            "description": "Pod was evicted from node",
            "common_causes": ["Disk pressure", "Memory pressure", "Node starvation"]
        },
        "CreateContainerConfigError": {
            "description": "Container configuration error",
            "common_causes": ["Missing ConfigMap", "Missing Secret", "Invalid image"]
        },
        "FailedScheduling": {
            "description": "Pod cannot be scheduled",
            "common_causes": ["Insufficient resources", "Taints/tolerations", "PVC not bound"]
        },
        "Unhealthy": {
            "description": "Readiness or liveness probe failed",
            "common_causes": ["Application not ready", "Network issues", "Startup probe failure"]
        }
    })

    def __post_init__(self):
        """Process environment variables and validate settings."""
        # Override with environment variables if present

        # LLM settings from environment
        self.llm.api_key = os.getenv("LLM_API_KEY", self.llm.api_key)
        self.llm.provider = os.getenv("LLM_PROVIDER", self.llm.provider)
        self.llm.model = os.getenv("LLM_MODEL", self.llm.model)

        # Azure OpenAI
        self.llm.azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", self.llm.azure_endpoint)

        # Ollama
        self.llm.ollama_base_url = os.getenv("OLLAMA_BASE_URL", self.llm.ollama_base_url)

        # Custom API
        self.llm.custom_base_url = os.getenv("CUSTOM_LLM_BASE_URL", self.llm.custom_base_url)

        # Alert webhooks from environment
        self.alerts.webhook_url = os.getenv("ALERT_WEBHOOK_URL", self.alerts.webhook_url)
        self.alerts.slack_webhook_url = os.getenv("SLACK_WEBHOOK_URL", self.alerts.slack_webhook_url)
        self.alerts.teams_webhook_url = os.getenv("TEAMS_WEBHOOK_URL", self.alerts.teams_webhook_url)
        self.alerts.telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN", self.alerts.telegram_bot_token)
        self.alerts.telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID", self.alerts.telegram_chat_id)
        self.alerts.grafana_url = os.getenv("GRAFANA_URL", self.alerts.grafana_url)
        self.alerts.grafana_api_key = os.getenv("GRAFANA_API_KEY", self.alerts.grafana_api_key)
        self.alerts.prometheus_url = os.getenv("PROMETHEUS_URL", self.alerts.prometheus_url)
        self.alerts.pagerduty_integration_key = os.getenv("PAGERDUTY_INTEGRATION_KEY", self.alerts.pagerduty_integration_key)
        self.alerts.opsgenie_api_key = os.getenv("OPSGENIE_API_KEY", self.alerts.opsgenie_api_key)

        # Email settings
        self.alerts.email_username = os.getenv("EMAIL_USERNAME", self.alerts.email_username)
        self.alerts.email_password = os.getenv("EMAIL_PASSWORD", self.alerts.email_password)
        self.alerts.email_from = os.getenv("EMAIL_FROM", self.alerts.email_from)

        # Enable alerts if any webhook is configured
        if self.alerts.webhook_url or self.alerts.slack_webhook_url:
            self.alerts.enabled = True

        # Ensure data directory exists
        Path(self.vector_db_path).mkdir(parents=True, exist_ok=True)

    @classmethod
    def from_dict(cls, config: Dict[str, Any]) -> "Settings":
        """Create settings from dictionary."""
        llm_config = config.get("llm", {})
        alert_config = config.get("alerts", {})

        llm_settings = LLMSettings(
            provider=llm_config.get("provider", "openai"),
            api_key=llm_config.get("api_key"),
            model=llm_config.get("model", "gpt-4"),
            temperature=llm_config.get("temperature", 0.7),
            max_tokens=llm_config.get("max_tokens", 2000),
            azure_endpoint=llm_config.get("azure_endpoint"),
            ollama_base_url=llm_config.get("ollama_base_url", "http://localhost:11434"),
            custom_base_url=llm_config.get("custom_base_url"),
            fallback_providers=llm_config.get("fallback_providers", [])
        )

        alert_settings = AlertSettings(
            enabled=alert_config.get("enabled", True),
            min_severity=alert_config.get("min_severity", "warning"),
            webhook_enabled=alert_config.get("webhook_enabled", False),
            webhook_url=alert_config.get("webhook_url"),
            slack_enabled=alert_config.get("slack_enabled", False),
            slack_webhook_url=alert_config.get("slack_webhook_url"),
            teams_enabled=alert_config.get("teams_enabled", False),
            teams_webhook_url=alert_config.get("teams_webhook_url"),
            email_enabled=alert_config.get("email_enabled", False),
            email_smtp_host=alert_config.get("email_smtp_host", "smtp.gmail.com"),
            email_smtp_port=alert_config.get("email_smtp_port", 587),
            email_from=alert_config.get("email_from"),
            email_to=alert_config.get("email_to", []),
            telegram_enabled=alert_config.get("telegram_enabled", False),
            telegram_bot_token=alert_config.get("telegram_bot_token"),
            telegram_chat_id=alert_config.get("telegram_chat_id"),
            grafana_enabled=alert_config.get("grafana_enabled", False),
            grafana_url=alert_config.get("grafana_url"),
            grafana_api_key=alert_config.get("grafana_api_key"),
            prometheus_enabled=alert_config.get("prometheus_enabled", False),
            prometheus_url=alert_config.get("prometheus_url"),
            pagerduty_enabled=alert_config.get("pagerduty_enabled", False),
            pagerduty_integration_key=alert_config.get("pagerduty_integration_key"),
            opsgenie_enabled=alert_config.get("opsgenie_enabled", False),
            opsgenie_api_key=alert_config.get("opsgenie_api_key"),
            discord_enabled=alert_config.get("discord_enabled", False),
            discord_webhook_url=alert_config.get("discord_webhook_url"),
            mattermost_enabled=alert_config.get("mattermost_enabled", False),
            mattermost_webhook_url=alert_config.get("mattermost_webhook_url"),
            custom_alerts=alert_config.get("custom_alerts", [])
        )

        return cls(
            llm=llm_settings,
            alerts=alert_settings,
            **{k: v for k, v in config.items() if k not in ["llm", "alerts"]}
        )

    @classmethod
    def from_yaml(cls, yaml_path: str) -> "Settings":
        """Load settings from YAML file."""
        import yaml
        with open(yaml_path, 'r') as f:
            config = yaml.safe_load(f)
        return cls.from_dict(config)

    @classmethod
    def from_json(cls, json_path: str) -> "Settings":
        """Load settings from JSON file."""
        import json
        with open(json_path, 'r') as f:
            config = json.load(f)
        return cls.from_dict(config)


def load_settings(config_path: str = None) -> Settings:
    """Load settings from configuration file or use defaults."""
    if config_path:
        path = Path(config_path)
        if path.exists():
            if path.suffix in ['.yaml', '.yml']:
                return Settings.from_yaml(config_path)
            elif path.suffix == '.json':
                return Settings.from_json(config_path)

    return Settings()
