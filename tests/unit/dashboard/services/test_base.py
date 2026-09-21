from unittest.mock import Mock

from services.base import BaseService


def test_refresh_clears_cache():
    """Refresh should clear the configured cache manager."""
    api_client = Mock()
    cache_manager = Mock()

    service = BaseService(
        api_client=api_client,
        cache_manager=cache_manager,
    )

    service.refresh()

    cache_manager.clear.assert_called_once_with()

from unittest.mock import Mock, patch

from services.base import BaseService


def test_handle_error_logs_and_reraises():
    """_handle_error should log the error and re-raise it."""
    service = BaseService(
        api_client=Mock(),
        cache_manager=Mock(),
    )

    error = ValueError("test error")

    with patch("services.base.logger.error") as error_mock:
        try:
            raise error
        except ValueError as exc:
            try:
                service._handle_error(exc, "test context")
            except ValueError as raised:
                assert raised is error

    error_mock.assert_called_once_with(
        "Error in test context: test error",
    )
