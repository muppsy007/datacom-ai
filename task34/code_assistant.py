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

from code_generator import detect_language, generate_code
from executor import run
from models import FinalOutcome

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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--force-fail", action="store_true")
    args = parser.parse_args()

    task = console.input("[bold]Enter your coding task:[/bold] ")

    console.print("\n[dim]Detecting language...[/dim]")
    language = detect_language(task)
    console.print(f"[dim]Detected language:[/dim] [cyan]{language}[/cyan]\n")

    messages = build_initial_messages(task)
    outcome: FinalOutcome | None = None

    for attempt in range(1, MAX_ATTEMPTS + 1):
        console.rule(f"Attempt {attempt}/{MAX_ATTEMPTS}")

        # Generate code
        console.print("[dim]Generating code...[/dim]")
        code = generate_code(messages)

        # Run tests
        console.print("[dim]Running tests...[/dim]")
        result = run(code, language, attempt_number=attempt, force_fail=args.force_fail)

        if result.success:
            outcome = FinalOutcome(
                success=True,
                total_attempts=attempt,
                final_code=result.code,
                last_error=None,
            )
            break

        console.print(f"[yellow]Attempt {attempt} failed.[/yellow]")
        if result.stderr:
            console.print(f"[dim]{result.stderr.strip()}[/dim]")
        
        # Add a little break to give the user time to see output
        time.sleep(3) 

        # Append the last (failed) code and message to the prompt so the next request has context
        messages.append({"role": "assistant", "content": code})
        messages.append({
            "role": "user",
            "content": f"That failed with the following error:\n\n{result.stderr}",
        })

        if attempt == MAX_ATTEMPTS:
            outcome = FinalOutcome(
                success=False,
                total_attempts=attempt,
                final_code=result.code,
                last_error=result.stderr,
            )

    assert outcome is not None
    console.rule("Result")

    if outcome.success:
        console.print(Panel(
            f"[green]All tests passed on attempt {outcome.total_attempts}/{MAX_ATTEMPTS}[/green]",
            title="Success",
            border_style="green",
        ))
    else:
        console.print(Panel(
            f"[red]Failed after {outcome.total_attempts} attempts[/red]\n\n"
            f"[dim]Last error:[/dim]\n{outcome.last_error}",
            title="Failed",
            border_style="red",
        ))

    console.print("\n[bold]Final code:[/bold]")
    console.print(Syntax(outcome.final_code, language, theme="monokai"))


if __name__ == "__main__":
    main()
