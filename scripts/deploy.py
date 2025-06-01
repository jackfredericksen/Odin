#!/usr/bin/env python3
"""Deployment script for Odin trading bot."""

import os
import subprocess
import sys
from pathlib import Path

def run_command(command: list, description: str) -> bool:
    """Run a command and return success status."""
    print(f"🔄 {description}...")
    try:
        subprocess.run(command, check=True)
        print(f"✅ {description} completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        return False

def main():
    """Main deployment function."""
    print("🚀 Deploying Odin Trading Bot")
    print("=" * 30)
    
    # Pre-deployment checks
    print("🔍 Running pre-deployment checks...")
    
    checks = [
        (["python", "-m", "pytest", "tests/", "-x"], "Running tests"),
        (["docker", "build", "-t", "odin-trading-bot:latest", "."], "Building Docker image"),
    ]
    
    for command, description in checks:
        if not run_command(command, description):
            print("❌ Pre-deployment checks failed")
            sys.exit(1)
    
    print("✅ All pre-deployment checks passed")
    
    # Deploy
    deploy_commands = [
        (["docker-compose", "down"], "Stopping existing containers"),
        (["docker-compose", "up", "-d"], "Starting new containers"),
    ]
    
    for command, description in deploy_commands:
        if not run_command(command, description):
            print(f"❌ Deployment failed at: {description}")
            sys.exit(1)
    
    print("\n🎉 Deployment completed successfully!")
    print("🌐 Application should be available at: http://localhost:5000")

if __name__ == "__main__":
    main()