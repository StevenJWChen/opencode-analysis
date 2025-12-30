"""
Structured Logging System

Provides consistent, configurable logging across PyCode.
Supports multiple verbosity levels and output formats.
"""

import logging
import sys
from enum import Enum
from typing import Optional
from pathlib import Path


class LogLevel(Enum):
    """Logging verbosity levels"""
    QUIET = "quiet"      # Errors only
    NORMAL = "normal"    # Errors + warnings + important info
    VERBOSE = "verbose"  # All info including debug
    DEBUG = "debug"      # Full debug output


class PyCodeLogger:
    """Centralized logger for PyCode

    Usage:
        logger = get_logger()
        logger.info("Processing file", file="script.py", lines=100)
        logger.error("API call failed", provider="anthropic", error=str(e))
    """

    def __init__(
        self,
        name: str = "pycode",
        level: LogLevel = LogLevel.NORMAL,
        log_file: Optional[Path] = None
    ):
        self.name = name
        self.level = level
        self._logger = logging.getLogger(name)
        self._setup_logger(log_file)

    def _setup_logger(self, log_file: Optional[Path] = None):
        """Configure the underlying logger"""
        # Clear existing handlers
        self._logger.handlers.clear()

        # Set level based on verbosity
        if self.level == LogLevel.QUIET:
            self._logger.setLevel(logging.ERROR)
        elif self.level == LogLevel.NORMAL:
            self._logger.setLevel(logging.INFO)
        elif self.level == LogLevel.VERBOSE:
            self._logger.setLevel(logging.DEBUG)
        else:  # DEBUG
            self._logger.setLevel(logging.DEBUG)

        # Console handler
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setLevel(self._logger.level)

        # Format: [LEVEL] message key=value key=value
        formatter = logging.Formatter(
            '[%(levelname)s] %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(formatter)
        self._logger.addHandler(console_handler)

        # File handler (if specified)
        if log_file:
            log_file.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.DEBUG)  # Always log everything to file

            # More detailed format for file
            file_formatter = logging.Formatter(
                '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(file_formatter)
            self._logger.addHandler(file_handler)

    def _format_context(self, **context) -> str:
        """Format context as key=value pairs"""
        if not context:
            return ""

        parts = []
        for key, value in context.items():
            # Handle different types
            if isinstance(value, str):
                # Quote strings with spaces
                if ' ' in value:
                    parts.append(f'{key}="{value}"')
                else:
                    parts.append(f'{key}={value}')
            else:
                parts.append(f'{key}={value}')

        return " " + " ".join(parts) if parts else ""

    def debug(self, message: str, **context):
        """Log debug message (only in verbose/debug mode)"""
        if self.level in [LogLevel.VERBOSE, LogLevel.DEBUG]:
            ctx = self._format_context(**context)
            self._logger.debug(f"{message}{ctx}")

    def info(self, message: str, **context):
        """Log info message (normal and above)"""
        if self.level != LogLevel.QUIET:
            ctx = self._format_context(**context)
            self._logger.info(f"{message}{ctx}")

    def warning(self, message: str, **context):
        """Log warning message (always shown except quiet)"""
        if self.level != LogLevel.QUIET:
            ctx = self._format_context(**context)
            self._logger.warning(f"{message}{ctx}")

    def error(self, message: str, **context):
        """Log error message (always shown)"""
        ctx = self._format_context(**context)
        self._logger.error(f"{message}{ctx}")

    def success(self, message: str, **context):
        """Log success message (info level with ✓ prefix)"""
        if self.level != LogLevel.QUIET:
            ctx = self._format_context(**context)
            self._logger.info(f"✓ {message}{ctx}")

    def set_level(self, level: LogLevel):
        """Change logging level"""
        self.level = level
        self._setup_logger()


# Global logger instance
_global_logger: Optional[PyCodeLogger] = None


def get_logger(
    name: str = "pycode",
    level: Optional[LogLevel] = None,
    log_file: Optional[Path] = None
) -> PyCodeLogger:
    """Get or create the global logger

    Args:
        name: Logger name (default: "pycode")
        level: Logging level (default: NORMAL)
        log_file: Optional file to log to

    Returns:
        PyCodeLogger instance
    """
    global _global_logger

    if _global_logger is None:
        _global_logger = PyCodeLogger(
            name=name,
            level=level or LogLevel.NORMAL,
            log_file=log_file
        )
    elif level is not None:
        _global_logger.set_level(level)

    return _global_logger


def configure_logging(
    level: LogLevel = LogLevel.NORMAL,
    log_file: Optional[Path] = None
):
    """Configure global logging

    Args:
        level: Logging verbosity level
        log_file: Optional file to write logs to
    """
    global _global_logger
    _global_logger = PyCodeLogger(
        name="pycode",
        level=level,
        log_file=log_file
    )


# Convenience functions
def debug(message: str, **context):
    """Log debug message"""
    get_logger().debug(message, **context)


def info(message: str, **context):
    """Log info message"""
    get_logger().info(message, **context)


def warning(message: str, **context):
    """Log warning message"""
    get_logger().warning(message, **context)


def error(message: str, **context):
    """Log error message"""
    get_logger().error(message, **context)


def success(message: str, **context):
    """Log success message"""
    get_logger().success(message, **context)
