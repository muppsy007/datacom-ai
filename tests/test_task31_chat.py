"""
Tests for task31 chat - covers database schema creation, message persistence, the load_messages 
limit and chronological ordering behaviour.
"""

def _init():
    from task31.chat import init_db
    return init_db(":memory:")


def test_init_db_creates_messages_table():
    conn = _init()
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='messages'")
    assert cursor.fetchone() is not None


def test_init_db_is_idempotent(tmp_path):
    from task31.chat import init_db

    db_path = str(tmp_path / "test.db")
    init_db(db_path)
    conn = init_db(db_path)

    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='messages'")
    assert cursor.fetchone() is not None


def test_save_message_inserts_row():
    from task31.chat import save_message
    conn = _init()
    save_message(conn, "user", "Hello")
    count = conn.execute("SELECT COUNT(*) FROM messages").fetchone()[0]
    assert count == 1


def test_save_message_persists_role_and_content():
    from task31.chat import save_message
    conn = _init()
    save_message(conn, "user", "Hello there")
    row = conn.execute("SELECT role, content FROM messages").fetchone()
    assert row[0] == "user"
    assert row[1] == "Hello there"


def test_load_messages_returns_in_chronological_order():
    from task31.chat import load_messages, save_message
    conn = _init()
    save_message(conn, "user", "first")
    save_message(conn, "assistant", "second")
    save_message(conn, "user", "third")

    messages = load_messages(conn)
    assert messages[0]["content"] == "first"
    assert messages[1]["content"] == "second"
    assert messages[2]["content"] == "third"


def test_load_messages_respects_limit():
    from task31.chat import load_messages, save_message
    conn = _init()
    for i in range(15):
        save_message(conn, "user", f"message {i}")

    messages = load_messages(conn, limit=10)
    assert len(messages) == 10


def test_load_messages_returns_most_recent_when_limited():
    from task31.chat import load_messages, save_message
    conn = _init()
    for i in range(15):
        save_message(conn, "user", f"message {i}")

    messages = load_messages(conn, limit=10)
    # should have messages 5 to 14, in order
    assert messages[0]["content"] == "message 5"
    assert messages[-1]["content"] == "message 14"


def test_load_messages_returns_correct_role_format():
    from task31.chat import load_messages, save_message
    conn = _init()
    save_message(conn, "user", "hi")
    save_message(conn, "assistant", "hello")

    messages = load_messages(conn)
    assert messages[0]["role"] == "user"
    assert messages[1]["role"] == "assistant"


def test_load_messages_empty_db_returns_empty_list():
    from task31.chat import load_messages
    conn = _init()
    assert load_messages(conn) == []


def test_save_message_persists_usage_fields():
    from task31.chat import save_message
    conn = _init()
    save_message(conn, "assistant", "Hello", prompt_tokens=100, completion_tokens=50, cost_usd=0.000775, latency_ms=342.5)
    row = conn.execute("SELECT prompt_tokens, completion_tokens, cost_usd, latency_ms FROM messages").fetchone()
    assert row[0] == 100
    assert row[1] == 50
    assert abs(row[2] - 0.000775) < 1e-9
    assert row[3] == 342.5


def test_save_message_usage_fields_nullable_for_user_messages():
    from task31.chat import save_message
    conn = _init()
    save_message(conn, "user", "Hello")
    row = conn.execute("SELECT prompt_tokens, completion_tokens, cost_usd, latency_ms FROM messages").fetchone()
    assert row[0] is None
    assert row[1] is None
    assert row[2] is None
    assert row[3] is None
