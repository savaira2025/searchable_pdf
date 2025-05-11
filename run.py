#!/usr/bin/env python3
"""
Run script for the Searchable PDF Library.
This script provides a simple way to start the API server or run the CLI.
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path

def main():
    """Main entry point for the run script."""
    parser = argparse.ArgumentParser(description="Run the Searchable PDF Library")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # API server command
    api_parser = subparsers.add_parser("api", help="Start the API server")
    api_parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    api_parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    api_parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    
    # CLI command
    cli_parser = subparsers.add_parser("cli", help="Run the CLI")
    cli_parser.add_argument("cli_args", nargs="*", help="Arguments to pass to the CLI")
    
    # Web command
    web_parser = subparsers.add_parser("web", help="Start the API server and open the web interface")
    web_parser.add_argument("--host", default="localhost", help="Host to bind to")
    web_parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    
    # Parse arguments
    args = parser.parse_args()
    
    # Execute command
    if args.command == "api":
        run_api_server(args.host, args.port, args.reload)
    elif args.command == "cli":
        run_cli(args.cli_args)
    elif args.command == "web":
        run_web_interface(args.host, args.port)
    else:
        parser.print_help()

def run_api_server(host, port, reload):
    """Start the API server."""
    print(f"Starting API server at http://{host}:{port}")
    
    # Build command
    cmd = [
        sys.executable, "-m", "uvicorn", "main:app",
        "--host", host,
        "--port", str(port)
    ]
    
    if reload:
        cmd.append("--reload")
    
    # Run command
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\nAPI server stopped")

def run_cli(cli_args):
    """Run the CLI with the specified arguments."""
    # Build command
    cmd = [sys.executable, "cli.py"] + cli_args
    
    # Run command
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\nCLI execution stopped")

def run_web_interface(host, port):
    """Start the API server and open the web interface."""
    import webbrowser
    import threading
    import time
    
    # Start API server in a separate thread
    server_thread = threading.Thread(
        target=run_api_server,
        args=(host, port, False),
        daemon=True
    )
    server_thread.start()
    
    # Wait for the server to start
    print("Waiting for the API server to start...")
    time.sleep(2)
    
    # Open web interface in browser
    url = f"http://{host}:{port}"
    print(f"Opening web interface at {url}")
    webbrowser.open(url)
    
    # Keep the main thread running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nWeb interface stopped")

if __name__ == "__main__":
    # Change to the script's directory
    os.chdir(Path(__file__).parent)
    
    # Run the script
    main()
