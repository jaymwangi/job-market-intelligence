from dashboard.core.config import DashboardConfig


def test_colors_includes_primary_color():
    config = DashboardConfig()

    assert config.colors["primary"] == "#1a1a2e"


def test_app_title_alias_returns_app_title():
    config = DashboardConfig(app_title="Test Dashboard")

    assert config.APP_TITLE == "Test Dashboard"


def test_app_icon_alias_returns_app_icon():
    config = DashboardConfig(app_icon="🧪")

    assert config.APP_ICON == "🧪"


def test_api_base_url_alias_returns_api_base_url():
    config = DashboardConfig(api_base_url="https://example.com")

    assert config.API_BASE_URL == "https://example.com"


def test_api_timeout_alias_returns_api_timeout():
    config = DashboardConfig(api_timeout=60)

    assert config.API_TIMEOUT == 60


def test_cache_ttl_alias_returns_cache_ttl_default():
    config = DashboardConfig(cache_ttl_default=900)

    assert config.CACHE_TTL == 900
