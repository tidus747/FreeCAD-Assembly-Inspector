"""Tests for logging setup."""

import logging

from assembly_inspector.logging_utils import configure_logging, get_logger


def test_configure_logging_sets_package_handler():
    configure_logging()
    logger = get_logger("assembly_inspector.test")

    package_logger = logging.getLogger("assembly_inspector")
    assert logger.name == "assembly_inspector.test"
    assert package_logger.handlers
    assert package_logger.propagate is False

