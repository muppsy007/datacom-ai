"""
Task 3.4 - Self-Healing Code Assistant
The code generation orchestrator. This is called by the code_assistant entry point and will:
1. Detect the requested language from the user prompt
2. Generate the code based on the running message history provided by code_assistant
3. Manually (regex) strips out any markdown fences the code response comes back with
"""
import os
import re

import dotenv
from openai import OpenAI
from rich.console import Console

dotenv.load_dotenv()

console = Console()

client = OpenAI(
    api_key=os.environ["OPENAI_API_KEY"],
    base_url=os.environ["OPENAI_BASE_URL"],
)

MODEL = os.environ["MODEL_NAME"]


def extract_code(response: str) -> str:
    """Just remove the ```rust type markdown fences LLM places around code"""
    match = re.search(r"```(?:\w+)?\n(.*?)```", response, re.DOTALL)
    return match.group(1).strip() if match else response.strip()


def detect_language(task: str) -> str:
    """Simple LLM call to work out the langague being referred to in the prompt"""
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You detect the target programming language from a coding task description. "
                    "Reply with only the lowercase language name and nothing else. "
                    "Examples: rust, python, go, typescript"
                ),
            },
            {"role": "user", "content": task},
        ],
    )
    # Strip and lowercase the response
    return response.choices[0].message.content.strip().lower()


def generate_code(messages: list[dict[str, str]]) -> str:
    """Makes an LLM call to get code as requested by the prompt and history"""
    chunks = []
    stream = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        stream=True,
    )
    for chunk in stream:
        text = chunk.choices[0].delta.content or ""
        if text:
            console.print(text, end="", markup=False)
            chunks.append(text)
    console.print()
    return extract_code("".join(chunks))
