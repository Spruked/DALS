#!/usr/bin/env python3
"""
Direct server startup for Digital Asset Logistics System (DALS)
"""

import sys
import os

# Add current directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def main():
    try:
        print("🚀 Starting Digital Asset Logistics System (DALS)...")
        from iss_module.api.api import app
        print("✓ App imported successfully")
        print(f"✓ App has {len(app.routes)} routes")

        import uvicorn
        print("✓ Starting server on http://127.0.0.1:8003")
        print("✓ Press Ctrl+C to stop the server")
        print()

        uvicorn.run(app, host='127.0.0.1', port=8003, log_level='info')

    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"✗ Error starting server: {e}")
        import traceback
        traceback.print_exc()
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()