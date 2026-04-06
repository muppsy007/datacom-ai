import subprocess
from pathlib import Path

from models import AttemptResult
from rich.console import Console

console = Console()

CARGO_TOML = """\
[package]
name = "attempt"
version = "0.1.0"
edition = "2024"
"""


def _in_container() -> bool:
    """Detect if we're running inside a Docker container."""
    return Path("/.dockerenv").exists()


def run(code: str, attempt_number: int, force_fail: bool = False) -> AttemptResult:
    project_dir = Path(__file__).parent.parent / "tmp" / f"attempt_{attempt_number}"
    src_dir = project_dir / "src"
    src_dir.mkdir(parents=True, exist_ok=True)

    # Write the generated code to file with Cargo.toml template
    (project_dir / "Cargo.toml").write_text(CARGO_TOML)
    (src_dir / "lib.rs").write_text(code if not (force_fail and attempt_number == 1) else code + "\nthis is not valid rust !!!")

    if _in_container():
        # Running inside Docker — use cargo directly (Rust installed in image)
        console.print("[yellow](rust_runner) running cargo test directly (inside container)")
        result = subprocess.run(
            ["cargo", "test"],
            capture_output=True,
            text=True,
            cwd=project_dir,
        )
    else:
        # Running on host — use Docker for isolation
        console.print("[yellow](rust_runner) ensuring rust:latest Docker image is available...")
        subprocess.run(["docker", "pull", "rust:latest"])

        cargo_location = subprocess.run(
            ["docker", "run", "--rm", "rust:latest", "which", "cargo"],
            capture_output=True, text=True
        ).stdout.strip()
        console.print(f"[yellow](rust_runner) using cargo: {cargo_location} (inside Docker)")

        result = subprocess.run(
            [
                "docker", "run", "--rm",
                "-v", f"{project_dir.resolve()}:/usr/src/app",
                "-w", "/usr/src/app",
                "rust:latest",
                "cargo", "test",
            ],
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
