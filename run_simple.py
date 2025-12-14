"""
Simple Odin startup script that bypasses complex initialization
"""
import uvicorn
from odin.api.app import create_app

if __name__ == "__main__":
    print("\n" + "="*60)
    print("   ODIN BITCOIN TRADING BOT")
    print("   Simple Startup Mode")
    print("="*60 + "\n")

    print("Creating FastAPI application...")
    app = create_app()

    print("\nStarting server...")
    print("Dashboard: http://localhost:8000")
    print("API Docs: http://localhost:8000/docs")
    print("\nPress Ctrl+C to stop\n")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
