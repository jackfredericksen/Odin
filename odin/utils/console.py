"""
Professional console output formatting for Odin
Provides clean, color-coded terminal output without emojis
"""

import sys
from enum import Enum
from typing import Optional


class Color(Enum):
    """ANSI color codes for terminal output."""

    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"

    # Foreground colors
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"

    # Bright foreground colors
    BRIGHT_BLACK = "\033[90m"
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"


class ConsoleFormatter:
    """Professional console output formatter."""

    def __init__(self, use_colors: bool = True):
        """
        Initialize console formatter.

        Args:
            use_colors: Whether to use ANSI color codes (auto-detected if not set)
        """
        # Auto-detect color support
        self.use_colors = use_colors and self._supports_color()

    @staticmethod
    def _supports_color() -> bool:
        """Check if terminal supports color output."""
        # Windows 10+ supports ANSI colors
        if sys.platform == "win32":
            try:
                import ctypes

                kernel32 = ctypes.windll.kernel32
                # Enable virtual terminal processing
                kernel32.SetConsoleMode(
                    kernel32.GetStdHandle(-11), 7
                )  # STD_OUTPUT_HANDLE
                return True
            except Exception:
                return False

        # Unix-like systems typically support colors
        return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()

    def colorize(self, text: str, color: Color, bold: bool = False) -> str:
        """
        Apply color to text.

        Args:
            text: Text to colorize
            color: Color to apply
            bold: Whether to make text bold

        Returns:
            Colorized text string
        """
        if not self.use_colors:
            return text

        result = ""
        if bold:
            result += Color.BOLD.value
        result += color.value + text + Color.RESET.value
        return result

    def success(self, text: str, bold: bool = False) -> str:
        """Format success message in green."""
        return self.colorize(text, Color.BRIGHT_GREEN, bold)

    def error(self, text: str, bold: bool = False) -> str:
        """Format error message in red."""
        return self.colorize(text, Color.BRIGHT_RED, bold)

    def warning(self, text: str, bold: bool = False) -> str:
        """Format warning message in yellow."""
        return self.colorize(text, Color.BRIGHT_YELLOW, bold)

    def info(self, text: str, bold: bool = False) -> str:
        """Format info message in cyan."""
        return self.colorize(text, Color.BRIGHT_CYAN, bold)

    def debug(self, text: str, bold: bool = False) -> str:
        """Format debug message in dim white."""
        return self.colorize(text, Color.BRIGHT_BLACK, bold)

    def header(self, text: str) -> str:
        """Format header text in bold blue."""
        return self.colorize(text, Color.BRIGHT_BLUE, bold=True)

    def dim(self, text: str) -> str:
        """Format dimmed text."""
        if not self.use_colors:
            return text
        return Color.DIM.value + text + Color.RESET.value

    def separator(self, char: str = "=", length: int = 70) -> str:
        """Create a separator line."""
        return self.dim(char * length)

    def box(
        self,
        title: str,
        lines: list[str],
        width: int = 70,
        color: Optional[Color] = None,
    ) -> str:
        """
        Create a bordered box with content.

        Args:
            title: Box title
            lines: Content lines
            width: Box width
            color: Optional color for the box

        Returns:
            Formatted box string
        """
        box_color = color or Color.BRIGHT_BLUE

        top = "┌" + "─" * (width - 2) + "┐"
        bottom = "└" + "─" * (width - 2) + "┘"

        result = []
        result.append(self.colorize(top, box_color))

        # Title
        if title:
            title_line = f"│ {title.center(width - 4)} │"
            result.append(self.colorize(title_line, box_color, bold=True))
            result.append(self.colorize("├" + "─" * (width - 2) + "┤", box_color))

        # Content lines
        for line in lines:
            # Handle multi-line content
            if "\n" in line:
                for subline in line.split("\n"):
                    content = f"│ {subline.ljust(width - 4)} │"
                    result.append(self.colorize(content, box_color))
            else:
                content = f"│ {line.ljust(width - 4)} │"
                result.append(self.colorize(content, box_color))

        result.append(self.colorize(bottom, box_color))

        return "\n".join(result)

    def status_line(
        self, label: str, value: str, status: str = "info", width: int = 50
    ) -> str:
        """
        Create a status line with label and value.

        Args:
            label: Status label
            value: Status value
            status: Status type (success, error, warning, info)
            width: Total line width

        Returns:
            Formatted status line
        """
        dots_count = width - len(label) - len(value) - 2
        dots = "." * max(1, dots_count)

        if status == "success":
            value_colored = self.success(value)
        elif status == "error":
            value_colored = self.error(value)
        elif status == "warning":
            value_colored = self.warning(value)
        else:
            value_colored = self.info(value)

        return f"{label} {self.dim(dots)} {value_colored}"

    def progress_bar(
        self, current: int, total: int, width: int = 40, show_percent: bool = True
    ) -> str:
        """
        Create a text-based progress bar.

        Args:
            current: Current progress value
            total: Total value
            width: Progress bar width
            show_percent: Whether to show percentage

        Returns:
            Formatted progress bar
        """
        if total == 0:
            percent = 0
        else:
            percent = min(100, int((current / total) * 100))

        filled = int((percent / 100) * width)
        empty = width - filled

        bar = "█" * filled + "░" * empty

        if percent >= 70:
            bar_colored = self.success(bar)
        elif percent >= 40:
            bar_colored = self.warning(bar)
        else:
            bar_colored = self.error(bar)

        if show_percent:
            return f"[{bar_colored}] {percent}%"
        else:
            return f"[{bar_colored}] {current}/{total}"


# Global formatter instance
_console_formatter: Optional[ConsoleFormatter] = None


def get_console_formatter() -> ConsoleFormatter:
    """Get or create global console formatter instance."""
    global _console_formatter
    if _console_formatter is None:
        _console_formatter = ConsoleFormatter()
    return _console_formatter


# Convenience functions
def print_success(message: str):
    """Print success message."""
    fmt = get_console_formatter()
    print(fmt.success(f"✓ {message}"))


def print_error(message: str):
    """Print error message."""
    fmt = get_console_formatter()
    print(fmt.error(f"✗ {message}"))


def print_warning(message: str):
    """Print warning message."""
    fmt = get_console_formatter()
    print(fmt.warning(f"⚠ {message}"))


def print_info(message: str):
    """Print info message."""
    fmt = get_console_formatter()
    print(fmt.info(f"ℹ {message}"))


def print_header(message: str):
    """Print header message."""
    fmt = get_console_formatter()
    print(fmt.header(message))


def print_separator(char: str = "=", length: int = 70):
    """Print separator line."""
    fmt = get_console_formatter()
    print(fmt.separator(char, length))


def print_box(title: str, lines: list[str], width: int = 70):
    """Print a bordered box."""
    fmt = get_console_formatter()
    print(fmt.box(title, lines, width))


def print_status(label: str, value: str, status: str = "info"):
    """Print a status line."""
    fmt = get_console_formatter()
    print(fmt.status_line(label, value, status))
