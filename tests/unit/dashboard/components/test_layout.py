from datetime import datetime
from unittest.mock import MagicMock, patch

from components.layout import (
    card,
    divider,
    info_bar,
    page_header,
    refresh_button,
    section_header,
    stats_bar,
    timestamp,
)


@patch("components.layout.get_icon")
@patch("components.layout.st")
def test_page_header_without_icon_or_subtitle(
    mock_st: MagicMock,
    mock_get_icon: MagicMock,
) -> None:
    page_header("Dashboard")

    mock_get_icon.assert_not_called()
    mock_st.markdown.assert_called_once()

    html = mock_st.markdown.call_args.args[0]
    assert "Dashboard" in html
    assert "display:inline-flex" not in html
    assert "color: #636e72" not in html
    assert mock_st.markdown.call_args.kwargs["unsafe_allow_html"] is True


@patch("components.layout.get_icon")
@patch("components.layout.st")
def test_page_header_maps_emoji_icon_and_includes_subtitle(
    mock_st: MagicMock,
    mock_get_icon: MagicMock,
) -> None:
    mock_get_icon.return_value = "<svg>analytics</svg>"

    page_header(
        "Analytics",
        subtitle="Job market overview",
        icon="📊",
    )

    mock_get_icon.assert_called_once_with(
        "analytics",
        size=32,
        color="#1a1a2e",
    )

    html = mock_st.markdown.call_args.args[0]
    assert "Analytics" in html
    assert "Job market overview" in html
    assert "<svg>analytics</svg>" in html


@patch("components.layout.get_icon")
@patch("components.layout.st")
def test_page_header_uses_custom_icon_name(
    mock_st: MagicMock,
    mock_get_icon: MagicMock,
) -> None:
    mock_get_icon.return_value = "<svg>custom</svg>"

    page_header("Jobs", icon="custom_icon")

    mock_get_icon.assert_called_once_with(
        "custom_icon",
        size=32,
        color="#1a1a2e",
    )


@patch("components.layout.get_icon")
@patch("components.layout.st")
def test_section_header_without_icon_or_subtitle(
    mock_st: MagicMock,
    mock_get_icon: MagicMock,
) -> None:
    section_header("Skills")

    mock_get_icon.assert_not_called()
    mock_st.markdown.assert_called_once()

    html = mock_st.markdown.call_args.args[0]
    assert "Skills" in html
    assert "display:inline-flex" not in html
    assert mock_st.markdown.call_args.kwargs["unsafe_allow_html"] is True


@patch("components.layout.get_icon")
@patch("components.layout.st")
def test_section_header_maps_emoji_icon_and_includes_subtitle(
    mock_st: MagicMock,
    mock_get_icon: MagicMock,
) -> None:
    mock_get_icon.return_value = "<svg>location</svg>"

    section_header(
        "Locations",
        subtitle="Top job locations",
        icon="📍",
    )

    mock_get_icon.assert_called_once_with(
        "location",
        size=20,
        color="#1a1a2e",
    )

    html = mock_st.markdown.call_args.args[0]
    assert "Locations" in html
    assert "Top job locations" in html
    assert "<svg>location</svg>" in html


@patch("components.layout.get_icon")
@patch("components.layout.st")
def test_section_header_uses_custom_icon_name(
    mock_st: MagicMock,
    mock_get_icon: MagicMock,
) -> None:
    mock_get_icon.return_value = "<svg>custom</svg>"

    section_header("Skills", icon="custom_icon")

    mock_get_icon.assert_called_once_with(
        "custom_icon",
        size=20,
        color="#1a1a2e",
    )


@patch("components.layout.st")
def test_stats_bar_with_multiple_stats(mock_st: MagicMock) -> None:
    stats_bar(
        [
            ("Jobs", 100),
            ("Companies", 25),
            ("Countries", 10),
        ]
    )

    mock_st.markdown.assert_called_once()
    html = mock_st.markdown.call_args.args[0]

    assert "100" in html
    assert "Jobs" in html
    assert "25" in html
    assert "Companies" in html
    assert "10" in html
    assert "Countries" in html
    assert html.count("•") == 2
    assert mock_st.markdown.call_args.kwargs["unsafe_allow_html"] is True


@patch("components.layout.st")
def test_stats_bar_with_empty_stats(mock_st: MagicMock) -> None:
    stats_bar([])

    mock_st.markdown.assert_called_once()

    html = mock_st.markdown.call_args.args[0]
    assert "<div" in html
    assert "•" not in html
    assert "</div>" in html


@patch("components.layout.get_icon")
@patch("components.layout.st")
def test_card_without_title_or_icon(
    mock_st: MagicMock,
    mock_get_icon: MagicMock,
) -> None:
    card("<p>Content</p>")

    mock_get_icon.assert_not_called()
    mock_st.markdown.assert_called_once()

    html = mock_st.markdown.call_args.args[0]
    assert "<p>Content</p>" in html
    assert "font-weight: 600" not in html


@patch("components.layout.get_icon")
@patch("components.layout.st")
def test_card_with_title_and_icon(
    mock_st: MagicMock,
    mock_get_icon: MagicMock,
) -> None:
    mock_get_icon.return_value = "<svg>info</svg>"

    card(
        "<p>Content</p>",
        title="Summary",
        icon="info",
    )

    mock_get_icon.assert_called_once_with(
        "info",
        size=16,
        color="#1a1a2e",
    )

    html = mock_st.markdown.call_args.args[0]
    assert "Summary" in html
    assert "<p>Content</p>" in html
    assert "<svg>info</svg>" in html


@patch("components.layout.st")
def test_divider(mock_st: MagicMock) -> None:
    divider()

    mock_st.markdown.assert_called_once()

    html = mock_st.markdown.call_args.args[0]
    assert "<hr" in html
    assert "background: #e9ecef" in html
    assert mock_st.markdown.call_args.kwargs["unsafe_allow_html"] is True


@patch("components.layout.get_icon")
@patch("components.layout.st")
def test_info_bar_uses_default_icon(
    mock_st: MagicMock,
    mock_get_icon: MagicMock,
) -> None:
    mock_get_icon.return_value = "<svg>info</svg>"

    info_bar("Analytics data is up to date.")

    mock_get_icon.assert_called_once_with(
        "info",
        size=16,
        color="#0f3460",
    )

    html = mock_st.markdown.call_args.args[0]
    assert "Analytics data is up to date." in html
    assert "<svg>info</svg>" in html


@patch("components.layout.get_icon")
@patch("components.layout.st")
def test_info_bar_uses_custom_icon(
    mock_st: MagicMock,
    mock_get_icon: MagicMock,
) -> None:
    mock_get_icon.return_value = "<svg>warning</svg>"

    info_bar("Something needs attention.", icon="warning")

    mock_get_icon.assert_called_once_with(
        "warning",
        size=16,
        color="#0f3460",
    )

    html = mock_st.markdown.call_args.args[0]
    assert "Something needs attention." in html
    assert "<svg>warning</svg>" in html


@patch("components.layout.datetime")
@patch("components.layout.st")
def test_timestamp(mock_st: MagicMock, mock_datetime: MagicMock) -> None:
    fixed_datetime = datetime(2026, 9, 14, 16, 30)
    mock_datetime.now.return_value = fixed_datetime

    timestamp()

    mock_datetime.now.assert_called_once()
    mock_st.markdown.assert_called_once()

    html = mock_st.markdown.call_args.args[0]
    assert "Last updated: Sep 14, 2026 at 04:30 PM" in html
    assert mock_st.markdown.call_args.kwargs["unsafe_allow_html"] is True


@patch("components.layout.get_icon")
@patch("components.layout.st")
def test_refresh_button_uses_defaults(
    mock_st: MagicMock,
    mock_get_icon: MagicMock,
) -> None:
    mock_get_icon.return_value = "<svg>refresh</svg>"
    mock_st.button.return_value = True

    result = refresh_button()

    mock_get_icon.assert_called_once_with(
        "refresh",
        size=16,
        color="#ffffff",
    )
    mock_st.button.assert_called_once_with(
        "<svg>refresh</svg> Refresh",
        use_container_width=True,
        key="refresh_button",
        help="Refresh dashboard",
    )
    assert result is True


@patch("components.layout.get_icon")
@patch("components.layout.st")
def test_refresh_button_uses_custom_label_and_key(
    mock_st: MagicMock,
    mock_get_icon: MagicMock,
) -> None:
    mock_get_icon.return_value = "<svg>refresh</svg>"
    mock_st.button.return_value = False

    result = refresh_button(
        label="Reload Data",
        key="reload_data",
    )

    mock_st.button.assert_called_once_with(
        "<svg>refresh</svg> Reload Data",
        use_container_width=True,
        key="reload_data",
        help="Refresh dashboard",
    )
    assert result is False
