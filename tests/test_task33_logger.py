"""
Tests for task33 travel_agent_logger - verifies schema creation and log_run persistence.
Uses an in-memory SQLite database using ":memory:" init so no files are written to disk.
"""

def test_init_db_creates_agent_runs_table():
    from task33.travel_agent_logger import init_db

    conn = init_db(":memory:")
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='agent_runs'")
    assert cursor.fetchone() is not None


def test_init_db_is_idempotent():
    from task33.travel_agent_logger import init_db

    # Calling twice on the same connection should not raise
    conn = init_db(":memory:")
    init_db(":memory:")


def test_log_run_inserts_row():
    from task33.travel_agent_logger import init_db, log_run

    conn = init_db(":memory:")
    log_run(
        conn=conn,
        prompt="Plan a trip from Christchurch to Auckland",
        tools="search_flights, get_weather",
        token_count=150,
        estimated_cost=0.0025,
        itinerary_actual_cost_nzd=320.0,
        constraint_satisfied=1,
        scratchpad='[{"tool": "search_flights", "reasoning": "Finding outbound flight to AKL"}]',
    )

    cursor = conn.execute("SELECT COUNT(*) FROM agent_runs")
    assert cursor.fetchone()[0] == 1


def test_log_run_persists_correct_values():
    from task33.travel_agent_logger import init_db, log_run

    conn = init_db(":memory:")
    log_run(
        conn=conn,
        prompt="Plan a trip from Christchurch to Auckland",
        tools="search_flights, get_weather",
        token_count=150,
        estimated_cost=0.0025,
        itinerary_actual_cost_nzd=320.0,
        constraint_satisfied=1,
        scratchpad='[{"tool": "search_flights", "reasoning": "Finding outbound flight to AKL"}]',
    )

    row = conn.execute(
        "SELECT prompt, tools_used, tokens_used, est_cost_usd, itinerary_actual_cost_nzd, constraint_satisfied FROM agent_runs"
    ).fetchone()

    assert row[0] == "Plan a trip from Christchurch to Auckland"
    assert row[1] == "search_flights, get_weather"
    assert row[2] == 150
    assert abs(row[3] - 0.0025) < 1e-9
    assert row[4] == 320.0
    assert row[5] == 1


def test_log_run_multiple_runs():
    from task33.travel_agent_logger import init_db, log_run

    conn = init_db(":memory:")
    for i in range(3):
        log_run(
            conn=conn,
            prompt=f"Trip {i}",
            tools="search_flights",
            token_count=100,
            estimated_cost=0.001,
            itinerary_actual_cost_nzd=200.0,
            constraint_satisfied=1,
            scratchpad="[]",
        )

    count = conn.execute("SELECT COUNT(*) FROM agent_runs").fetchone()[0]
    assert count == 3
