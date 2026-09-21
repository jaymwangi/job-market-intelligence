from unittest.mock import MagicMock, patch

from components.pagination import render_pagination


class Context:
    def __enter__(self) -> "Context":
        return self

    def __exit__(
        self,
        exc_type: object,
        exc_value: object,
        traceback: object,
    ) -> None:
        return None


class SessionState(dict[str, object]):
    def __getattr__(self, name: str) -> object:
        return self[name]

    def __setattr__(self, name: str, value: object) -> None:
        self[name] = value

def setup_streamlit_mock(mock_st: MagicMock) -> SessionState:
    session_state = SessionState()
    mock_st.session_state = session_state
    mock_st.columns.side_effect = lambda spec: [
        Context() for _ in range(spec if isinstance(spec, int) else len(spec))
    ]
    mock_st.button.return_value = False
    return session_state


@patch("components.pagination.st")
def test_render_pagination_returns_for_single_page(mock_st: MagicMock) -> None:
    render_pagination(1, 1)

    mock_st.markdown.assert_not_called()
    mock_st.columns.assert_not_called()
    mock_st.button.assert_not_called()


@patch("components.pagination.st")
def test_render_pagination_renders_all_pages_when_five_or_fewer(
    mock_st: MagicMock,
) -> None:
    setup_streamlit_mock(mock_st)

    render_pagination(3, 5)

    assert mock_st.columns.call_count == 2
    mock_st.caption.assert_called_once_with("Page 3 of 5")


@patch("components.pagination.st")
def test_render_pagination_renders_first_five_pages_near_start(
    mock_st: MagicMock,
) -> None:
    setup_streamlit_mock(mock_st)

    render_pagination(2, 10)

    assert mock_st.columns.call_count == 2
    mock_st.caption.assert_called_once_with("Page 2 of 10")


@patch("components.pagination.st")
def test_render_pagination_renders_last_five_pages_near_end(
    mock_st: MagicMock,
) -> None:
    setup_streamlit_mock(mock_st)

    render_pagination(9, 10)

    assert mock_st.columns.call_count == 2
    mock_st.caption.assert_called_once_with("Page 9 of 10")


@patch("components.pagination.st")
def test_render_pagination_renders_middle_five_pages(
    mock_st: MagicMock,
) -> None:
    setup_streamlit_mock(mock_st)

    render_pagination(6, 10)

    assert mock_st.columns.call_count == 2
    mock_st.caption.assert_called_once_with("Page 6 of 10")


@patch("components.pagination.st")
def test_previous_button_is_disabled_on_first_page(
    mock_st: MagicMock,
) -> None:
    setup_streamlit_mock(mock_st)

    render_pagination(1, 5)

    previous_call = mock_st.button.call_args_list[0]
    assert previous_call.args[0] == "⬅ Previous"
    assert previous_call.kwargs["disabled"] is True


@patch("components.pagination.st")
def test_next_button_is_disabled_on_last_page(
    mock_st: MagicMock,
) -> None:
    setup_streamlit_mock(mock_st)

    render_pagination(5, 5)

    next_call = mock_st.button.call_args_list[-1]
    assert next_call.args[0] == "Next ➡"
    assert next_call.kwargs["disabled"] is True


@patch("components.pagination.st")
def test_current_page_button_is_disabled(
    mock_st: MagicMock,
) -> None:
    setup_streamlit_mock(mock_st)

    render_pagination(3, 5)

    page_calls = mock_st.button.call_args_list[1:-1]

    current_call = next(
        call for call in page_calls if call.args[0] == "**3**"
    )

    assert current_call.kwargs["disabled"] is True



@patch("components.pagination.st")
def test_page_info_is_displayed(
    mock_st: MagicMock,
) -> None:
    setup_streamlit_mock(mock_st)

    render_pagination(4, 8)

    mock_st.caption.assert_called_once_with("Page 4 of 8")


@patch("components.pagination.st")
def test_previous_button_updates_page_and_reruns_when_clicked(
    mock_st: MagicMock,
) -> None:
    session_state = setup_streamlit_mock(mock_st)

    # Previous is clicked; remaining buttons are not clicked.
    mock_st.button.side_effect = [True, False, False, False, False, False, False]

    render_pagination(3, 5)

    assert session_state["jobs_page"] == 2
    mock_st.rerun.assert_called_once()


@patch("components.pagination.st")
def test_next_button_updates_page_and_reruns_when_clicked(
    mock_st: MagicMock,
) -> None:
    session_state = setup_streamlit_mock(mock_st)

    # Previous, pages 1-5 are not clicked; Next is clicked.
    mock_st.button.side_effect = [False, False, False, False, False, False, True]

    render_pagination(3, 5)

    assert session_state["jobs_page"] == 4
    mock_st.rerun.assert_called_once()


@patch("components.pagination.st")
def test_other_page_button_updates_page_and_reruns(
    mock_st: MagicMock,
) -> None:
    session_state = setup_streamlit_mock(mock_st)

    # Previous, page 1 are not clicked; page 2 is clicked.
    mock_st.button.side_effect = [False, False, True, False, False, False, False]

    render_pagination(3, 5)

    assert session_state["jobs_page"] == 2
    mock_st.rerun.assert_called_once()