import subprocess
from pathlib import Path

from models import AttemptResult

CARGO_TOML = """\
[package]
name = "attempt"
version = "0.1.0"
edition = "2024"
"""


def run(code: str, attempt_number: int, force_fail: bool = False) -> AttemptResult:
    project_dir = Path("tmp") / f"attempt_{attempt_number}"
    src_dir = project_dir / "src"
    src_dir.mkdir(parents=True, exist_ok=True)

    (project_dir / "Cargo.toml").write_text(CARGO_TOML)
    (src_dir / "lib.rs").write_text(code if not (force_fail and attempt_number == 1) else code + "\nthis is not valid rust !!!")

    result = subprocess.run(
        ["cargo", "test"],
        cwd=project_dir,
        capture_output=True,
        text=True,
    )

    return AttemptResult(
        success=result.returncode == 0,
        code=code,
        stdout=result.stdout,
        stderr=result.stderr,
        attempt_number=attempt_number,
    )
