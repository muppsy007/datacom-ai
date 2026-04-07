import sqlite3
from pathlib import Path

import plotly.express as px
import streamlit as st

METRICS_DB = Path(__file__).resolve().parent.parent.parent / "metrics.db"


def _get_assistant_turns() -> list[dict]:
    """Read assistant messages with usage data from the DB. Never writes."""
    if not METRICS_DB.exists():
        return []
    conn = sqlite3.connect(str(METRICS_DB))
    conn.row_factory = sqlite3.Row

    table = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='messages'"
    ).fetchone()
    if not table:
        conn.close()
        return []

    rows = conn.execute(
        "SELECT cost_usd, latency_ms FROM messages "
        "WHERE role = 'assistant' AND cost_usd IS NOT NULL "
        "ORDER BY id"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def render_chat_tab():
    turns = _get_assistant_turns()

    if not turns:
        st.info("No chat data yet. Click below to start a conversation.")
        if st.button("Go to Chat"):
            st.switch_page("pages/1_Chat.py")
        return

    total_turns = len(turns)
    total_cost = sum(t["cost_usd"] for t in turns)
    avg_latency = sum(t["latency_ms"] for t in turns) / total_turns
    avg_cost = total_cost / total_turns

    # --- Metric cards ---
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Turns", total_turns)
    with col2:
        st.metric("Total Cost", f"${total_cost:.4f}")
    with col3:
        st.metric("Avg Latency", f"{avg_latency:.0f}ms")
    with col4:
        st.metric("Avg Cost/Turn", f"${avg_cost:.6f}")

    # --- Cost per turn chart ---
    cost_data = [{"Turn": i, "Cost (USD)": t["cost_usd"]} for i, t in enumerate(turns, 1)]
    fig_cost = px.area(
        cost_data,
        x="Turn",
        y="Cost (USD)",
        title="Cost per turn (USD)",
        color_discrete_sequence=["#378ADD"],
    )
    fig_cost.update_traces(fillcolor="rgba(55, 138, 221, 0.2)", line_color="#378ADD")
    fig_cost.update_layout(
        showlegend=False,
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor="rgba(0,0,0,0.05)"),
    )
    st.plotly_chart(fig_cost, width="stretch")

    # --- Latency per turn chart ---
    latency_data = [{"Turn": i, "Latency (ms)": t["latency_ms"]} for i, t in enumerate(turns, 1)]
    fig_latency = px.area(
        latency_data,
        x="Turn",
        y="Latency (ms)",
        title="Latency per turn (ms)",
        color_discrete_sequence=["#1D9E75"],
    )
    fig_latency.update_traces(fillcolor="rgba(29, 158, 117, 0.2)", line_color="#1D9E75")
    fig_latency.update_layout(
        showlegend=False,
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor="rgba(0,0,0,0.05)"),
    )
    st.plotly_chart(fig_latency, width="stretch")
