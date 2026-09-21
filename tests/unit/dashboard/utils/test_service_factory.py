from unittest.mock import patch

from utils.service_factory import (
    clear_service_cache,
    get_analytics_service,
    get_health_service,
    get_jobs_service,
)


def test_get_jobs_service_delegates_to_state_manager():
    expected = object()

    with patch(
        "utils.service_factory.StateManager.get_jobs_service",
        return_value=expected,
    ) as mock_get:
        result = get_jobs_service()

    mock_get.assert_called_once_with()
    assert result is expected


def test_get_analytics_service_delegates_to_state_manager():
    expected = object()

    with patch(
        "utils.service_factory.StateManager.get_analytics_service",
        return_value=expected,
    ) as mock_get:
        result = get_analytics_service()

    mock_get.assert_called_once_with()
    assert result is expected


def test_get_health_service_delegates_to_state_manager():
    expected = object()

    with patch(
        "utils.service_factory.StateManager.get_health_service",
        return_value=expected,
    ) as mock_get:
        result = get_health_service()

    mock_get.assert_called_once_with()
    assert result is expected


def test_clear_service_cache_delegates_to_state_manager():
    with patch(
        "utils.service_factory.StateManager.clear_cache",
    ) as mock_clear:
        result = clear_service_cache()

    mock_clear.assert_called_once_with()
    assert result is None