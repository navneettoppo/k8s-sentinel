"""
K3s-Sentinel: AI Agent for K3s Cluster Root Cause Analysis

This module provides the main entry point for the K3s-Sentinel agent.
"""

import asyncio
import logging
import signal
import sys
import argparse
from typing import Optional
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent.telemetry_collector import TelemetryCollector
from agent.context_engine import ContextEngine
from agent.analysis_core import AnalysisCore
from agent.alert_handlers import AlertDispatcher
from config.settings import Settings


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        prog="k3s-sentinel",
        description="K3s-Sentinel - AI Agent for K3s Cluster Root Cause Analysis"
    )

    parser.add_argument(
        "--kubeconfig", "-k",
        metavar="PATH",
        help="Path to kubeconfig file"
    )

    parser.add_argument(
        "--tui", "-t",
        action="store_true",
        help="Start the full TUI interface"
    )

    parser.add_argument(
        "--api",
        action="store_true",
        help="Start API server only"
    )

    parser.add_argument(
        "--context", "-c",
        metavar="NAME",
        help="Kubernetes context to use"
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )

    return parser.parse_args()


class K3sSentinelAgent:
    """
    Main AI Agent class for K3s cluster root cause analysis.

    This agent monitors K3s cluster health, builds dependency graphs,
    detects anomalies, and uses AI to trace symptoms back to root causes.
    """

    def __init__(self, config_path: Optional[str] = None):
        """Initialize the K3s-Sentinel agent with configuration."""
        self.logger = logging.getLogger(__name__)
        self.settings = Settings(config_path)

        # Initialize components
        self.telemetry_collector: Optional[TelemetryCollector] = None
        self.context_engine: Optional[ContextEngine] = None
        self.analysis_core: Optional[AnalysisCore] = None
        self.alert_dispatcher: Optional[AlertDispatcher] = None

        self.is_running = False
        self._setup_logging()

    def _setup_logging(self):
        """Configure logging for the agent."""
        logging.basicConfig(
            level=getattr(logging, self.settings.log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler(self.settings.log_file) if self.settings.log_file else logging.NullHandler()
            ]
        )
        self.logger.info("K3s-Sentinel Agent initialized")

    async def start(self):
        """Start the K3s-Sentinel agent and all its components."""
        self.logger.info("Starting K3s-Sentinel Agent...")
        self.is_running = True

        try:
            # Initialize components in order
            self.logger.info("Initializing Context Engine...")
            self.context_engine = ContextEngine(self.settings)
            await self.context_engine.initialize()

            self.logger.info("Initializing Telemetry Collector...")
            self.telemetry_collector = TelemetryCollector(self.settings)
            await self.telemetry_collector.start()

            self.logger.info("Initializing Analysis Core...")
            self.analysis_core = AnalysisCore(self.settings, self.context_engine)
            await self.analysis_core.initialize()

            self.logger.info("Initializing Alert Dispatcher...")
            self.alert_dispatcher = AlertDispatcher(self.settings)
            await self.alert_dispatcher.initialize()

            # Main event loop
            await self._main_loop()

        except Exception as e:
            self.logger.error(f"Error starting agent: {e}", exc_info=True)
            await self.stop()
            raise

    async def _main_loop(self):
        """Main event loop for processing cluster events."""
        self.logger.info("Entering main event loop...")

        while self.is_running:
            try:
                # Process collected telemetry
                events = await self.telemetry_collector.get_events()

                for event in events:
                    # Analyze event for potential issues
                    analysis_result = await self.analysis_core.analyze_event(event)

                    if analysis_result:
                        # Dispatch alert if root cause identified
                        await self.alert_dispatcher.dispatch(analysis_result)

                # Update topology graph periodically
                await self.context_engine.update_topology()

                # Wait before next iteration
                await asyncio.sleep(self.settings.poll_interval)

            except asyncio.CancelledError:
                self.logger.info("Agent cancelled")
                break
            except Exception as e:
                self.logger.error(f"Error in main loop: {e}", exc_info=True)
                await asyncio.sleep(5)  # Wait before retry

    async def stop(self):
        """Stop the K3s-Sentinel agent and cleanup resources."""
        self.logger.info("Stopping K3s-Sentinel Agent...")
        self.is_running = False

        if self.telemetry_collector:
            await self.telemetry_collector.stop()

        if self.alert_dispatcher:
            await self.alert_dispatcher.close()

        if self.context_engine:
            await self.context_engine.close()

        self.logger.info("K3s-Sentinel Agent stopped")

    def handle_signal(self, signum, frame):
        """Handle shutdown signals gracefully."""
        self.logger.info(f"Received signal {signum}, initiating shutdown...")
        asyncio.create_task(self.stop())


async def run_agent():
    """Run the K3s-Sentinel agent."""
    agent = K3sSentinelAgent()

    # Setup signal handlers
    signal.signal(signal.SIGINT, agent.handle_signal)
    signal.signal(signal.SIGTERM, agent.handle_signal)

    try:
        await agent.start()
    except KeyboardInterrupt:
        await agent.stop()
    except Exception as e:
        logging.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


def run_tui(kubeconfig_path: Optional[str] = None):
    """Run the TUI interface."""
    try:
        from tui import K3sSentinelTUI
        app = K3sSentinelTUI(kubeconfig_path=kubeconfig_path)
        app.run()
    except ImportError as e:
        print(f"Error: TUI not available: {e}", file=sys.stderr)
        print("Make sure textual is installed: pip install textual", file=sys.stderr)
        sys.exit(1)


def run_api_server(kubeconfig_path: Optional[str] = None):
    """Run the API server."""
    import uvicorn
    from api_server import app, load_kubeconfig

    if kubeconfig_path:
        load_kubeconfig(kubeconfig_path)
        print(f"Using kubeconfig: {kubeconfig_path}")

    print("Starting API server on http://0.0.0.0:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)


def main():
    """Main entry point for K3s-Sentinel."""
    args = parse_args()

    # Configure logging
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    # Import config manager for path resolution
    from config_manager import resolve_kubeconfig_path

    # Resolve kubeconfig path
    kubeconfig_path = resolve_kubeconfig_path(args.kubeconfig)

    if args.tui:
        # Run TUI
        run_tui(kubeconfig_path)
    elif args.api:
        # Run API server only
        run_api_server(kubeconfig_path)
    else:
        # Default: run the AI agent
        asyncio.run(run_agent())


if __name__ == "__main__":
    main()
