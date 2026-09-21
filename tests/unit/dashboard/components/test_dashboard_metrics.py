from unittest.mock import MagicMock, patch

from components.metrics import MetricCardData, render_metric_card, render_metric_row


class SessionContainer:
    """Simple context-manager stand-in for Streamlit containers."""

    def __enter__(self) -> "SessionContainer":
        return self

    def __exit__(self, exc_type: object, exc_value: object, traceback: object) -> None:
        return None


def test_metric_card_data_defaults() -> None:
    data = MetricCardData(title="Total Jobs", value=100)

    assert data.title == "Total Jobs"
    assert data.value == 100
    assert data.icon is None
    assert data.color is None
    assert data.subtitle is None
    assert data.trend is None
    assert data.trend_label is None


def test_metric_card_data_accepts_all_fields() -> None:
    data = MetricCardData(
        title="Growth",
        value=125.5,
        icon="growth",
        color="#123456",
        subtitle="Compared with last month",
        trend=12.5,
        trend_label="vs last month",
    )

    assert data.title == "Growth"
    assert data.value == 125.5
    assert data.icon == "growth"
    assert data.color == "#123456"
    assert data.subtitle == "Compared with last month"
    assert data.trend == 12.5
    assert data.trend_label == "vs last month"


@patch("components.metrics.get_icon")
@patch("components.metrics.st")
def test_render_metric_card_uses_defaults(
    mock_st: MagicMock,
    mock_get_icon: MagicMock,
) -> None:
    mock_st.container.return_value = SessionContainer()
    mock_get_icon.return_value = "<svg>jobs</svg>"

    data = MetricCardData(title="Total Jobs", value=100)

    render_metric_card(data)

    mock_get_icon.assert_called_once_with(
        "jobs_metric",
        size=20,
        color="#6c5ce7",
    )

    assert mock_st.markdown.call_count == 2
    assert mock_st.markdown.call_args_list[0].kwargs["unsafe_allow_html"] is True
    assert mock_st.markdown.call_args_list[1].kwargs["unsafe_allow_html"] is True


@patch("components.metrics.get_icon")
@patch("components.metrics.st")
def test_render_metric_card_uses_custom_color_and_icon(
    mock_st: MagicMock,
    mock_get_icon: MagicMock,
) -> None:
    mock_st.container.return_value = SessionContainer()
    mock_get_icon.return_value = "<svg>custom</svg>"

    data = MetricCardData(
        title="Revenue",
        value="$5000",
        icon="revenue",
        color="#123456",
    )

    render_metric_card(data)

    mock_get_icon.assert_called_once_with(
        "revenue",
        size=20,
        color="#123456",
    )

    card_html = mock_st.markdown.call_args_list[1].args[0]
    assert "$5000" in card_html
    assert "Revenue" in card_html
    assert "<svg>custom</svg>" in card_html
    style_html = mock_st.markdown.call_args_list[0].args[0]
    assert "#123456" in style_html


@patch("components.metrics.get_icon")
@patch("components.metrics.st")
def test_render_metric_card_positive_trend_with_label(
    mock_st: MagicMock,
    mock_get_icon: MagicMock,
) -> None:
    mock_st.container.return_value = SessionContainer()
    mock_get_icon.return_value = "<svg>trend</svg>"

    data = MetricCardData(
        title="Applications",
        value=200,
        trend=12.5,
        trend_label="vs last month",
    )

    render_metric_card(data)

    card_html = mock_st.markdown.call_args_list[1].args[0]

    assert "↑ 12.5%" in card_html
    assert "vs last month" in card_html


@patch("components.metrics.get_icon")
@patch("components.metrics.st")
def test_render_metric_card_negative_trend_without_label(
    mock_st: MagicMock,
    mock_get_icon: MagicMock,
) -> None:
    mock_st.container.return_value = SessionContainer()
    mock_get_icon.return_value = "<svg>trend</svg>"

    data = MetricCardData(
        title="Errors",
        value=10,
        trend=-7.25,
    )

    render_metric_card(data)

    card_html = mock_st.markdown.call_args_list[1].args[0]

    assert "↓ 7.2%" in card_html
    assert "7.25" not in card_html


@patch("components.metrics.get_icon")
@patch("components.metrics.st")
def test_render_metric_card_without_trend_or_subtitle(
    mock_st: MagicMock,
    mock_get_icon: MagicMock,
) -> None:
    mock_st.container.return_value = SessionContainer()
    mock_get_icon.return_value = "<svg>basic</svg>"

    data = MetricCardData(
        title="Jobs",
        value=50,
    )

    render_metric_card(data)

    card_html = mock_st.markdown.call_args_list[1].args[0]

    assert "metric-card-trend" not in card_html
    assert "metric-card-subtitle" not in card_html


@patch("components.metrics.get_icon")
@patch("components.metrics.st")
def test_render_metric_card_with_subtitle(
    mock_st: MagicMock,
    mock_get_icon: MagicMock,
) -> None:
    mock_st.container.return_value = SessionContainer()
    mock_get_icon.return_value = "<svg>basic</svg>"

    data = MetricCardData(
        title="Jobs",
        value=50,
        subtitle="Updated today",
    )

    render_metric_card(data)

    card_html = mock_st.markdown.call_args_list[1].args[0]

    assert "metric-card-subtitle" in card_html
    assert "Updated today" in card_html


@patch("components.metrics.st")
def test_render_metric_row_with_no_metrics(mock_st: MagicMock) -> None:
    render_metric_row([])

    mock_st.info.assert_called_once_with("No metrics to display")
    mock_st.columns.assert_not_called()


@patch("components.metrics.render_metric_card")
@patch("components.metrics.st")
def test_render_metric_row_uses_requested_column_count(
    mock_st: MagicMock,
    mock_render_metric_card: MagicMock,
) -> None:
    columns = [SessionContainer(), SessionContainer()]
    mock_st.columns.return_value = columns

    metrics = [
        MetricCardData(title="Jobs", value=100),
        MetricCardData(title="Users", value=50),
    ]

    render_metric_row(metrics, columns=4)

    mock_st.columns.assert_called_once_with(2)
    assert mock_render_metric_card.call_count == 2
    mock_render_metric_card.assert_any_call(metrics[0])
    mock_render_metric_card.assert_any_call(metrics[1])


@patch("components.metrics.render_metric_card")
@patch("components.metrics.st")
def test_render_metric_row_cycles_through_columns(
    mock_st: MagicMock,
    mock_render_metric_card: MagicMock,
) -> None:
    columns = [
        SessionContainer(),
        SessionContainer(),
    ]
    mock_st.columns.return_value = columns

    metrics = [
        MetricCardData(title="Jobs", value=100),
        MetricCardData(title="Users", value=50),
        MetricCardData(title="Companies", value=25),
        MetricCardData(title="Countries", value=10),
    ]

    render_metric_row(metrics, columns=2)

    mock_st.columns.assert_called_once_with(2)
    assert mock_render_metric_card.call_count == 4
    assert mock_render_metric_card.call_args_list == [
        ((metrics[0],), {}),
        ((metrics[1],), {}),
        ((metrics[2],), {}),
        ((metrics[3],), {}),
    ]