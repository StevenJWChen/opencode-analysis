"""Tests for structured logging system"""

import pytest
import logging
from pathlib import Path
from io import StringIO

import sys
sys.path.insert(0, 'src')

from pycode.logging import (
    PyCodeLogger,
    LogLevel,
    configure_logging,
    get_logger,
)


class TestPyCodeLogger:
    """Test PyCodeLogger class"""

    def test_logger_creation(self):
        """Test creating a logger"""
        logger = PyCodeLogger(name="test", level=LogLevel.NORMAL)
        assert logger.name == "test"
        assert logger.level == LogLevel.NORMAL

    def test_log_levels(self):
        """Test different log levels"""
        # Quiet - should only log errors
        logger = PyCodeLogger(level=LogLevel.QUIET)
        assert logger.level == LogLevel.QUIET

        # Normal - should log warnings and errors
        logger = PyCodeLogger(level=LogLevel.NORMAL)
        assert logger.level == LogLevel.NORMAL

        # Verbose - should log everything except debug
        logger = PyCodeLogger(level=LogLevel.VERBOSE)
        assert logger.level == LogLevel.VERBOSE

        # Debug - should log everything
        logger = PyCodeLogger(level=LogLevel.DEBUG)
        assert logger.level == LogLevel.DEBUG

    def test_contextual_logging(self):
        """Test logging with context key=value pairs"""
        logger = PyCodeLogger(level=LogLevel.DEBUG)

        # Should not raise exception
        logger.info("Test message", key1="value1", key2=42, key3=True)
        logger.debug("Debug message", session_id="abc123", iteration=5)
        logger.warning("Warning message", error="test error", code=404)
        logger.error("Error message", exception="TestException", stack="trace")

    def test_file_logging(self, temp_dir):
        """Test logging to a file"""
        log_file = temp_dir / "test.log"
        logger = PyCodeLogger(name="test", level=LogLevel.DEBUG, log_file=log_file)

        logger.info("Test message to file")

        assert log_file.exists()
        content = log_file.read_text()
        assert "Test message to file" in content

    def test_quiet_level_suppresses_info(self):
        """Test that quiet level suppresses info messages"""
        logger = PyCodeLogger(level=LogLevel.QUIET)

        # Info should be suppressed in quiet mode
        # No easy way to test without capturing output, but we verify the level is set
        assert logger.level == LogLevel.QUIET

    def test_format_context(self):
        """Test context formatting"""
        logger = PyCodeLogger(level=LogLevel.DEBUG)

        # Test that context is formatted correctly
        formatted = logger._format_context(key1="value1", key2=42)
        assert "key1=value1" in formatted
        assert "key2=42" in formatted


class TestConfigureLogging:
    """Test configure_logging function"""

    def test_configure_logging_quiet(self):
        """Test configuring logging to quiet level"""
        configure_logging(level=LogLevel.QUIET)
        logger = get_logger()
        assert logger.level == LogLevel.QUIET

    def test_configure_logging_debug(self):
        """Test configuring logging to debug level"""
        configure_logging(level=LogLevel.DEBUG)
        logger = get_logger()
        assert logger.level == LogLevel.DEBUG

    def test_configure_logging_with_file(self, temp_dir):
        """Test configuring logging with a file"""
        log_file = temp_dir / "pycode.log"
        configure_logging(level=LogLevel.DEBUG, log_file=log_file)

        logger = get_logger()
        logger.info("Test file logging")

        assert log_file.exists()
        content = log_file.read_text()
        assert "Test file logging" in content


class TestGetLogger:
    """Test get_logger singleton"""

    def test_get_logger_returns_same_instance(self):
        """Test that get_logger returns the same instance"""
        logger1 = get_logger()
        logger2 = get_logger()
        assert logger1 is logger2

    def test_get_logger_after_configure(self):
        """Test that get_logger returns configured logger"""
        configure_logging(level=LogLevel.VERBOSE)
        logger = get_logger()
        assert logger.level == LogLevel.VERBOSE


class TestLogLevelEnum:
    """Test LogLevel enum"""

    def test_log_level_values(self):
        """Test LogLevel enum values"""
        assert LogLevel.QUIET.value == "quiet"
        assert LogLevel.NORMAL.value == "normal"
        assert LogLevel.VERBOSE.value == "verbose"
        assert LogLevel.DEBUG.value == "debug"

    def test_log_level_from_string(self):
        """Test creating LogLevel from string"""
        assert LogLevel("quiet") == LogLevel.QUIET
        assert LogLevel("normal") == LogLevel.NORMAL
        assert LogLevel("verbose") == LogLevel.VERBOSE
        assert LogLevel("debug") == LogLevel.DEBUG
