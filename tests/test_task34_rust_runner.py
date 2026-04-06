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


def _patch_file(monkeypatch, tmp_path):
    """Redirect Path(__file__) so project_dir resolves inside tmp_path."""
    import task34.languages.rust_runner as rust_runner
    monkeypatch.setattr(rust_runner, "__file__", str(tmp_path / "languages" / "rust_runner.py"))


def test_run_writes_cargo_toml_and_lib_rs(tmp_path, monkeypatch):
    from task34.languages.rust_runner import CARGO_TOML, run

    _patch_file(monkeypatch, tmp_path)
    code = "pub fn add(a: i32, b: i32) -> i32 { a + b }"

    with patch("task34.languages.rust_runner.subprocess.run", return_value=_make_completed_process(0)):
        run(code, attempt_number=1)

    project_dir = tmp_path / "tmp" / "attempt_1"
    assert (project_dir / "Cargo.toml").read_text() == CARGO_TOML
    assert (project_dir / "src" / "lib.rs").read_text() == code


def test_run_returns_success_on_zero_exit(tmp_path, monkeypatch):
    from task34.languages.rust_runner import run

    _patch_file(monkeypatch, tmp_path)
    code = "pub fn add(a: i32, b: i32) -> i32 { a + b }"

    with patch("task34.languages.rust_runner.subprocess.run", return_value=_make_completed_process(0, stdout="test passed")):
        result = run(code, attempt_number=1)

    assert result.success is True
    assert result.code == code
    assert result.attempt_number == 1


def test_run_returns_failure_on_nonzero_exit(tmp_path, monkeypatch):
    from task34.languages.rust_runner import run

    _patch_file(monkeypatch, tmp_path)
    code = "this is not valid rust !!!"
    stderr_text = "error: expected item"

    with patch("task34.languages.rust_runner.subprocess.run", return_value=_make_completed_process(101, stderr=stderr_text)):
        result = run(code, attempt_number=1)

    assert result.success is False
    assert result.stderr == stderr_text


def test_force_fail_appends_invalid_rust_on_attempt_1(tmp_path, monkeypatch):
    from task34.languages.rust_runner import run

    _patch_file(monkeypatch, tmp_path)
    code = "pub fn add(a: i32, b: i32) -> i32 { a + b }"

    with patch("task34.languages.rust_runner.subprocess.run", return_value=_make_completed_process(1, stderr="error: expected item")):
        run(code, attempt_number=1, force_fail=True)

    lib_rs = tmp_path / "tmp" / "attempt_1" / "src" / "lib.rs"
    assert "this is not valid rust" in lib_rs.read_text()


def test_force_fail_does_not_corrupt_attempt_2(tmp_path, monkeypatch):
    from task34.languages.rust_runner import run

    _patch_file(monkeypatch, tmp_path)
    code = "pub fn add(a: i32, b: i32) -> i32 { a + b }"

    with patch("task34.languages.rust_runner.subprocess.run", return_value=_make_completed_process(0)):
        run(code, attempt_number=2, force_fail=True)

    lib_rs = tmp_path / "tmp" / "attempt_2" / "src" / "lib.rs"
    assert lib_rs.read_text() == code
