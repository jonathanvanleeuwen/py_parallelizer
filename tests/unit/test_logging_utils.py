"""Tests for logging utilities."""

import logging

import pytest

from py_parallelizer.utils.logging import TqdmLoggingHandler, setup_logger


class TestTqdmLoggingHandler:
    def test_default_level(self):
        handler = TqdmLoggingHandler()
        assert handler.level == logging.NOTSET

    def test_custom_level(self):
        handler = TqdmLoggingHandler(level=logging.DEBUG)
        assert handler.level == logging.DEBUG

    def test_emit_writes_message(self, capsys):
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

    def test_raises_keyboard_interrupt(self):
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
            raise KeyboardInterrupt()

        handler.format = mock_format

        with pytest.raises(KeyboardInterrupt):
            handler.emit(record)

    def test_raises_system_exit(self):
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
    def test_returns_logger(self):
        logger = setup_logger("test_module")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_module"

    def test_adds_tqdm_handler(self):
        logger = setup_logger("test_module_unique_handler")
        has_tqdm_handler = any(
            isinstance(h, TqdmLoggingHandler) for h in logger.handlers
        )
        assert has_tqdm_handler

    def test_does_not_duplicate_handlers(self):
        logger_name = "test_module_no_duplicate"

        existing_logger = logging.getLogger(logger_name)
        existing_logger.handlers.clear()

        setup_logger(logger_name)
        setup_logger(logger_name)

        logger = logging.getLogger(logger_name)
        tqdm_handlers = [
            h for h in logger.handlers if isinstance(h, TqdmLoggingHandler)
        ]
        assert len(tqdm_handlers) == 1
