import logging

from dashboard.utils.logging import (
    get_logger,
    log_api_call,
    log_performance,
    setup_logging,
)


def test_setup_logging_sets_expected_log_levels():
    setup_logging("DEBUG")

    assert logging.getLogger("urllib3").level == logging.WARNING
    assert logging.getLogger("requests").level == logging.WARNING


def test_setup_logging_defaults_invalid_level_to_info(monkeypatch):
    captured = {}

    def fake_basic_config(**kwargs):
        captured.update(kwargs)

    monkeypatch.setattr(logging, "basicConfig", fake_basic_config)

    setup_logging("INVALID")

    assert captured["level"] == logging.INFO


def test_get_logger_returns_named_logger():
    logger = get_logger("test_logger")

    assert logger.name == "test_logger"


def test_log_performance_logs_message(caplog):
    with caplog.at_level(logging.INFO, logger="performance"):
        log_performance("ETL pipeline", 1.234)

    assert "ETL pipeline took 1.23s" in caplog.text


def test_log_api_call_logs_message(caplog):
    with caplog.at_level(logging.DEBUG, logger="api"):
        log_api_call("/jobs", 200, 0.456)

    assert "/jobs → 200 (0.46s)" in caplog.text
