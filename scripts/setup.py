#!/usr/bin/env python3
"""Setup script for Odin trading bot development environment."""

import os
import subprocess
import sys
from pathlib import Path

def run_command(command: list, description: str) -> bool:
    """Run a command and return success status."""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e.stderr}")
        return False

def main():
    """Main setup function."""
    print("🚀 Setting up Odin Trading Bot development environment")
    print("=" * 60)
    
    # Check Python version
    if sys.version_info < (3, 11):
        print("❌ Python 3.11 or higher is required")
        sys.exit(1)
    
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    
    # Create necessary directories
    directories = ["data", "logs", "web/static/css", "web/static/js", "web/static/images"]
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"📁 Created directory: {directory}")
    
    # Copy environment file
    if not Path(".env").exists():
        if Path(".env.example").exists():
            subprocess.run(["cp", ".env.example", ".env"])
            print("📄 Created .env file from .env.example")
        else:
            print("⚠️  .env.example not found, skipping .env creation")
    
    # Install dependencies
    commands = [
        (["pip", "install", "--upgrade", "pip"], "Upgrading pip"),
        (["pip", "install", "-r", "requirements-dev.txt"], "Installing development dependencies"),
        (["pre-commit", "install"], "Setting up pre-commit hooks"),
    ]
    
    for command, description in commands:
        if not run_command(command, description):
            print(f"⚠️  {description} failed, continuing...")
    
    # Initialize database
    print("🔄 Initializing database...")
    try:
        from odin.core.database import init_database
        import asyncio
        asyncio.run(init_database())
        print("✅ Database initialized")
    except Exception as e:
        print(f"⚠️  Database initialization failed: {e}")
    
    print("\n🎉 Setup completed!")
    print("\nNext steps:")
    print("1. Review and update .env file with your settings")
    print("2. Run tests: pytest tests/")
    print("3. Start the application: python -m odin.main")
    print("4. Access the dashboard: http://localhost:5000")

if __name__ == "__main__":
    main()

# scripts/migrate.py
#!/usr/bin/env python3
"""Database migration script for Odin trading bot."""

import asyncio
import sys
from pathlib import Path

async def migrate_database():
    """Run database migrations."""
    print("🔄 Running database migrations...")
    
    try:
        from odin.core.database import init_database
        await init_database()
        print("✅ Database migrations completed")
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        sys.exit(1)

def main():
    """Main migration function."""
    print("🚀 Odin Trading Bot - Database Migration")
    print("=" * 40)
    
    asyncio.run(migrate_database())

if __name__ == "__main__":
    main()