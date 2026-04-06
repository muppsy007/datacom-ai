"""
Tests for task34 code_assistant — focuses on the self-healing retry loop:
success on first attempt, recovery after failure, and exhausting all attempts.
"""
from unittest.mock import MagicMock, patch

from task34.models import AttemptResult


def _make_result(success: bool, stderr: str = "") -> AttemptResult:
    return AttemptResult(
        success=success,
        code="fn add(a: i32, b: i32) -> i32 { a + b }",
        stdout="",
        stderr=stderr,
        attempt_number=1,
    )


def test_build_initial_messages_contains_system_and_user():
    from task34.code_assistant import build_initial_messages

    messages = build_initial_messages("write quicksort in rust")

    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"
    assert "write quicksort in rust" in messages[1]["content"]


def test_build_initial_messages_system_prompt_mentions_tests():
    from task34.code_assistant import build_initial_messages

    messages = build_initial_messages("write quicksort in rust")

    assert "test" in messages[0]["content"].lower()


def test_loop_succeeds_on_first_attempt():
    from task34.code_assistant import main

    success_result = _make_result(success=True)

    with patch("task34.code_assistant.detect_language", return_value="rust"), \
         patch("task34.code_assistant.generate_code", return_value=success_result.code) as mock_generate, \
         patch("task34.code_assistant.run", return_value=success_result) as mock_run, \
         patch("task34.code_assistant.console") as mock_console, \
         patch("sys.argv", ["code_assistant.py"]):

        mock_console.input.return_value = "write an add function in rust"
        main()

    mock_generate.assert_called_once()
    mock_run.assert_called_once()


def test_loop_appends_error_to_messages_on_failure():
    from task34.code_assistant import build_initial_messages, generate_code, run

    fail_result = _make_result(success=False, stderr="error[E0308]: mismatched types")
    success_result = _make_result(success=True)

    captured_messages = []

    def fake_generate(messages):
        captured_messages.append(list(messages))
        return "fn add(a: i32, b: i32) -> i32 { a + b }"

    with patch("task34.code_assistant.detect_language", return_value="rust"), \
         patch("task34.code_assistant.generate_code", side_effect=fake_generate), \
         patch("task34.code_assistant.run", side_effect=[fail_result, success_result]), \
         patch("task34.code_assistant.time.sleep"), \
         patch("task34.code_assistant.console") as mock_console, \
         patch("sys.argv", ["code_assistant.py"]):

        mock_console.input.return_value = "write an add function in rust"
        from task34.code_assistant import main
        main()

    # Second call should have the error appended to messages
    assert len(captured_messages) == 2
    second_call_messages = captured_messages[1]
    roles = [m["role"] for m in second_call_messages]
    assert "assistant" in roles
    assert "user" in roles
    error_message = next(m for m in second_call_messages if m["role"] == "user" and "error" in m["content"].lower())
    assert "mismatched types" in error_message["content"]


def test_loop_exhausts_max_attempts_and_reports_failure():
    from task34.code_assistant import MAX_ATTEMPTS, main

    fail_result = _make_result(success=False, stderr="error: something went wrong")
    all_failures = [fail_result] * MAX_ATTEMPTS

    printed_panels = []

    with patch("task34.code_assistant.detect_language", return_value="rust"), \
         patch("task34.code_assistant.generate_code", return_value=fail_result.code), \
         patch("task34.code_assistant.run", side_effect=all_failures), \
         patch("task34.code_assistant.time.sleep"), \
         patch("task34.code_assistant.console") as mock_console, \
         patch("sys.argv", ["code_assistant.py"]):

        mock_console.input.return_value = "write an add function in rust"
        main()

    # Console should have printed a failure panel — check rule was called MAX_ATTEMPTS times
    assert mock_console.rule.call_count >= MAX_ATTEMPTS


def test_loop_does_not_exceed_max_attempts():
    from task34.code_assistant import MAX_ATTEMPTS, main

    fail_result = _make_result(success=False, stderr="error")
    run_call_count = []

    def counting_run(*args, **kwargs):
        run_call_count.append(1)
        return fail_result

    with patch("task34.code_assistant.detect_language", return_value="rust"), \
         patch("task34.code_assistant.generate_code", return_value=fail_result.code), \
         patch("task34.code_assistant.run", side_effect=counting_run), \
         patch("task34.code_assistant.time.sleep"), \
         patch("task34.code_assistant.console") as mock_console, \
         patch("sys.argv", ["code_assistant.py"]):

        mock_console.input.return_value = "write an add function in rust"
        main()

    assert len(run_call_count) == MAX_ATTEMPTS
