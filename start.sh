#!/bin/bash

# ============================================
# K3s-Sentinel Unified Start Script
# ============================================
# This script starts the K3s-Sentinel agent with all components.
# Configuration is loaded from .env file.
#
# Usage:
#   ./start.sh              # Start all services
#   ./start.sh --backend    # Start only backend API
#   ./start.sh --frontend   # Start only frontend dashboard
#   ./start.sh --help       # Show help
#
# Endpoints:
#   - Backend API:  http://localhost:8000
#   - API Docs:     http://localhost:8000/docs
#   - Dashboard:    http://localhost:3000
# ============================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
START_BACKEND=true
START_FRONTEND=true
MODE="all"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="${SCRIPT_DIR}/logs"
PID_DIR="${SCRIPT_DIR}/pids"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --backend)
            START_FRONTEND=false
            MODE="backend"
            shift
            ;;
        --frontend)
            START_BACKEND=false
            MODE="frontend"
            shift
            ;;
        --help|-h)
            echo "K3s-Sentinel Start Script"
            echo ""
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --backend    Start only the backend API server"
            echo "  --frontend   Start only the frontend dashboard"
            echo "  --help       Show this help message"
            echo ""
            echo "Endpoints (when started with default settings):"
            echo "  - Backend API:  http://localhost:8000"
            echo "  - API Docs:     http://localhost:8000/docs"
            echo "  - Dashboard:    http://localhost:3000"
            echo ""
            echo "Configuration:"
            echo "  Edit .env file to customize settings"
            echo ""
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Print banner
print_banner() {
    echo -e "${BLUE}"
    echo "  ███████╗██╗   ██╗███╗   ███╗██╗███╗   ██╗██╗   ██╗███████╗"
    echo "  ██╔════╝╚██╗ ██╔╝████╗ ████║██║████╗  ██║██║   ██║██╔════╝"
    echo "  ███████╗ ╚████╔╝ ██╔████╔██║██║██╔██╗ ██║██║   ██║███████╗"
    echo "  ╚════██║  ╚██╔╝  ██║╚██╔╝██║██║██║╚██╗██║██║   ██║╚════██║"
    echo "  ███████║   ██║   ██║ ╚═╝ ██║██║██║ ╚████║╚██████╔╝███████║"
    echo "  ╚══════╝   ╚═╝   ╚═╝     ╚═╝╚═╝╚═╝  ╚═══╝ ╚═════╝ ╚══════╝"
    echo -e "${NC}"
    echo -e "${GREEN}K3s Cluster Root Cause Analysis Agent${NC}"
    echo ""
}

# Create necessary directories
setup_directories() {
    mkdir -p "${LOG_DIR}"
    mkdir -p "${PID_DIR}"
    mkdir -p "${SCRIPT_DIR}/data"
    mkdir -p "${SCRIPT_DIR}/config"
}

# Load environment variables
load_env() {
    local env_file="${SCRIPT_DIR}/.env"

    if [ -f "${env_file}" ]; then
        echo -e "${YELLOW}Loading configuration from .env file...${NC}"
        set -a
        source "${env_file}"
        set +a
    else
        echo -e "${YELLOW}Warning: .env file not found. Using default configuration.${NC}"
        echo -e "${YELLOW}Copy .env.example to .env and customize your settings.${NC}"
        echo ""
    fi

    # Set defaults if not defined
    : "${BACKEND_API_URL:=http://localhost:8000}"
    : "${DASHBOARD_PORT:=3000}"
    : "${LLM_PROVIDER:=openai}"
    : "${LOG_LEVEL:=INFO}"
}

# Check Python version
check_python() {
    echo -e "${YELLOW}Checking Python version...${NC}"

    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}Error: Python 3 is not installed.${NC}"
        exit 1
    fi

    python_version=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1)
    if [ "$python_version" -lt 3 ]; then
        echo -e "${RED}Error: Python 3.9+ required. Found Python $python_version${NC}"
        exit 1
    fi

    echo -e "${GREEN}Python $python_version detected${NC}"
}

# Install dependencies
install_deps() {
    echo -e "${YELLOW}Checking dependencies...${NC}"

    # Check if requirements.txt exists
    if [ -f "${SCRIPT_DIR}/requirements.txt" ]; then
        # Check if pip packages are installed
        if ! python3 -c "import fastapi" &> /dev/null; then
            echo -e "${YELLOW}Installing Python dependencies...${NC}"
            pip install -q -r "${SCRIPT_DIR}/requirements.txt"
        fi
    fi

    # Check for kubectl
    if ! command -v kubectl &> /dev/null; then
        echo -e "${YELLOW}Warning: kubectl not found. Install for full cluster integration.${NC}"
    fi

    echo -e "${GREEN}Dependencies ready${NC}"
}

# Start backend API server
start_backend() {
    echo -e "${YELLOW}Starting K3s-Sentinel Backend API...${NC}"

    local backend_log="${LOG_DIR}/backend.log"
    local backend_pid="${PID_DIR}/backend.pid"

    # Check if already running
    if [ -f "${backend_pid}" ]; then
        local old_pid=$(cat "${backend_pid}")
        if kill -0 "${old_pid}" 2>/dev/null; then
            echo -e "${YELLOW}Backend API already running (PID: ${old_pid})${NC}"
            return 0
        fi
    fi

    # Start the backend
    cd "${SCRIPT_DIR}"

    # Create a simple .env loader for Python
    cat > "${SCRIPT_DIR}/_env_loader.py" << 'ENVLOADER'
import os
import sys

# Load .env file if exists
env_file = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(env_file):
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()

# Add sentinel path
sys.path.insert(0, os.path.dirname(__file__))
ENVLOADER

    nohup python3 -c "import sys; sys.path.insert(0, '${SCRIPT_DIR}'); exec(open('${SCRIPT_DIR}/_env_loader.py').read()); from api_server import app; import uvicorn; uvicorn.run(app, host='0.0.0.0', port=8000, log_level='${LOG_LEVEL:-info}')" > "${backend_log}" 2>&1 &
    local pid=$!

    echo $pid > "${backend_pid}"
    echo -e "${GREEN}Backend API started (PID: ${pid})${NC}"
    echo -e "${GREEN}  - API URL:     http://localhost:8000${NC}"
    echo -e "${GREEN}  - API Docs:    http://localhost:8000/docs${NC}"
    echo -e "${GREEN}  - Log file:    ${backend_log}${NC}"

    # Wait a moment for the server to start
    sleep 2

    # Check if server is running
    if ! kill -0 "${pid}" 2>/dev/null; then
        echo -e "${RED}Error: Backend API failed to start. Check log: ${backend_log}${NC}"
        cat "${backend_log}"
        exit 1
    fi

    echo ""
}

# Start frontend dashboard
start_frontend() {
    echo -e "${YELLOW}Starting K3s-Sentinel Dashboard...${NC}"

    local frontend_log="${LOG_DIR}/frontend.log"
    local frontend_pid="${PID_DIR}/frontend.pid"

    # Check if already running
    if [ -f "${frontend_pid}" ]; then
        local old_pid=$(cat "${frontend_pid}")
        if kill -0 "${old_pid}" 2>/dev/null; then
            echo -e "${YELLOW}Dashboard already running (PID: ${old_pid})${NC}"
            return 0
        fi
    fi

    # Check if dist folder exists
    local dist_path="${SCRIPT_DIR}/dashboard/dist"
    if [ ! -d "${dist_path}" ]; then
        echo -e "${YELLOW}Dashboard dist folder not found. Building...${NC}"
        cd "${SCRIPT_DIR}/dashboard"
        if command -v pnpm &> /dev/null; then
            pnpm build
        elif command -v npm &> /dev/null; then
            npm run build
        else
            echo -e "${RED}Error: Neither pnpm nor npm found. Cannot build dashboard.${NC}"
            return 1
        fi
        cd "${SCRIPT_DIR}"
    fi

    # Create a simple static file server for the dashboard
    # Using Python's built-in http.server
    cd "${dist_path}"

    nohup python3 -m http.server "${DASHBOARD_PORT:-3000}" --bind 0.0.0.0 > "${frontend_log}" 2>&1 &
    local pid=$!

    cd "${SCRIPT_DIR}"

    echo $pid > "${frontend_pid}"
    echo -e "${GREEN}Dashboard started (PID: ${pid})${NC}"
    echo -e "${GREEN}  - Dashboard:  http://localhost:${DASHBOARD_PORT:-3000}${NC}"
    echo -e "${GREEN}  - Log file:   ${frontend_log}${NC}"

    # Wait a moment for the server to start
    sleep 2

    # Check if server is running
    if ! kill -0 "${pid}" 2>/dev/null; then
        echo -e "${RED}Error: Dashboard failed to start. Check log: ${frontend_log}${NC}"
        cat "${frontend_log}"
        exit 1
    fi

    echo ""
}

# Stop all services
stop_all() {
    echo -e "${YELLOW}Stopping K3s-Sentinel...${NC}"

    # Stop backend
    if [ -f "${PID_DIR}/backend.pid" ]; then
        local pid=$(cat "${PID_DIR}/backend.pid")
        if kill -0 "${pid}" 2>/dev/null; then
            kill "${pid}"
            echo -e "${GREEN}Backend API stopped${NC}"
        fi
        rm -f "${PID_DIR}/backend.pid"
    fi

    # Stop frontend
    if [ -f "${PID_DIR}/frontend.pid" ]; then
        local pid=$(cat "${PID_DIR}/frontend.pid")
        if kill -0 "${pid}" 2>/dev/null; then
            kill "${pid}"
            echo -e "${GREEN}Dashboard stopped${NC}"
        fi
        rm -f "${PID_DIR}/frontend.pid"
    fi

    echo -e "${GREEN}All services stopped${NC}"
}

# Show status
show_status() {
    echo "K3s-Sentinel Status"
    echo "==================="
    echo ""

    # Backend status
    if [ -f "${PID_DIR}/backend.pid" ]; then
        local pid=$(cat "${PID_DIR}/backend.pid")
        if kill -0 "${pid}" 2>/dev/null; then
            echo -e "${GREEN}● Backend API:   Running (PID: ${pid})${NC}"
            echo "  → http://localhost:8000"
            echo "  → http://localhost:8000/docs"
        else
            echo -e "${RED}● Backend API:   Not running (stale PID file)${NC}"
        fi
    else
        echo -e "${YELLOW}● Backend API:   Not running${NC}"
    fi

    # Frontend status
    if [ -f "${PID_DIR}/frontend.pid" ]; then
        local pid=$(cat "${PID_DIR}/frontend.pid")
        if kill -0 "${pid}" 2>/dev/null; then
            echo -e "${GREEN}● Dashboard:     Running (PID: ${pid})${NC}"
            echo "  → http://localhost:${DASHBOARD_PORT:-3000}"
        else
            echo -e "${RED}● Dashboard:     Not running (stale PID file)${NC}"
        fi
    else
        echo -e "${YELLOW}● Dashboard:     Not running${NC}"
    fi

    echo ""
}

# Print usage info
print_usage() {
    echo ""
    echo -e "${GREEN}K3s-Sentinel is now running!${NC}"
    echo ""
    echo "Endpoints:"
    if [ "$START_BACKEND" = true ]; then
        echo -e "  ${BLUE}• Backend API:${NC}   http://localhost:8000"
        echo -e "  ${BLUE}• API Docs:${NC}      http://localhost:8000/docs"
    fi
    if [ "$START_FRONTEND" = true ]; then
        echo -e "  ${BLUE}• Dashboard:${NC}     http://localhost:${DASHBOARD_PORT:-3000}"
    fi
    echo ""
    echo "Configuration:"
    echo "  • Edit .env file to customize settings"
    echo "  • API keys and alerts can be configured there"
    echo ""
    echo "To stop:"
    echo "  ./start.sh --stop"
    echo ""
    echo "To restart:"
    echo "  ./start.sh --restart"
    echo ""
}

# Cleanup function
cleanup() {
    echo ""
    echo -e "${YELLOW}Received shutdown signal. Stopping services...${NC}"
    stop_all
    exit 0
}

# Register cleanup handler
trap cleanup SIGINT SIGTERM

# Main execution
main() {
    print_banner
    setup_directories
    load_env
    check_python
    install_deps

    if [ "$START_BACKEND" = true ]; then
        start_backend
    fi

    if [ "$START_FRONTEND" = true ]; then
        start_frontend
    fi

    print_usage

    # Wait for services
    echo -e "${YELLOW}Press Ctrl+C to stop all services${NC}"
    echo ""

    # Keep the script running
    while true; do
        sleep 1
    done
}

# Run main function
main
