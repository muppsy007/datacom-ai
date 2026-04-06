"""
Tests for task33 travel_agent_tools - covers search_flights, get_weather, search_attractions, 
and calculate_cost from travel_planner.
calculate_total is already covered in test_task33_agent.py.
"""
import pytest

def test_search_flights_returns_five_flights():
    from task33.travel_agent_tools import search_flights

    result = search_flights("CHC", "AKL", "2025-06-01")
    assert len(result["flights"]) == 5


def test_search_flights_sets_correct_origin_and_destination():
    from task33.travel_agent_tools import search_flights

    result = search_flights("CHC", "AKL", "2025-06-01")
    for flight in result["flights"]:
        assert flight["origin"] == "CHC"
        assert flight["destination"] == "AKL"


def test_search_flights_includes_required_fields():
    from task33.travel_agent_tools import search_flights

    result = search_flights("CHC", "AKL", "2025-06-01")
    required = {
        "flight_number", 
        "origin", 
        "destination", 
        "departure_datetime", 
        "arrival_datetime", 
        "airline", 
        "cost_nzd", 
        "duration_minutes"
    }
    for flight in result["flights"]:
        assert required.issubset(flight.keys())


def test_search_flights_is_deterministic():
    from task33.travel_agent_tools import search_flights

    # Flight output for one direction should always be the same between calls
    r1 = search_flights("CHC", "AKL", "2025-06-01")
    r2 = search_flights("CHC", "AKL", "2025-06-01")
    assert r1 == r2


def test_search_flights_differs_by_route():
    from task33.travel_agent_tools import search_flights

    # Flight output for different directions should never be the same between calls
    outbound = search_flights("CHC", "AKL", "2025-06-01")
    returning = search_flights("AKL", "CHC", "2025-06-03")
    assert outbound["flights"][0]["cost_nzd"] != returning["flights"][0]["cost_nzd"]


def test_get_weather_returns_correct_location():
    from task33.travel_agent_tools import get_weather

    result = get_weather("Auckland", "2025-06-01", "2025-06-02")
    assert result["location"] == "Auckland"


def test_get_weather_returns_two_daily_entries():
    from task33.travel_agent_tools import get_weather

    result = get_weather("Auckland", "2025-06-01", "2025-06-02")
    assert len(result["daily"]) == 2


def test_get_weather_daily_entries_have_required_fields():
    from task33.travel_agent_tools import get_weather

    result = get_weather("Auckland", "2025-06-01", "2025-06-02")
    required = {
        "location", 
        "date", 
        "temperature_max_celsius", 
        "temperature_min_celsius", 
        "condition", 
        "summary"
    }
    for day in result["daily"]:
        assert required.issubset(day.keys())


def test_get_weather_dates_match_start_and_end():
    from task33.travel_agent_tools import get_weather

    result = get_weather("Auckland", "2025-06-01", "2025-06-02")
    assert result["daily"][0]["date"] == "2025-06-01"
    assert result["daily"][1]["date"] == "2025-06-02"


def test_search_attractions_returns_attractions_list():
    from task33.travel_agent_tools import search_attractions

    # searching for attractions in Auckland should result in at least one entry
    result = search_attractions("Auckland")
    assert "attractions" in result
    assert len(result["attractions"]) > 0


def test_search_attractions_returns_correct_location():
    from task33.travel_agent_tools import search_attractions

    result = search_attractions("Auckland")
    assert result["location"] == "Auckland"


def test_search_attractions_have_required_fields():
    from task33.travel_agent_tools import search_attractions

    result = search_attractions("Auckland")
    required = {
        "name", 
        "description", 
        "cost_nzd", 
        "duration_hours"
    }
    for attraction in result["attractions"]:
        assert required.issubset(attraction.keys())


def test_calculate_cost_returns_correct_value():
    from task33.travel_planner import calculate_cost

    # 100 prompt tokens at $0.0025/1000 = $0.00025, 50 completion tokens at $0.01/1000 = $0.0005
    cost = calculate_cost(prompt_tokens=100, completion_tokens=50)
    assert cost == pytest.approx(0.00075) # avoid flaky calcs with approx


def test_calculate_cost_zero_tokens():
    from task33.travel_planner import calculate_cost

    assert calculate_cost(0, 0) == 0.0
