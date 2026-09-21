from unittest.mock import MagicMock, patch

from components.loading import (
    loading_spinner,
    show_loading_animation,
    show_loading_card,
    show_skeleton_loader,
)


def test_loading_spinner_uses_default_text():
    spinner = MagicMock()

    with patch("components.loading.st.spinner", return_value=spinner):
        with loading_spinner():
            pass

    spinner.__enter__.assert_called_once()
    spinner.__exit__.assert_called_once()


def test_loading_spinner_uses_custom_text():
    spinner = MagicMock()

    with patch("components.loading.st.spinner", return_value=spinner) as mock_spinner:
        with loading_spinner("Please wait..."):
            pass

    mock_spinner.assert_called_once_with("Please wait...")
    spinner.__enter__.assert_called_once()
    spinner.__exit__.assert_called_once()


def test_loading_spinner_yields_control():
    spinner = MagicMock()

    with patch("components.loading.st.spinner", return_value=spinner):
        with loading_spinner("Loading jobs...") as value:
            assert value is None


def test_show_loading_card_uses_defaults():
    with patch("components.loading.st.info") as mock_info:
        result = show_loading_card()

    mock_info.assert_called_once_with("⏳ Loading data...")
    assert result is mock_info.return_value


def test_show_loading_card_uses_custom_text_and_icon():
    with patch("components.loading.st.info") as mock_info:
        result = show_loading_card("Fetching jobs...", "📊")

    mock_info.assert_called_once_with("📊 Fetching jobs...")
    assert result is mock_info.return_value


def test_show_skeleton_loader_uses_defaults():
    with patch("components.loading.st.markdown") as mock_markdown:
        show_skeleton_loader()

    assert mock_markdown.call_count == 4

    css_call = mock_markdown.call_args_list[0]
    assert css_call.kwargs["unsafe_allow_html"] is True
    assert "@keyframes shimmer" in css_call.args[0]
    assert "height: 60px" in css_call.args[0]

    for call in mock_markdown.call_args_list[1:]:
        assert call.args[0] == '<div class="skeleton-row"></div>'
        assert call.kwargs["unsafe_allow_html"] is True


def test_show_skeleton_loader_uses_custom_rows_and_height():
    with patch("components.loading.st.markdown") as mock_markdown:
        show_skeleton_loader(rows=5, height=100)

    assert mock_markdown.call_count == 6

    css = mock_markdown.call_args_list[0].args[0]
    assert "height: 100px" in css

    skeleton_calls = mock_markdown.call_args_list[1:]
    assert len(skeleton_calls) == 5


def test_show_skeleton_loader_with_zero_rows_only_renders_css():
    with patch("components.loading.st.markdown") as mock_markdown:
        show_skeleton_loader(rows=0)

    assert mock_markdown.call_count == 1
    assert "@keyframes shimmer" in mock_markdown.call_args_list[0].args[0]


def test_show_loading_animation_uses_defaults():
    with patch("components.loading.st.markdown") as mock_markdown:
        result = show_loading_animation()

    mock_markdown.assert_called_once()
    assert result is mock_markdown.return_value

    html = mock_markdown.call_args.args[0]
    assert "🔄 Loading..." in html
    assert "animation: spin 1s linear infinite" in html
    assert "@keyframes spin" in html
    assert mock_markdown.call_args.kwargs["unsafe_allow_html"] is True


def test_show_loading_animation_uses_custom_message_and_icon():
    with patch("components.loading.st.markdown") as mock_markdown:
        show_loading_animation("Loading analytics...", "📈")

    html = mock_markdown.call_args.args[0]

    assert "📈 Loading analytics..." in html
    assert "width: 24px" in html
    assert "height: 24px" in html
    assert "border-radius: 50%" in html
    assert "animation: spin 1s linear infinite" in html