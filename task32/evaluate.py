'''
Task 3.2 - RAG QA
Evaluates retrieval quality by running each question from the answer key through the retrieval 
pipeline and computing Recall@5 (the proportion of questions where the correct source appears in 
the top 5 results).
'''
import json
from pathlib import Path
from typing import Any

from retrieval import retrieve
from rich.console import Console
from rich.table import Table


console = Console()

def evaluate(question_path: str = str(Path(__file__).resolve().parent / "eval" / "questions.json")) -> None:
    question_file = Path(question_path)
    question_data = load_questions(question_file)

    table = Table(title="Recall@5 Evaluation")
    table.add_column("Question")
    table.add_column("Pass")
    table.add_column("Sources Returned")

    total_passed = 0
    total_questions = len(question_data)
    for question in question_data:
        # Get the result for the question and pull the source_ids
        results = retrieve(question["question"])
        returned_source_ids = [meta["source_id"] for meta in results["metadatas"][0]] # type: ignore
        
        # A pass is if the expected source is found in at least one of the result sources
        passed = source_matched(question, results)
        if passed:
            total_passed += 1

        table.add_row(
            question["question"],
            "[green]Yes[/green]" if passed else "[red]No[/red]",
            ", ".join(returned_source_ids),
        )

    recall_score = (total_passed / total_questions) 
    console.print(table)
    console.print(f"[bold red]recall@5 score: {recall_score:.2%}")

def source_matched(question: dict[str, Any], results: Any) -> bool:
    returned_source_ids = [meta["source_id"] for meta in results["metadatas"][0]]
    return any(sid in returned_source_ids for sid in question["source_id"])

def load_questions(path: Path) -> list[dict[str, Any]]:
    with open(path) as f:
        return json.load(f)
    
def main():
    evaluate()

if __name__ == "__main__":
    main()

