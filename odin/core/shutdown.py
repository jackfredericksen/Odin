"""
Odin Graceful Shutdown Manager

Handles graceful shutdown, port cleanup, and resource management to prevent
port conflicts and zombie processes.

Author: Odin Development Team
"""

import asyncio
import logging
import os
import signal
import sys
from typing import Optional

logger = logging.getLogger(__name__)


class ShutdownManager:
    """
    Manages graceful shutdown and cleanup of resources.

    Handles:
    - Signal handling (SIGTERM, SIGINT)
    - Port cleanup
    - Background task cancellation
    - Database connection cleanup
    """

    def __init__(self, port: int = 8000):
        self.port = port
        self.shutdown_event = asyncio.Event()
        self.cleanup_tasks = []
        self._signal_handlers_installed = False

    def install_signal_handlers(self):
        """Install signal handlers for graceful shutdown."""
        if self._signal_handlers_installed:
            return

        # Handle SIGTERM and SIGINT for graceful shutdown
        if sys.platform != "win32":
            signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)

        self._signal_handlers_installed = True
        logger.info("Signal handlers installed for graceful shutdown")

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        signal_name = signal.Signals(signum).name
        logger.info(f"Received {signal_name} signal, initiating graceful shutdown...")
        self.shutdown_event.set()

    def register_cleanup_task(self, cleanup_func):
        """
        Register a cleanup function to be called during shutdown.

        Args:
            cleanup_func: Async function to call during cleanup
        """
        self.cleanup_tasks.append(cleanup_func)
        logger.debug(f"Registered cleanup task: {cleanup_func.__name__}")

    async def cleanup(self):
        """Execute all registered cleanup tasks."""
        logger.info("Starting cleanup process...")

        # Run all cleanup tasks
        for task in self.cleanup_tasks:
            try:
                logger.debug(f"Executing cleanup: {task.__name__}")
                if asyncio.iscoroutinefunction(task):
                    await task()
                else:
                    task()
            except Exception as e:
                logger.error(f"Error in cleanup task {task.__name__}: {e}")

        logger.info("Cleanup process completed")

    async def wait_for_shutdown(self):
        """Wait for shutdown signal."""
        await self.shutdown_event.wait()

    @staticmethod
    def kill_process_on_port(port: int) -> bool:
        """
        Kill any process using the specified port.

        Args:
            port: Port number to free up

        Returns:
            bool: True if a process was killed, False otherwise
        """
        import platform
        import subprocess

        try:
            system = platform.system()

            if system == "Windows":
                # Find process using port
                result = subprocess.run(
                    f"netstat -ano | findstr :{port}",
                    shell=True,
                    capture_output=True,
                    text=True,
                )

                if result.returncode == 0 and result.stdout:
                    # Extract PID from netstat output
                    lines = result.stdout.strip().split("\n")
                    for line in lines:
                        if "LISTENING" in line:
                            parts = line.split()
                            pid = parts[-1]

                            # Kill the process
                            kill_result = subprocess.run(
                                f"taskkill /F /PID {pid}",
                                shell=True,
                                capture_output=True,
                                text=True,
                            )

                            if kill_result.returncode == 0:
                                logger.info(f"Killed process {pid} using port {port}")
                                return True
                            else:
                                logger.warning(
                                    f"Failed to kill process {pid}: {kill_result.stderr}"
                                )

            elif system in ["Linux", "Darwin"]:  # Linux or macOS
                # Find process using port
                result = subprocess.run(
                    f"lsof -ti:{port}", shell=True, capture_output=True, text=True
                )

                if result.returncode == 0 and result.stdout:
                    pid = result.stdout.strip()

                    # Kill the process
                    subprocess.run(f"kill -9 {pid}", shell=True)
                    logger.info(f"Killed process {pid} using port {port}")
                    return True

            return False

        except Exception as e:
            logger.error(f"Error killing process on port {port}: {e}")
            return False

    @staticmethod
    def check_port_available(port: int) -> bool:
        """
        Check if a port is available.

        Args:
            port: Port number to check

        Returns:
            bool: True if port is available, False if in use
        """
        import socket

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("0.0.0.0", port))
                return True
            except OSError:
                return False

    def ensure_port_free(self) -> bool:
        """
        Ensure the configured port is free, killing any process if necessary.

        Returns:
            bool: True if port is now free, False otherwise
        """
        if self.check_port_available(self.port):
            logger.info(f"Port {self.port} is available")
            return True

        logger.warning(f"Port {self.port} is in use, attempting to free it...")
        if self.kill_process_on_port(self.port):
            # Wait a moment for port to be released
            import time

            time.sleep(1)

            if self.check_port_available(self.port):
                logger.info(f"Port {self.port} is now available")
                return True

        logger.error(f"Failed to free port {self.port}")
        return False


# Global shutdown manager instance
_shutdown_manager: Optional[ShutdownManager] = None


def get_shutdown_manager(port: int = 8000) -> ShutdownManager:
    """
    Get or create the global shutdown manager instance.

    Args:
        port: Port number to manage

    Returns:
        ShutdownManager: The global shutdown manager instance
    """
    global _shutdown_manager
    if _shutdown_manager is None:
        _shutdown_manager = ShutdownManager(port)
    return _shutdown_manager


async def graceful_shutdown(app, shutdown_manager: ShutdownManager):
    """
    Perform graceful shutdown of the application.

    Args:
        app: FastAPI application instance
        shutdown_manager: Shutdown manager instance
    """
    logger.info("Initiating graceful shutdown...")

    # Cancel all background tasks
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    for task in tasks:
        task.cancel()

    # Wait for tasks to complete cancellation
    await asyncio.gather(*tasks, return_exceptions=True)

    # Run cleanup tasks
    await shutdown_manager.cleanup()

    logger.info("Graceful shutdown complete")
