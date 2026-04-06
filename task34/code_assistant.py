"""
Task 3.4 - Self-Healing Code Assistant
This is the main entry file for the process. Run this and it will prompt you for a task
Optionally add --force-fail when running the file and it will intentionally fail to demo the loop
"""
import argparse
import time

import dotenv
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

from collections.abc import Generator

from code_generator import detect_language, generate_code
from executor import run
from models import AttemptResult

dotenv.load_dotenv()

console = Console()

MAX_ATTEMPTS = 3

SYSTEM_PROMPT = (
    "You are an expert software engineer. "
    "When given a coding task, write correct, idiomatic code that includes tests. "
    "For Rust, include #[cfg(test)] blocks with #[test] functions. "
    "Return only the source code with no explanation."
)


def build_initial_messages(task: str) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": task},
    ]


def run_task(task: str, force_fail: bool = False) -> Generator[AttemptResult]:
    """Run the self-healing code generation loop, yielding each AttemptResult."""
    language = detect_language(task)
    messages = build_initial_messages(task)

    for attempt in range(1, MAX_ATTEMPTS + 1):
        code = generate_code(messages)
        result = run(code, language, attempt_number=attempt, force_fail=force_fail)

        yield result

        if result.success:
            break

        # Append the last (failed) code and message to the prompt so the next request has context
        messages.append({"role": "assistant", "content": code})
        messages.append({
            "role": "user",
            "content": f"That failed with the following error:\n\n{result.stderr}",
        })


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--force-fail", action="store_true")
    args = parser.parse_args()

    task = console.input("[cyan][bold]Enter your coding task:[/bold] ")

    last_result: AttemptResult | None = None
    for result in run_task(task, force_fail=args.force_fail):
        last_result = result
        console.rule(f"Attempt {result.attempt_number}/{MAX_ATTEMPTS}")

        if result.success:
            break

        console.print(f"[yellow]Attempt {result.attempt_number} failed.[/yellow]")
        if result.stderr:
            console.print(f"[dim]{result.stderr.strip()}[/dim]")

        # Add a little break to give the user time to see output
        time.sleep(3)

    assert last_result is not None
    console.rule("Result")

    if last_result.success:
        console.print(Panel(
            f"[green]All tests passed on attempt {last_result.attempt_number}/{MAX_ATTEMPTS}[/green]",
            title="Success",
            border_style="green",
        ))
    else:
        console.print(Panel(
            f"[red]Failed after {last_result.attempt_number} attempts[/red]\n\n"
            f"[dim]Last error:[/dim]\n{last_result.stderr}",
            title="Failed",
            border_style="red",
        ))

    language = detect_language(task)
    console.print("\n[bold]Final code:[/bold]")
    console.print(Syntax(last_result.code, language, theme="monokai"))


if __name__ == "__main__":
    main()
