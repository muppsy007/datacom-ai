'''
Task 3.2 - RAG QA
Evaluates retrieval quality by running each question from the answer key through the retrieval 
pipeline and computing Recall@5 (the proportion of questions where the correct source appears in 
the top 5 results).
'''
import json
from pathlib import Path
from typing import Any

from task32.retrieval import retrieve, save_retrieval_run
from rich.console import Console
from rich.table import Table


console = Console()

def evaluate(question_path: str = str(Path(__file__).resolve().parent / "eval" / "questions.json")) -> dict[str, Any]:
    question_file = Path(question_path)
    question_data = load_questions(question_file)

    results_list: list[dict[str, Any]] = []
    total_passed = 0
    total_questions = len(question_data)
    for question in question_data:
        # Get the result for the question and pull the source_ids
        results, latency_ms = retrieve(question["question"])
        returned_source_ids = [meta["source_id"] for meta in results["metadatas"][0]] # type: ignore

        # A pass is if the expected source is found in at least one of the result sources
        passed = source_matched(question, results)
        if passed:
            total_passed += 1

        save_retrieval_run(
            query=question["question"],
            latency_ms=latency_ms,
            source="evaluate",
            passed=1 if passed else 0,
            returned_sources=json.dumps(returned_source_ids),
        )

        results_list.append({
            "question": question["question"],
            "passed": passed,
            "returned_sources": returned_source_ids,
        })

    recall_score = total_passed / total_questions

    return {
        "results": results_list,
        "recall_score": recall_score,
        "total_passed": total_passed,
        "total_questions": total_questions,
    }

def source_matched(question: dict[str, Any], results: Any) -> bool:
    returned_source_ids = [meta["source_id"] for meta in results["metadatas"][0]]
    return any(sid in returned_source_ids for sid in question["source_id"])

def load_questions(path: Path) -> list[dict[str, Any]]:
    with open(path) as f:
        return json.load(f)
    
def main():
    data = evaluate()

    table = Table(title="Recall@5 Evaluation")
    table.add_column("Question")
    table.add_column("Pass")
    table.add_column("Sources Returned")

    for row in data["results"]:
        table.add_row(
            row["question"],
            "[green]Yes[/green]" if row["passed"] else "[red]No[/red]",
            ", ".join(row["returned_sources"]),
        )

    console.print(table)
    console.print(f"[bold red]recall@5 score: {data['recall_score']:.2%}")

if __name__ == "__main__":
    main()
