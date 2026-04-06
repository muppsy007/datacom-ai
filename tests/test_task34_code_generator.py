"""
Tests for task34 code_generator — focuses on extract_code since detect_language
and generate_code require a live LLM call and are covered by integration use.
"""
from task34.code_generator import extract_code


def test_extract_code_strips_rust_fence():
    raw = "```rust\nfn main() {}\n```"
    assert extract_code(raw) == "fn main() {}"


def test_extract_code_strips_generic_fence():
    raw = "```\nfn main() {}\n```"
    assert extract_code(raw) == "fn main() {}"


def test_extract_code_returns_raw_when_no_fence():
    raw = "fn main() {}"
    assert extract_code(raw) == "fn main() {}"


def test_extract_code_strips_surrounding_whitespace():
    raw = "  fn main() {}  "
    assert extract_code(raw) == "fn main() {}"


def test_extract_code_strips_python_fence():
    raw = "```python\ndef hello():\n    pass\n```"
    assert extract_code(raw) == "def hello():\n    pass"
