import json
from pathlib import Path


# Test that load_questions reads and parses the JSON file correctly
def test_load_questions(tmp_path: Path):
    questions = [
        {"question": "Who is Frodo's uncle?", "source_id": ["fellowship_pdf"]},
        {"question": "What colour is Moby Dick?", "source_id": ["moby_dick"]},
    ]
    question_file = tmp_path / "questions.json"
    question_file.write_text(json.dumps(questions))

    from evaluate import load_questions
    result = load_questions(question_file)

    assert len(result) == 2
    assert result[0]["question"] == "Who is Frodo's uncle?"


# Test that a question passes when the correct source appears in the top 5
def test_evaluate_counts_pass_when_source_found():
    from evaluate import source_matched

    question = {"question": "Who is Frodo's uncle?", "source_id": ["fellowship_pdf"]}
    mock_result = {
        "metadatas": [[{"source_id": "fellowship_pdf", "title": "The Fellowship of the Ring", "chunk_index": 0}]],
    }

    assert source_matched(question, mock_result) is True


# Test that a question fails when the correct source is not in the top 5
def test_evaluate_counts_fail_when_source_not_found():
    from evaluate import source_matched

    question = {"question": "What is Jarndyce?", "source_id": ["bleak_house"]}
    mock_result = {
        "metadatas": [[{"source_id": "sherlock_holmes", "title": "Sherlock Holmes", "chunk_index": 0}]],
    }

    assert source_matched(question, mock_result) is False


# Test that a question with multiple valid sources passes if any one is returned
def test_evaluate_passes_if_any_valid_source_found():
    from evaluate import source_matched

    question = {
        "question": "Which dictionary does the US government use?",
        "source_id": ["gpo_style_manual_2000", "gpo_style_manual_2008", "gpo_style_manual_2016"],
    }
    mock_result = {
        "metadatas": [[{"source_id": "gpo_style_manual_2016", "title": "GPO Style Manual 2016", "chunk_index": 0}]],
    }

    assert source_matched(question, mock_result) is True
