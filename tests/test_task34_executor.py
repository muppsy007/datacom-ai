"""
Tests for task34 executor — verifies language dispatch and unsupported language handling.
"""
import sys
from unittest.mock import MagicMock, patch

import pytest


def test_run_dispatches_to_rust_runner():
    from task34.executor import run

    mock_result = MagicMock()
    with patch("task34.executor.RUNNERS", {"rust": MagicMock(return_value=mock_result)}) as mock_runners:
        result = run("fn main() {}", "rust", attempt_number=1)

    mock_runners["rust"].assert_called_once_with("fn main() {}", 1, force_fail=False)
    assert result is mock_result


def test_run_passes_force_fail_to_runner():
    from task34.executor import run

    mock_runner = MagicMock()
    with patch("task34.executor.RUNNERS", {"rust": mock_runner}):
        run("fn main() {}", "rust", attempt_number=2, force_fail=True)

    mock_runner.assert_called_once_with("fn main() {}", 2, force_fail=True)


def test_run_exits_on_unsupported_language():
    from task34.executor import run

    with pytest.raises(SystemExit):
        run("print('hi')", "cobol", attempt_number=1)
