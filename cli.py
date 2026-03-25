"""
CLI Module for K3s-Sentinel.

Provides command-line interface with kubeconfig browser using textual TUI.
"""

import os
import sys
import argparse
from pathlib import Path
from typing import Optional, List, Tuple

from textual.app import App, ComposeResult
from textual.containers import Container, VerticalScroll, HorizontalScroll
from textual.widgets import Header, Footer, Tree, Button, Static, Input, DirectoryTree
from textual.widgets.tree import TreeNode
from textual import on
from textual.events import Key

from config_manager import (
    get_config_manager,
    resolve_kubeconfig_path,
    validate_kubeconfig_path,
    ConfigManager
)


class KubeconfigBrowser(App):
    """
    Interactive kubeconfig file browser using textual TUI.

    Allows users to navigate the filesystem and select a kubeconfig file.
    """

    CSS = """
    Screen {
        background: $surface;
    }

    #browser-container {
        height: 100%;
        padding: 1;
    }

    #info-panel {
        height: 3;
        background: $primary;
        padding: 1 2;
        content-align: center middle;
    }

    #instructions {
        height: 3;
        background: $surface-darken-1;
        padding: 1 2;
        content-align: center middle;
    }

    DirectoryTree {
        height: 1fr;
        border: solid $primary;
    }

    #status-bar {
        height: 3;
        background: $surface-darken-2;
        padding: 1 2;
    }

    Button {
        margin: 1;
    }

    #button-container {
        height: auto;
        align: center middle;
        padding: 1;
    }
    """

    BINDINGS = [
        ("escape", "cancel", "Cancel"),
        ("enter", "select", "Select"),
        ("q", "quit", "Quit"),
    ]

    def __init__(self, initial_path: Optional[str] = None):
        """Initialize the browser."""
        super().__init__()
        self.config_manager = get_config_manager()
        self.selected_path: Optional[str] = None
        self.initial_path = initial_path or str(Path.home())

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield Header()

        with Container(id="browser-container"):
            yield Static("Select a kubeconfig file:", id="info-panel")
            yield DirectoryTree(self.initial_path, id="dir-tree")
            yield Static(
                "Navigate: ↑↓  |  Select: Enter  |  Cancel: Esc  |  Quit: q",
                id="instructions"
            )

        yield Footer()

    def on_mount(self) -> None:
        """Handle mount event."""
        tree = self.query_one("#dir-tree", DirectoryTree)
        tree.focus()

    @on(DirectoryTree.FileSelected)
    def on_file_selected(self, event: DirectoryTree.FileSelected) -> None:
        """Handle file selection."""
        self.selected_path = str(event.path)
        self.exit(result=self.selected_path)

    @on(DirectoryTree.DirectorySelected)
    def on_directory_selected(self, event: DirectoryTree.DirectorySelected) -> None:
        """Handle directory selection."""
        pass

    def action_cancel(self) -> None:
        """Cancel selection."""
        self.selected_path = None
        self.exit(result=None)

    def action_select(self) -> None:
        """Confirm selection."""
        tree = self.query_one("#dir-tree", DirectoryTree)
        selected = tree.cursor_node
        if selected and selected.data:
            self.selected_path = str(selected.data.path)
            self.exit(result=self.selected_path)


class PathValidator:
    """Validates and displays kubeconfig path information."""

    def __init__(self, path: str):
        """Initialize with path to validate."""
        self.path = path
        self.is_valid = False
        self.message = ""
        self.cluster_name: Optional[str] = None
        self.contexts: List[str] = []
        self._validate()

    def _validate(self) -> None:
        """Perform validation."""
        is_valid, message = validate_kubeconfig_path(self.path)
        self.is_valid = is_valid
        self.message = message

        if is_valid:
            self._load_info()

    def _load_info(self) -> None:
        """Load additional kubeconfig info."""
        try:
            from kubernetes import config
            contexts, current_context = config.list_kube_config_contexts(
                config_file=self.path
            )
            self.contexts = [c["name"] for c in contexts]
            self.cluster_name = current_context
        except Exception as e:
            self.message = f"Warning: Could not load context info: {e}"


class CLI:
    """
    Command-line interface for K3s-Sentinel.

    Handles argument parsing and coordinates between CLI and TUI modes.
    """

    def __init__(self):
        """Initialize CLI."""
        self.config_manager = get_config_manager()
        self.parser = self._create_parser()

    def _create_parser(self) -> argparse.ArgumentParser:
        """Create argument parser."""
        parser = argparse.ArgumentParser(
            prog="k3s-sentinel",
            description="K3s-Sentinel - AI Agent for K3s Cluster Root Cause Analysis",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  k3s-sentinel                    # Start with TUI (auto-detect kubeconfig)
  k3s-sentinel --kubeconfig /path/to/config  # Use specific kubeconfig
  k3s-sentinel --browser          # Force interactive kubeconfig browser
  k3s-sentinel --tui              # Start full TUI interface
  k3s-sentinel --api              # Start API server only
            """
        )

        parser.add_argument(
            "--kubeconfig", "-k",
            metavar="PATH",
            help="Path to kubeconfig file"
        )

        parser.add_argument(
            "--browser", "-b",
            action="store_true",
            help="Open interactive kubeconfig file browser"
        )

        parser.add_argument(
            "--tui", "-t",
            action="store_true",
            help="Start the full TUI interface"
        )

        parser.add_argument(
            "--api",
            action="store_true",
            help="Start API server only (no TUI)"
        )

        parser.add_argument(
            "--context", "-c",
            metavar="NAME",
            help="Kubernetes context to use"
        )

        parser.add_argument(
            "--namespace", "-n",
            metavar="NAME",
            default="default",
            help="Default namespace to query (default: default)"
        )

        parser.add_argument(
            "--refresh", "-r",
            type=int,
            metavar="SECONDS",
            help="Refresh interval for TUI (default: 30)"
        )

        parser.add_argument(
            "--theme",
            choices=["dark", "light"],
            default="dark",
            help="UI theme (default: dark)"
        )

        parser.add_argument(
            "--debug",
            action="store_true",
            help="Enable debug logging"
        )

        parser.add_argument(
            "--version", "-v",
            action="version",
            version="%(prog)s 1.0.0"
        )

        return parser

    def resolve_kubeconfig(self, cli_path: Optional[str] = None) -> Tuple[Optional[str], bool]:
        """
        Resolve kubeconfig path with optional browser fallback.

        Args:
            cli_path: Path from CLI argument

        Returns:
            Tuple of (resolved_path, used_browser)
        """
        # Try direct resolution first
        resolved = resolve_kubeconfig_path(cli_path)
        if resolved:
            return resolved, False

        # Try saved config path
        saved_path = self.config_manager.get_kubeconfig_path()
        if saved_path:
            is_valid, _ = validate_kubeconfig_path(saved_path)
            if is_valid:
                return saved_path, False

        # No valid path found, user needs to specify
        if cli_path:
            print(f"Error: Invalid kubeconfig path: {cli_path}", file=sys.stderr)
            sys.exit(1)

        return None, False

    def run_browser(self, initial_path: Optional[str] = None) -> Optional[str]:
        """
        Run interactive kubeconfig browser.

        Args:
            initial_path: Initial directory to display

        Returns:
            Selected path or None if cancelled
        """
        app = KubeconfigBrowser(initial_path)
        return app.run()

    def print_status(self, kubeconfig_path: Optional[str]) -> None:
        """Print kubeconfig status information."""
        if not kubeconfig_path:
            print("No kubeconfig selected.")
            return

        validator = PathValidator(kubeconfig_path)
        print(f"Kubeconfig: {kubeconfig_path}")
        print(f"Status: {validator.message}")

        if validator.contexts:
            print(f"Contexts ({len(validator.contexts)}):")
            for ctx in validator.contexts[:5]:
                marker = " *" if ctx == validator.cluster_name else ""
                print(f"  - {ctx}{marker}")
            if len(validator.contexts) > 5:
                print(f"  ... and {len(validator.contexts) - 5} more")

    def execute(self, args: Optional[List[str]] = None) -> int:
        """
        Execute CLI with given arguments.

        Args:
            args: Command-line arguments (uses sys.argv if None)

        Returns:
            Exit code
        """
        parsed = self.parser.parse_args(args)

        # Handle --browser flag
        if parsed.browser:
            result = self.run_browser()
            if result:
                self.config_manager.set_kubeconfig_path(result)
                print(f"Selected: {result}")
            return 0

        # Resolve kubeconfig
        kubeconfig_path, used_browser = self.resolve_kubeconfig(parsed.kubeconfig)

        # If --browser was implicitly needed but not specified
        if not kubeconfig_path and not parsed.tui and not parsed.api:
            print("No valid kubeconfig found. Opening browser...")
            result = self.run_browser()
            if result:
                kubeconfig_path = result
                self.config_manager.set_kubeconfig_path(result)
            else:
                print("No kubeconfig selected.", file=sys.stderr)
                return 1

        # Save selected path
        if kubeconfig_path:
            self.config_manager.set_kubeconfig_path(kubeconfig_path)
            if parsed.debug:
                self.print_status(kubeconfig_path)

        # Save context if specified
        if parsed.context:
            self.config_manager.set_last_context(parsed.context)

        # Save UI preferences
        if parsed.theme:
            self.config_manager.set_ui_theme(parsed.theme)

        if parsed.refresh:
            self.config_manager.set_refresh_interval(parsed.refresh)

        # Determine what to run
        if parsed.api:
            # Run API server only
            return self.run_api(kubeconfig_path, parsed)
        elif parsed.tui:
            # Run full TUI
            return self.run_tui(kubeconfig_path, parsed)
        else:
            # Default: run TUI
            return self.run_tui(kubeconfig_path, parsed)

    def run_api(self, kubeconfig_path: Optional[str], args) -> int:
        """Run API server."""
        from api_server import load_kubeconfig
        if kubeconfig_path:
            load_kubeconfig(kubeconfig_path)
            print(f"Connected to cluster with kubeconfig: {kubeconfig_path}")

        # Import and run uvicorn
        import uvicorn
        from api_server import app

        print("Starting API server on http://0.0.0.0:8000")
        uvicorn.run(app, host="0.0.0.0", port=8000)
        return 0

    def run_tui(self, kubeconfig_path: Optional[str], args) -> int:
        """Run full TUI."""
        # Import here to avoid circular imports and textual import issues
        try:
            from tui import K3sSentinelTUI
            app = K3sSentinelTUI(
                kubeconfig_path=kubeconfig_path,
                default_namespace=args.namespace,
                refresh_interval=args.refresh or self.config_manager.get_refresh_interval(),
                theme=args.theme
            )
            app.run()
            return 0
        except ImportError as e:
            print(f"Error: TUI not available: {e}", file=sys.stderr)
            print("Make sure textual is installed: pip install textual", file=sys.stderr)
            return 1


def main():
    """Main entry point."""
    cli = CLI()
    return cli.execute()


if __name__ == "__main__":
    sys.exit(main())