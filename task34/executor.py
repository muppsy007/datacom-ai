"""
Task 3.4 - Self-Healing Code Assistant
This simply defines the language runners and calls the one for the requested language.
"""
import sys
from typing import Callable

from rich.console import Console

from models import AttemptResult
from languages.python_runner import run as run_python
from languages.rust_runner import run as run_rust

console = Console()

RUNNERS: dict[str, Callable[..., AttemptResult]] = {
    "python": run_python,
    "rust": run_rust,
}


def run(code: str, language: str, attempt_number: int, force_fail: bool = False) -> AttemptResult:
    """We map the runner name to the language name. All we do is pull the relevant runner out.
    If a language doesn't have a map, we don't support it. So just exit with an error
    """
    runner = RUNNERS.get(language)
    if runner is None:
        console.print(f"[red]Language not currently supported: {language}[/red]")
        sys.exit(1)
    return runner(code, attempt_number, force_fail=force_fail)
