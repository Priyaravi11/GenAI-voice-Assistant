"""
Development server launcher for GenAI Voice Assistant.

Starts backend and frontend development servers with live reloading.
Handles environment setup, dependency checks, and process management.

Usage:
    python scripts/run_dev.py                # Start both servers
    python scripts/run_dev.py --backend-only # Backend only
    python scripts/run_dev.py --frontend-only # Frontend only
    python scripts/run_dev.py --port 8001    # Custom backend port
"""

import os
import sys
import subprocess
import time
import argparse
from pathlib import Path
from typing import Optional, List


class Colors:
    """Terminal color codes."""
    GREEN = '\033[92m'
    BLUE = '\033[94m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_header(message: str) -> None:
    """Print colored header message."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.GREEN}{message}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}\n")


def print_success(message: str) -> None:
    """Print success message."""
    print(f"{Colors.GREEN}✓ {message}{Colors.RESET}")


def print_error(message: str) -> None:
    """Print error message."""
    print(f"{Colors.RED}✗ {message}{Colors.RESET}")


def print_warning(message: str) -> None:
    """Print warning message."""
    print(f"{Colors.YELLOW}⚠ {message}{Colors.RESET}")


def print_info(message: str) -> None:
    """Print info message."""
    print(f"{Colors.BLUE}ℹ {message}{Colors.RESET}")


def check_python_version() -> bool:
    """Check Python version >= 3.11."""
    if sys.version_info < (3, 11):
        print_error(f"Python 3.11+ required. You have {sys.version}")
        return False
    print_success(f"Python {sys.version_info.major}.{sys.version_info.minor} ✓")
    return True


def check_env_file() -> bool:
    """Check if .env file exists."""
    env_path = Path(".env")
    if not env_path.exists():
        print_warning(".env file not found")
        print_info("Creating from .env.example...")
        
        env_example = Path(".env.example")
        if env_example.exists():
            with open(env_example) as src, open(env_path, "w") as dst:
                dst.write(src.read())
            print_success(".env created from .env.example")
            print_warning("Update .env with your actual configuration")
            return True
        else:
            print_error(".env.example not found")
            return False
    
    print_success(".env file found ✓")
    return True


def check_venv() -> bool:
    """Check if virtual environment is activated."""
    in_venv = hasattr(sys, 'real_prefix') or (
        hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
    )
    
    if not in_venv:
        print_warning("Virtual environment not activated")
        if sys.platform == "win32":
            print_info("Activate with: venv\\Scripts\\activate")
        else:
            print_info("Activate with: source venv/bin/activate")
        return False
    
    print_success("Virtual environment activated ✓")
    return True


def check_dependencies(requirements: str = "requirements.txt") -> bool:
    """Check if dependencies are installed."""
    req_path = Path(requirements)
    if not req_path.exists():
        print_warning(f"{requirements} not found")
        return False
    
    print_info("Checking Python dependencies...")
    
    # Try importing key dependencies
    try:
        import fastapi
        import uvicorn
        print_success("Backend dependencies installed ✓")
    except ImportError as e:
        print_error(f"Missing dependency: {e}")
        print_info("Install with: pip install -r requirements.txt")
        return False
    
    return True


def check_node_modules() -> bool:
    """Check if frontend dependencies are installed."""
    frontend_path = Path("frontend/node_modules")
    if not frontend_path.exists():
        print_warning("Frontend node_modules not found")
        print_info("Installing with: cd frontend && npm install")
        return False
    
    print_success("Frontend dependencies installed ✓")
    return True


def start_backend(port: int = 8000, reload: bool = True) -> Optional[subprocess.Popen]:
    """Start FastAPI backend server."""
    print_header(f"Starting Backend Server (port {port})")
    
    cmd = [
        sys.executable,
        "-m", "uvicorn",
        "backend.app.main:app",
        "--host", "0.0.0.0",
        "--port", str(port),
    ]
    
    if reload:
        cmd.append("--reload")
    
    print_info(f"Command: {' '.join(cmd)}")
    print_info("Backend server starting...")
    
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        print_success(f"Backend server started (PID: {process.pid})")
        return process
    except Exception as e:
        print_error(f"Failed to start backend: {e}")
        return None


def start_frontend() -> Optional[subprocess.Popen]:
    """Start Vite dev server for frontend."""
    print_header("Starting Frontend Server")
    
    frontend_dir = Path("frontend")
    if not frontend_dir.exists():
        print_error("frontend directory not found")
        return None
    
    cmd = ["npm", "run", "dev"]
    print_info(f"Command: {' '.join(cmd)}")
    print_info("Frontend server starting...")
    
    try:
        process = subprocess.Popen(
            cmd,
            cwd=str(frontend_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        print_success(f"Frontend server started (PID: {process.pid})")
        return process
    except Exception as e:
        print_error(f"Failed to start frontend: {e}")
        return None


def run_output(process: subprocess.Popen, label: str) -> None:
    """Run process output in background thread."""
    import threading
    
    def print_output():
        for line in process.stdout:
            if line:
                print(f"{Colors.BOLD}{label}{Colors.RESET} {line.rstrip()}")
    
    thread = threading.Thread(target=print_output, daemon=True)
    thread.start()


def wait_for_server(host: str = "127.0.0.1", port: int = 8000, timeout: int = 30) -> bool:
    """Wait for server to be ready."""
    import socket
    
    print_info(f"Waiting for server {host}:{port}...")
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            sock = socket.create_connection((host, port), timeout=1)
            sock.close()
            print_success(f"Server {host}:{port} is ready")
            return True
        except (socket.timeout, ConnectionRefusedError):
            time.sleep(0.5)
    
    print_warning(f"Server {host}:{port} not responding after {timeout}s")
    return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="GenAI Voice Assistant Development Server"
    )
    parser.add_argument(
        "--backend-only",
        action="store_true",
        help="Start only backend server"
    )
    parser.add_argument(
        "--frontend-only",
        action="store_true",
        help="Start only frontend server"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Backend server port (default: 8000)"
    )
    parser.add_argument(
        "--no-reload",
        action="store_true",
        help="Disable auto-reload for backend"
    )
    parser.add_argument(
        "--skip-checks",
        action="store_true",
        help="Skip environment checks"
    )
    
    args = parser.parse_args()
    
    # Change to project directory
    os.chdir(Path(__file__).parent.parent)
    
    # Print header
    print_header("GenAI Voice Assistant - Development Server")
    
    # Perform checks
    if not args.skip_checks:
        print_info("Running environment checks...")
        
        checks = [
            ("Python Version", check_python_version),
            ("Environment File", check_env_file),
            ("Virtual Environment", check_venv),
            ("Python Dependencies", check_dependencies),
        ]
        
        if not args.backend_only:
            checks.append(("Node Dependencies", check_node_modules))
        
        all_passed = True
        for check_name, check_func in checks:
            try:
                if not check_func():
                    all_passed = False
            except Exception as e:
                print_error(f"{check_name} check failed: {e}")
                all_passed = False
        
        if not all_passed:
            print_error("\nEnvironment checks failed. Fix issues above and try again.")
            return 1
    
    # Start servers
    processes: List[subprocess.Popen] = []
    
    try:
        if not args.frontend_only:
            backend_process = start_backend(
                port=args.port,
                reload=not args.no_reload
            )
            if backend_process:
                processes.append(backend_process)
                run_output(backend_process, "[BACKEND]")
                
                # Wait for backend to be ready
                wait_for_server("127.0.0.1", args.port)
        
        if not args.backend_only:
            time.sleep(1)  # Small delay before starting frontend
            frontend_process = start_frontend()
            if frontend_process:
                processes.append(frontend_process)
                run_output(frontend_process, "[FRONTEND]")
        
        # Print summary
        print_header("Development Servers Running")
        if not args.frontend_only:
            print_info(f"Backend:  http://localhost:{args.port}")
            print_info(f"API Docs: http://localhost:{args.port}/docs")
        if not args.backend_only:
            print_info("Frontend: http://localhost:5173 (or shown in console)")
        
        print_info("Press Ctrl+C to stop all servers")
        print()
        
        # Keep processes running
        if processes:
            for process in processes:
                process.wait()
        else:
            print_warning("No servers started")
            return 1
    
    except KeyboardInterrupt:
        print_header("Shutting Down Servers")
        for process in processes:
            if process.poll() is None:  # Still running
                print_info(f"Stopping process {process.pid}...")
                try:
                    process.terminate()
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
        print_success("All servers stopped")
    
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
