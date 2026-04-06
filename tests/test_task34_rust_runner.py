"""
Tests for task34 rust_runner — verifies file layout, subprocess invocation,
AttemptResult mapping, and force_fail behaviour. cargo is never actually run.
"""
from pathlib import Path
from unittest.mock import MagicMock, patch


def _make_completed_process(returncode: int, stdout: str = "", stderr: str = "") -> MagicMock:
    cp = MagicMock()
    cp.returncode = returncode
    cp.stdout = stdout
    cp.stderr = stderr
    return cp


def test_run_writes_cargo_toml_and_lib_rs(tmp_path, monkeypatch):
    from task34.languages.rust_runner import CARGO_TOML, run

    code = "pub fn add(a: i32, b: i32) -> i32 { a + b }"

    monkeypatch.chdir(tmp_path)
    with patch("task34.languages.rust_runner.subprocess.run", return_value=_make_completed_process(0)):
        run(code, attempt_number=1)

    project_dir = tmp_path / "tmp" / "attempt_1"
    assert (project_dir / "Cargo.toml").read_text() == CARGO_TOML
    assert (project_dir / "src" / "lib.rs").read_text() == code


def test_run_returns_success_on_zero_exit(tmp_path):
    from task34.languages.rust_runner import CARGO_TOML, run

    code = "pub fn add(a: i32, b: i32) -> i32 { a + b }"

    with patch("task34.languages.rust_runner.Path") as mock_path_cls, \
         patch("task34.languages.rust_runner.subprocess.run", return_value=_make_completed_process(0, stdout="test passed")):

        # Redirect filesystem ops to tmp_path
        def fake_truediv(self, other):
            return tmp_path / str(other)

        project_dir = tmp_path / "attempt_1"
        src_dir = project_dir / "src"

        mock_tmp = MagicMock()
        mock_project = MagicMock()
        mock_src = MagicMock()
        mock_src.mkdir = MagicMock()

        mock_path_cls.return_value.__truediv__ = MagicMock(return_value=mock_project)
        mock_project.__truediv__ = MagicMock(return_value=mock_src)

        result = run(code, attempt_number=1)

    assert result.success is True
    assert result.code == code
    assert result.attempt_number == 1


def test_run_returns_failure_on_nonzero_exit(tmp_path):
    from task34.languages.rust_runner import run

    code = "this is not valid rust !!!"
    stderr_text = "error: expected item"

    with patch("task34.languages.rust_runner.Path") as mock_path_cls, \
         patch("task34.languages.rust_runner.subprocess.run",
               return_value=_make_completed_process(101, stderr=stderr_text)):

        mock_project = MagicMock()
        mock_src = MagicMock()
        mock_path_cls.return_value.__truediv__ = MagicMock(return_value=mock_project)
        mock_project.__truediv__ = MagicMock(return_value=mock_src)

        result = run(code, attempt_number=1)

    assert result.success is False
    assert result.stderr == stderr_text


def test_force_fail_appends_invalid_rust_on_attempt_1(tmp_path):
    from task34.languages.rust_runner import run

    code = "pub fn add(a: i32, b: i32) -> i32 { a + b }"
    captured_args = {}

    def fake_subprocess_run(cmd, **kwargs):
        captured_args["cwd"] = kwargs.get("cwd")
        return _make_completed_process(1, stderr="error: expected item")

    with patch("task34.languages.rust_runner.Path") as mock_path_cls, \
         patch("task34.languages.rust_runner.subprocess.run", side_effect=fake_subprocess_run):

        mock_project = MagicMock()
        mock_src = MagicMock()
        written = {}

        def write_text(content):
            written["content"] = content

        mock_src.__truediv__ = MagicMock(return_value=MagicMock(write_text=write_text))
        mock_path_cls.return_value.__truediv__ = MagicMock(return_value=mock_project)
        mock_project.__truediv__ = MagicMock(return_value=mock_src)

        run(code, attempt_number=1, force_fail=True)

    assert "this is not valid rust" in written.get("content", "")


def test_force_fail_does_not_corrupt_attempt_2(tmp_path):
    from task34.languages.rust_runner import run

    code = "pub fn add(a: i32, b: i32) -> i32 { a + b }"
    written = {}

    def fake_subprocess_run(cmd, **kwargs):
        return _make_completed_process(0)

    with patch("task34.languages.rust_runner.Path") as mock_path_cls, \
         patch("task34.languages.rust_runner.subprocess.run", side_effect=fake_subprocess_run):

        mock_project = MagicMock()
        mock_src = MagicMock()

        def write_text(content):
            written["content"] = content

        mock_src.__truediv__ = MagicMock(return_value=MagicMock(write_text=write_text))
        mock_path_cls.return_value.__truediv__ = MagicMock(return_value=mock_project)
        mock_project.__truediv__ = MagicMock(return_value=mock_src)

        run(code, attempt_number=2, force_fail=True)

    assert written.get("content") == code
