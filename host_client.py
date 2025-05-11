#!/usr/bin/env python3
"""
Simple HTTP server to host the client application.
"""

import http.server
import socketserver
import os
import webbrowser
import socket
import time

# Configuration
DIRECTORY = "client"
# Try ports in this range
START_PORT = 8000
END_PORT = 9000

class Handler(http.server.SimpleHTTPRequestHandler):
    """Custom handler to serve files from the client directory."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

def find_available_port(start_port, end_port):
    """Find an available port in the given range."""
    for port in range(start_port, end_port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('', port))
                return port
            except OSError:
                continue
    raise RuntimeError(f"No available ports in range {start_port}-{end_port}")

def main():
    """Start the HTTP server and open the browser."""
    # Change to the script directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    # Create the client directory if it doesn't exist
    os.makedirs(DIRECTORY, exist_ok=True)

    # Find an available port
    try:
        port = find_available_port(START_PORT, END_PORT)
        print(f"Found available port: {port}")
    except RuntimeError as e:
        print(f"Error: {e}")
        return

    # Start the server
    try:
        httpd = socketserver.TCPServer(("", port), Handler)
        print(f"Serving at http://localhost:{port}")
        print(f"Press Ctrl+C to stop the server")

        # Open the browser
        webbrowser.open(f"http://localhost:{port}")

        # Serve until interrupted
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped")
    except Exception as e:
        print(f"Error starting server: {e}")

if __name__ == "__main__":
    main()
