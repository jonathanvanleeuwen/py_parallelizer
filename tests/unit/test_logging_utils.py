"""Tests for logging utilities."""

import logging

import pytest

from py_parallelizer.logging_utils import TqdmLoggingHandler, setup_logger


class TestTqdmLoggingHandler:
    """Tests for TqdmLoggingHandler class."""

    def test_handler_initialization_default_level(self):
        """Test that handler initializes with NOTSET level by default."""
        handler = TqdmLoggingHandler()
        assert handler.level == logging.NOTSET

    def test_handler_initialization_custom_level(self):
        """Test that handler initializes with custom level."""
        handler = TqdmLoggingHandler(level=logging.DEBUG)
        assert handler.level == logging.DEBUG

    def test_handler_emit_writes_message(self, capsys):
        """Test that handler emits formatted messages."""
        handler = TqdmLoggingHandler()
        handler.setFormatter(logging.Formatter("%(message)s"))

        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        handler.emit(record)
        captured = capsys.readouterr()
        assert "Test message" in captured.out

    def test_handler_raises_keyboard_interrupt(self):
        """Test that KeyboardInterrupt is re-raised."""
        handler = TqdmLoggingHandler()

        # Create a record that will cause an exception during formatting
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Test",
            args=(),
            exc_info=None,
        )

        # Mock the format method to raise KeyboardInterrupt
        def mock_format(record):
            raise KeyboardInterrupt()

        handler.format = mock_format

        with pytest.raises(KeyboardInterrupt):
            handler.emit(record)

    def test_handler_raises_system_exit(self):
        """Test that SystemExit is re-raised."""
        handler = TqdmLoggingHandler()

        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Test",
            args=(),
            exc_info=None,
        )

        def mock_format(record):
            raise SystemExit()

        handler.format = mock_format

        with pytest.raises(SystemExit):
            handler.emit(record)


class TestSetupLogger:
    """Tests for setup_logger function."""

    def test_setup_logger_returns_logger(self):
        """Test that setup_logger returns a logger instance."""
        logger = setup_logger("test_module")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_module"

    def test_setup_logger_adds_tqdm_handler(self):
        """Test that setup_logger adds TqdmLoggingHandler."""
        # Use unique name to avoid conflicts with other tests
        logger = setup_logger("test_module_unique_handler")
        has_tqdm_handler = any(isinstance(h, TqdmLoggingHandler) for h in logger.handlers)
        assert has_tqdm_handler

    def test_setup_logger_does_not_duplicate_handlers(self):
        """Test that calling setup_logger twice doesn't duplicate handlers."""
        logger_name = "test_module_no_duplicate"

        # Clear any existing handlers
        existing_logger = logging.getLogger(logger_name)
        existing_logger.handlers.clear()

        # Call setup_logger twice
        setup_logger(logger_name)
        setup_logger(logger_name)

        logger = logging.getLogger(logger_name)
        tqdm_handlers = [h for h in logger.handlers if isinstance(h, TqdmLoggingHandler)]
        assert len(tqdm_handlers) == 1
