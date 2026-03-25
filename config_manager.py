"""
Configuration Manager for K3s-Sentinel.

Handles persistent configuration storage using TOML format.
Manages kubeconfig paths, UI settings, and user preferences.
"""

import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass, field

try:
    import tomllib
except ImportError:
    # Python < 3.11 compatibility
    import tomli as tomllib


@dataclass
class KubeconfigConfig:
    """Kubeconfig-related configuration."""
    path: Optional[str] = None
    last_context: Optional[str] = None


@dataclass
class UIConfig:
    """UI-related configuration."""
    theme: str = "dark"
    refresh_interval: int = 30


@dataclass
class AppConfig:
    """Main application configuration."""
    kubeconfig: KubeconfigConfig = field(default_factory=KubeconfigConfig)
    ui: UIConfig = field(default_factory=UIConfig)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AppConfig":
        """Create config from dictionary."""
        kubeconfig_data = data.get("kubeconfig", {})
        ui_data = data.get("ui", {})

        return cls(
            kubeconfig=KubeconfigConfig(
                path=kubeconfig_data.get("path"),
                last_context=kubeconfig_data.get("last_context")
            ),
            ui=UIConfig(
                theme=ui_data.get("theme", "dark"),
                refresh_interval=ui_data.get("refresh_interval", 30)
            )
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return {
            "kubeconfig": {
                "path": self.kubeconfig.path,
                "last_context": self.kubeconfig.last_context
            },
            "ui": {
                "theme": self.ui.theme,
                "refresh_interval": self.ui.refresh_interval
            }
        }


class ConfigManager:
    """
    Manages persistent configuration for K3s-Sentinel.

    Configuration is stored in ~/.config/k3s-sentinel/config.toml
    """

    CONFIG_DIR = Path.home() / ".config" / "k3s-sentinel"
    CONFIG_FILE = CONFIG_DIR / "config.toml"

    def __init__(self):
        """Initialize the configuration manager."""
        self._config: Optional[AppConfig] = None
        self._ensure_config_dir()

    def _ensure_config_dir(self) -> None:
        """Ensure configuration directory exists."""
        try:
            self.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        except PermissionError:
            # Fall back to temp directory if home is not writable
            self.CONFIG_DIR = Path("/tmp") / ".config" / "k3s-sentinel"
            self.CONFIG_FILE = self.CONFIG_DIR / "config.toml"
            self.CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    def load(self) -> AppConfig:
        """
        Load configuration from file.

        Returns:
            AppConfig object with loaded configuration
        """
        if self._config is not None:
            return self._config

        if not self.CONFIG_FILE.exists():
            self._config = AppConfig()
            return self._config

        try:
            with open(self.CONFIG_FILE, "rb") as f:
                data = tomllib.load(f)
            self._config = AppConfig.from_dict(data)
        except Exception as e:
            print(f"Warning: Failed to load config from {self.CONFIG_FILE}: {e}")
            self._config = AppConfig()

        return self._config

    def save(self, config: Optional[AppConfig] = None) -> None:
        """
        Save configuration to file.

        Args:
            config: Configuration to save. If None, uses current config.
        """
        if config is not None:
            self._config = config
        elif self._config is None:
            self._config = AppConfig()

        try:
            # Convert to TOML string manually for compatibility
            toml_content = self._config_to_toml(self._config)
            with open(self.CONFIG_FILE, "w") as f:
                f.write(toml_content)
        except PermissionError:
            print(f"Warning: Cannot write to {self.CONFIG_FILE}, config will not persist")
        except Exception as e:
            print(f"Warning: Failed to save config: {e}")

    def _config_to_toml(self, config: AppConfig) -> str:
        """Convert config to TOML string."""
        lines = ["# K3s-Sentinel Configuration", "# Auto-generated file", ""]

        lines.append("[kubeconfig]")
        if config.kubeconfig.path:
            lines.append(f'path = "{config.kubeconfig.path}"')
        if config.kubeconfig.last_context:
            lines.append(f'last_context = "{config.kubeconfig.last_context}"')

        lines.append("")
        lines.append("[ui]")
        lines.append(f'theme = "{config.ui.theme}"')
        lines.append(f"refresh_interval = {config.ui.refresh_interval}")

        return "\n".join(lines)

    def get_kubeconfig_path(self) -> Optional[str]:
        """Get the configured kubeconfig path."""
        config = self.load()
        return config.kubeconfig.path

    def set_kubeconfig_path(self, path: str) -> None:
        """Set the kubeconfig path and save."""
        config = self.load()
        config.kubeconfig.path = path
        self.save(config)

    def get_last_context(self) -> Optional[str]:
        """Get the last used context."""
        config = self.load()
        return config.kubeconfig.last_context

    def set_last_context(self, context: str) -> None:
        """Set the last used context and save."""
        config = self.load()
        config.kubeconfig.last_context = context
        self.save(config)

    def get_ui_theme(self) -> str:
        """Get the UI theme."""
        config = self.load()
        return config.ui.theme

    def set_ui_theme(self, theme: str) -> None:
        """Set the UI theme and save."""
        config = self.load()
        config.ui.theme = theme
        self.save(config)

    def get_refresh_interval(self) -> int:
        """Get the refresh interval in seconds."""
        config = self.load()
        return config.ui.refresh_interval

    def set_refresh_interval(self, interval: int) -> None:
        """Set the refresh interval and save."""
        config = self.load()
        config.ui.refresh_interval = interval
        self.save(config)


# Singleton instance
_config_manager: Optional[ConfigManager] = None


def get_config_manager() -> ConfigManager:
    """Get the singleton config manager instance."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


def resolve_kubeconfig_path(cli_path: Optional[str] = None) -> Optional[str]:
    """
    Resolve kubeconfig path following priority order:
    1. CLI flag --kubeconfig
    2. Environment variable KUBECONFIG
    3. Default ~/.kube/config
    4. Default /etc/rancher/k3s/k3s.yaml

    Args:
        cli_path: Path provided via CLI flag

    Returns:
        Resolved kubeconfig path or None if no valid path found
    """
    # 1. CLI flag takes highest priority
    if cli_path:
        expanded = os.path.expanduser(os.path.expandvars(cli_path))
        if os.path.exists(expanded) and os.access(expanded, os.R_OK):
            return expanded
        return None

    # 2. Environment variable
    env_path = os.environ.get("KUBECONFIG")
    if env_path:
        # KUBECONFIG can contain multiple paths separated by colons
        paths = env_path.split(":")
        for p in paths:
            expanded = os.path.expanduser(os.path.expandvars(p))
            if os.path.exists(expanded) and os.access(expanded, os.R_OK):
                return expanded

    # 3. Default ~/.kube/config
    default_path = os.path.expanduser("~/.kube/config")
    if os.path.exists(default_path) and os.access(default_path, os.R_OK):
        return default_path

    # 4. Default K3s path
    k3s_default = "/etc/rancher/k3s/k3s.yaml"
    if os.path.exists(k3s_default) and os.access(k3s_default, os.R_OK):
        return k3s_default

    return None


def validate_kubeconfig_path(path: str) -> tuple[bool, str]:
    """
    Validate a kubeconfig path.

    Args:
        path: Path to validate

    Returns:
        Tuple of (is_valid, message)
    """
    if not path:
        return False, "Path is empty"

    expanded = os.path.expanduser(os.path.expandvars(path))

    if not os.path.exists(expanded):
        return False, f"Path does not exist: {expanded}"

    if not os.path.isfile(expanded):
        return False, f"Path is not a file: {expanded}"

    if not os.access(expanded, os.R_OK):
        return False, f"Permission denied: cannot read {expanded}"

    # Try to parse as kubeconfig
    try:
        from kubernetes import config
        config.load_kube_config(config_file=expanded)
        return True, "Valid kubeconfig"
    except Exception as e:
        return False, f"Invalid kubeconfig: {e}"


if __name__ == "__main__":
    # Test the config manager
    cm = get_config_manager()
    print(f"Config file: {cm.CONFIG_FILE}")

    # Test kubeconfig resolution
    path = resolve_kubeconfig_path()
    print(f"Resolved kubeconfig: {path}")

    path = resolve_kubeconfig_path("/nonexistent/path")
    print(f"Invalid path result: {path}")