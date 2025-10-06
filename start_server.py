#!/usr/bin/env python3
"""
Simple server startup script for DALS
=====================================

This script provides a simple way to start the Digital Asset Logistics System
server without dealing with module complexities.
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from iss_module.service import create_app
    import uvicorn

    def main():
        print("Creating DALS application...")
        app = create_app()
        print(f"App created with {len(app.routes)} routes")
        print("Starting server on http://127.0.0.1:8003")
        print("Press Ctrl+C to stop the server")
        uvicorn.run(app, host="127.0.0.1", port=8003)

    if __name__ == "__main__":
        main()

except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure all dependencies are installed:")
    print("pip install -r requirements.txt")
    sys.exit(1)

except Exception as e:
    print(f"Error starting server: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)