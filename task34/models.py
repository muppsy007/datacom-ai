"""
Task 3.4 - Self-Healing Code Assistant
Simple definition of dataclass structures for attempts and final outcomes
"""
from dataclasses import dataclass


@dataclass
class AttemptResult:
    success: bool
    code: str  # plain source, markdown fences stripped
    stdout: str
    stderr: str
    attempt_number: int


@dataclass
class FinalOutcome:
    success: bool
    total_attempts: int
    final_code: str
    last_error: str | None
