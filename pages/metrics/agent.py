import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st

METRICS_DB = Path(__file__).resolve().parent.parent.parent / "metrics.db"


def _get_agent_runs() -> list[dict]:
    """Read all agent runs from the DB. Never writes."""
    if not METRICS_DB.exists():
        return []
    conn = sqlite3.connect(str(METRICS_DB))
    conn.row_factory = sqlite3.Row

    table = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='agent_runs'"
    ).fetchone()
    if not table:
        conn.close()
        return []

    rows = conn.execute(
        "SELECT prompt, est_cost_usd, budget_nzd, itinerary_actual_cost_nzd, constraint_satisfied "
        "FROM agent_runs ORDER BY id"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def render_agent_tab():
    runs = _get_agent_runs()

    if not runs:
        st.info("No agent data yet. Head to the Trip Planner page to run some prompts.")
        if st.button("Go to Trip Planner"):
            st.switch_page("pages/3_Trip_Planner.py")
        return

    total_runs = len(runs)
    constraints_met = sum(1 for r in runs if r["constraint_satisfied"])
    success_rate = constraints_met / total_runs
    avg_cost = sum(r["est_cost_usd"] for r in runs) / total_runs

    # --- Metric cards ---
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Runs", total_runs)
    with col2:
        st.metric("Constraints Met", constraints_met)
    with col3:
        st.metric("Success Rate", f"{success_rate:.0%}")
    with col4:
        st.metric("Avg LLM Cost", f"${avg_cost:.4f}")

    # --- Runs table ---
    df = pd.DataFrame(
        [
            {
                "Prompt": r["prompt"],
                "Budget": f"NZ${r['budget_nzd']:.2f}" if r["budget_nzd"] else "—",
                "Actual": f"NZ${r['itinerary_actual_cost_nzd']:.2f}" if r["itinerary_actual_cost_nzd"] else "—",
                "Result": "PASS" if r["constraint_satisfied"] else "FAIL",
            }
            for r in runs
        ]
    )

    def _pill_color(val: str):
        color = "#16a34a" if val == "PASS" else "#dc2626"
        return (
            f"background-color: {color}; color: white; border-radius: 12px;"
            " padding: 2px 10px; text-align: center"
        )

    styled = df.style.map(_pill_color, subset=["Result"])
    st.dataframe(
        styled,
        column_config={"Result": st.column_config.TextColumn(width="small")},
        width="stretch",
        hide_index=True,
    )
