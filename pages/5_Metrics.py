import json
import sqlite3
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

st.title("Metrics")
st.caption("Evaluation dashboard — metrics across all tasks")

METRICS_DB = Path(__file__).resolve().parent.parent / "metrics.db"


def _get_eval_runs() -> list[dict]:
    """Read the most recent evaluated retrieval run per question. Never writes."""
    if not METRICS_DB.exists():
        return []
    conn = sqlite3.connect(str(METRICS_DB))
    conn.row_factory = sqlite3.Row

    table = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='retrieval_runs'"
    ).fetchone()
    if not table:
        conn.close()
        return []

    rows = conn.execute(
        """
        SELECT r.query, r.latency_ms, r.passed, r.returned_sources
        FROM retrieval_runs r
        INNER JOIN (
            SELECT query, MAX(id) AS max_id
            FROM retrieval_runs
            WHERE passed IS NOT NULL
            GROUP BY query
        ) latest ON r.id = latest.max_id
        ORDER BY r.id
        """
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


tab_chat, tab_retrieval, tab_agents = st.tabs(
    ["Chat Telemetry", "Retrieval Performance", "Agent Runs"]
)

with tab_chat:
    st.info("No data available")

with tab_retrieval:
    eval_rows = _get_eval_runs()

    if not eval_rows:
        st.info("No evaluation data yet")
        if st.button("Run Evaluation"):
            with st.status("Running evaluation...", expanded=True) as status:
                st.write("Retrieving answers for each question...")
                from task32.evaluate import evaluate

                evaluate()
                status.update(label="Evaluation complete!", state="complete")
            st.rerun()
    else:
        total_questions = len(eval_rows)
        total_passed = sum(r["passed"] for r in eval_rows)
        recall = total_passed / total_questions
        latencies = [r["latency_ms"] for r in eval_rows]
        median_ms = sorted(latencies)[len(latencies) // 2] if latencies else 0

        # --- Metric cards ---
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Recall@5", f"{recall:.1%}", f"{total_passed}/{total_questions} passed")
        with col2:
            subtitle = "Under 300ms target" if median_ms < 300 else "Over 300ms target"
            st.metric("Median Retrieval", f"{median_ms:.0f}ms", subtitle)
        with col3:
            st.metric("Questions Evaluated", total_questions)

        # --- Latency bar chart ---
        chart_data = []
        for i, row in enumerate(eval_rows, 1):
            ms = row["latency_ms"]
            chart_data.append(
                {"Question": f"Q{i}", "Latency (ms)": ms, "Over target": ms > 300}
            )

        fig = px.bar(
            chart_data,
            x="Question",
            y="Latency (ms)",
            color="Over target",
            color_discrete_map={False: "#636EFA", True: "#EF553B"},
            title="Retrieval Latency per Query",
        )
        fig.add_hline(
            y=300, line_dash="dash", line_color="red", annotation_text="300ms target"
        )
        fig.update_layout(showlegend=False, xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)

        # --- Results table ---
        st.subheader("Results")
        df = pd.DataFrame(
            [
                {
                    "Question": row["query"],
                    "Result": "PASS" if row["passed"] else "FAIL",
                    "Top Sources": ", ".join(json.loads(row["returned_sources"])),
                }
                for row in eval_rows
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
            use_container_width=True,
            hide_index=True,
        )

with tab_agents:
    st.info("No data available")
