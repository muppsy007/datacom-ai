import json
from unittest.mock import MagicMock, patch


def test_calculate_total_within_budget():
    from task33.travel_agent_tools import calculate_total

    result = calculate_total(
        items=[{"name": "outbound: QF535", "cost_nzd": 150.0}, {"name": "Museum", "cost_nzd": 28.0}],
        budget_nzd=500.0,
    )

    assert result["constraint_satisfied"] is True
    assert result["remove_item"] is None
    assert result["total_nzd"] == 178.0


def test_calculate_total_removes_cheapest_covering_activity():
    from task33.travel_agent_tools import calculate_total

    # Total: 150 + 150 + 28 + 35 + 85 + 120 = 568, overage = 68
    # Waiheke ($85) is cheapest activity that covers $68 overage
    result = calculate_total(
        items=[
            {"name": "outbound: QF535", "cost_nzd": 150.0},
            {"name": "return: NZ301", "cost_nzd": 150.0},
            {"name": "Auckland War Memorial Museum", "cost_nzd": 28.0},
            {"name": "Sky Tower observation deck", "cost_nzd": 35.0},
            {"name": "Waiheke Island day trip", "cost_nzd": 85.0},
            {"name": "Harbour sailing tour", "cost_nzd": 120.0},
        ],
        budget_nzd=500.0,
    )

    assert result["constraint_satisfied"] is False
    assert result["remove_item"] == "Waiheke Island day trip"


def test_calculate_total_removes_most_expensive_when_no_single_item_covers_overage():
    from task33.travel_agent_tools import calculate_total

    # Total: 150 + 150 + 28 + 35 = 363, overage = 163
    # No single activity covers $163, so most expensive (Sky Tower $35) is NOT it —
    # most expensive activity is Sky Tower $35, still less than overage.
    # Falls back to max: Sky Tower $35
    result = calculate_total(
        items=[
            {"name": "outbound: QF535", "cost_nzd": 150.0},
            {"name": "return: NZ301", "cost_nzd": 150.0},
            {"name": "Auckland War Memorial Museum", "cost_nzd": 28.0},
            {"name": "Sky Tower observation deck", "cost_nzd": 35.0},
        ],
        budget_nzd=200.0,
    )

    assert result["constraint_satisfied"] is False
    assert result["remove_item"] == "Sky Tower observation deck"


def test_calculate_total_never_removes_flights():
    from task33.travel_agent_tools import calculate_total

    # Only flights, both over budget — no activities to remove
    result = calculate_total(
        items=[
            {"name": "outbound: QF535", "cost_nzd": 300.0},
            {"name": "return: NZ301", "cost_nzd": 300.0},
        ],
        budget_nzd=500.0,
    )

    assert result["constraint_satisfied"] is False
    assert result["remove_item"] is None


def test_dispatch_tool_strips_reasoning():
    from task33.travel_agent_tools import dispatch_tool

    result = dispatch_tool(
        "search_attractions",
        json.dumps({"location": "Auckland", "reasoning": "Finding things to do"}),
    )

    data = json.loads(result)
    assert "attractions" in data
    assert len(data["attractions"]) > 0


def test_dispatch_tool_search_flights_strips_reasoning():
    from task33.travel_agent_tools import dispatch_tool

    result = dispatch_tool(
        "search_flights",
        json.dumps({"origin": "CHC", "destination": "AKL", "date": "2025-06-01", "reasoning": "Need outbound flight"}),
    )

    data = json.loads(result)
    assert "flights" in data
    assert all(f["origin"] == "CHC" for f in data["flights"])


def test_run_agent_returns_steps_scratchpad_and_itinerary():
    from task33.travel_agent import run_agent

    # Build a minimal fake tool call then a final answer
    tool_call = MagicMock()
    tool_call.id = "call_1"
    tool_call.function.name = "search_attractions"
    tool_call.function.arguments = json.dumps({"location": "Auckland", "reasoning": "Find things to do"})

    tool_response = MagicMock()
    tool_response.tool_calls = [tool_call]
    tool_response.content = None

    final_itinerary = {
        "destination": "Auckland", "origin": "Christchurch",
        "start_date": "2025-06-01", "end_date": "2025-06-02",
        "duration_days": 1, "budget_nzd": 500.0, "actual_cost_nzd": 28.0,
        "constraint_satisfied": True,
        "flights": {"outbound": [], "return": []},
        "days": [{"day": 1, "date": "2025-06-01", "activities": []}],
        "weather_summary": "", "notes": "",
    }

    final_response = MagicMock()
    final_response.tool_calls = None
    final_response.content = json.dumps(final_itinerary)

    usage = MagicMock()
    usage.prompt_tokens = 100
    usage.completion_tokens = 50

    turn1 = MagicMock()
    turn1.choices = [MagicMock(message=tool_response)]
    turn1.usage = usage

    turn2 = MagicMock()
    turn2.choices = [MagicMock(message=final_response)]
    turn2.usage = usage

    with patch("task33.travel_agent.client") as mock_client:
        mock_client.chat.completions.create.side_effect = [turn1, turn2]
        result = run_agent(prompt="Plan a trip", budget_nzd=500.0, db_path="test.db")

    assert "itinerary" in result
    assert "steps_scratchpad" in result
    assert result["steps_scratchpad"][0]["tool"] == "search_attractions"
    assert result["steps_scratchpad"][0]["reasoning"] == "Find things to do"
    assert json.loads(result["itinerary"])["destination"] == "Auckland"
