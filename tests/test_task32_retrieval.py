import numpy as np
from unittest.mock import MagicMock, patch


# Test that retrieve() returns n_results results
def test_retrieve_returns_correct_number_of_results():
    mock_collection = MagicMock()
    mock_collection.query.return_value = {
        "ids": [["doc_0", "doc_1", "doc_2", "doc_3", "doc_4"]],
        "documents": [["chunk 0", "chunk 1", "chunk 2", "chunk 3", "chunk 4"]],
        "metadatas": [[
            {"source_id": "moby_dick", "title": "Moby Dick", "chunk_index": 0},
            {"source_id": "moby_dick", "title": "Moby Dick", "chunk_index": 1},
            {"source_id": "moby_dick", "title": "Moby Dick", "chunk_index": 2},
            {"source_id": "moby_dick", "title": "Moby Dick", "chunk_index": 3},
            {"source_id": "moby_dick", "title": "Moby Dick", "chunk_index": 4},
        ]],
        "distances": [[0.1, 0.2, 0.3, 0.4, 0.5]],
        "embeddings": None,
        "uris": None,
        "data": None,
        "included": ["metadatas", "documents", "distances"],
    }

    with patch("task32.retrieval.chroma_client") as mock_client, \
         patch("task32.retrieval.model") as mock_model:
        mock_client.get_collection.return_value = mock_collection
        mock_model.encode.return_value = np.array([0.1] * 384)

        from task32.retrieval import retrieve
        results, latency_ms = retrieve("What is the white whale?", n_results=5)

    assert len(results["ids"][0]) == 5
    assert latency_ms >= 0


# Test that retrieve() passes the query embedding to Chroma
def test_retrieve_queries_chroma_with_embedding():
    mock_collection = MagicMock()
    mock_collection.query.return_value = {
        "ids": [[]],
        "documents": [[]],
        "metadatas": [[]],
        "distances": [[]],
        "embeddings": None,
        "uris": None,
        "data": None,
        "included": ["metadatas", "documents", "distances"],
    }

    fake_embedding = np.array([0.5] * 384)

    with patch("task32.retrieval.chroma_client") as mock_client, \
         patch("task32.retrieval.model") as mock_model:
        mock_client.get_collection.return_value = mock_collection
        mock_model.encode.return_value = fake_embedding

        from task32.retrieval import retrieve
        retrieve("Who is Ahab?")

    mock_collection.query.assert_called_once_with(
        query_embeddings=[fake_embedding.tolist()],
        n_results=5,
    )


# Test that retrieve() uses get_collection, not get_or_create_collection
# If the collection doesn't exist, we want an error, not a silent empty collection
def test_retrieve_uses_get_collection_not_create():
    with patch("task32.retrieval.chroma_client") as mock_client, \
         patch("task32.retrieval.model"):
        mock_client.get_collection.return_value = MagicMock()
        mock_client.get_collection.return_value.query.return_value = {
            "ids": [[]], "documents": [[]], "metadatas": [[]], "distances": [[]],
            "embeddings": None, "uris": None, "data": None,
            "included": ["metadatas", "documents", "distances"],
        }

        from task32.retrieval import retrieve
        retrieve("test query")

    mock_client.get_collection.assert_called_once_with(name="book_corpus")
    mock_client.get_or_create_collection.assert_not_called()


# Test that save_retrieval_run writes a record to the database
def test_save_retrieval_run_inserts_record(tmp_path):
    import sqlite3
    db_path = str(tmp_path / "test_metrics.db")

    with patch.dict("os.environ", {"DB_PATH": db_path}):
        from task32.retrieval import save_retrieval_run
        save_retrieval_run(
            query="test question",
            latency_ms=42.5,
            source="evaluate",
            passed=1,
            returned_sources='["moby_dick"]',
        )

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM retrieval_runs").fetchall()
    conn.close()

    assert len(rows) == 1
    assert rows[0]["query"] == "test question"
    assert rows[0]["latency_ms"] == 42.5
    assert rows[0]["source"] == "evaluate"
    assert rows[0]["passed"] == 1
    assert rows[0]["returned_sources"] == '["moby_dick"]'


# Test that save_retrieval_run leaves passed/returned_sources null when not provided
def test_save_retrieval_run_nullable_fields(tmp_path):
    import sqlite3
    db_path = str(tmp_path / "test_metrics.db")

    with patch.dict("os.environ", {"DB_PATH": db_path}):
        from task32.retrieval import save_retrieval_run
        save_retrieval_run(query="test question", latency_ms=10.0)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM retrieval_runs").fetchall()
    conn.close()

    assert len(rows) == 1
    assert rows[0]["passed"] is None
    assert rows[0]["returned_sources"] is None
