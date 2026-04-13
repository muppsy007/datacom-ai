"""
Task 3.3 - Planning Agent with Tool Calling
This defines our tools (all mocks to avoid setting up external APIs) that our agent should decide
to use and process during it's planning.
"""
import hashlib
import json
import random

from openai.types.chat import ChatCompletionToolParam
from typing import Any

# Mock inbound and outbound flights API
def search_flights(origin: str, destination: str, date: str) -> dict[str, Any]:
    # Deterministic seed using md5 so prices are stable across restarts
    # (Python's hash() is randomized per process via PYTHONHASHSEED)
    seed = int(hashlib.md5((origin + destination + date).encode()).hexdigest(), 16)
    random.seed(seed)
    
    carriers = [                                                                                                                              
          ("NZ301", "Air New Zealand", "07:00", "08:05", 65),                                                                                   
          ("JQ201", "Jetstar",         "13:00", "14:15", 75),                                                                                   
          ("NZ305", "Air New Zealand", "09:30", "10:35", 65),
          ("FJ101", "Fiji Airways",    "11:00", "12:20", 80),                                                                                   
          ("QF535", "Qantas",          "15:45", "16:50", 65),                                                                                   
      ]                                                                                                                                         
    flights: list[dict[str, Any]] = [                                                                                                         
        {                                                                                                                                     
            "flight_number": fn,
            "origin": origin,
            "destination": destination,
            "departure_datetime": f"{date}T{dep}:00",                                                                                         
            "arrival_datetime": f"{date}T{arr}:00",
            "airline": airline,                                                                                                               
            "cost_nzd": round(random.uniform(149.0, 399.0), 2), # Random price                                                                           
            "duration_minutes": dur,
        }                                                                                                                                     
        for fn, airline, dep, arr, dur in carriers
    ]                                                                                                                                         
    return {"flights": flights}

# Mock Weather API modelled on Open-Meteo (open-meteo.com) response shape
def get_weather(location: str, start_date: str, end_date: str) -> dict[str, Any]:
    daily: list[dict[str, Any]] = [
        {
            "location": location,
            "date": start_date,
            "temperature_max_celsius": 19.2,
            "temperature_min_celsius": 13.1,
            "weather_code": 2,
            "condition": "Partly cloudy",
            "wind_speed_max_kph": 20.0,
            "summary": "Mild and partly cloudy. Good conditions for sightseeing.",
        },
        {
            "location": location,
            "date": end_date,
            "temperature_max_celsius": 21.5,
            "temperature_min_celsius": 14.8,
            "weather_code": 1,
            "condition": "Mainly clear",
            "wind_speed_max_kph": 12.5,
            "summary": "Mainly clear and warm. Excellent day for outdoor activities.",
        },
    ]
    return {
        "location": location,
        "daily": daily,
    }

# Mock the attractions in a given location
def search_attractions(location: str) -> dict[str, Any]:
    attractions: list[dict[str, Any]] = [                                                                                                     
        {                                                                                                                                     
            "name": "Auckland War Memorial Museum",                                                                                           
            "description": "World-class museum covering NZ history and natural history.",                                                     
            "cost_nzd": 28.0,                                                                                                                 
            "duration_hours": 2.5,                                                                                                            
        },                                                                                                                                    
        {                                                                                                                                     
            "name": "Sky Tower observation deck",
            "description": "360-degree views from 186m above the CBD.",                                                                       
            "cost_nzd": 35.0,
            "duration_hours": 1.0,                                                                                                            
        },      
        {                                                                                                                                     
            "name": "Waiheke Island day trip",
            "description": "Ferry to Waiheke, wineries and beaches.",
            "cost_nzd": 85.0,                                                                                                                 
            "duration_hours": 8.0,
        },                                                                                                                                    
        {       
            "name": "Harbour sailing tour",                                                                                                   
            "description": "Two-hour sailing on the Waitemata Harbour.",
            "cost_nzd": 120.0,                                                                                                                
            "duration_hours": 2.0,
        },                                                                                                                                    
    ]           
    return {"location": location, "attractions": attractions}

TOOL_SCHEMAS: list[ChatCompletionToolParam] = [
    {                                                                                                                                         
        "type": "function",
        "function": {                                                                                                                         
            "name": "search_flights",
            "description": "Search for available flights between two cities on a given date.",                                                
            "parameters": {                                                                                                                   
                "type": "object",
                "properties": {                                                                                                               
                    "origin":      {"type": "string", "description": "IATA airport code, e.g. CHC"},
                    "destination": {"type": "string", "description": "IATA airport code, e.g. AKL"},                                          
                    "date":        {"type": "string", "description": "Date in YYYY-MM-DD format"},
                    "reasoning":   {"type": "string"},
                },                                                                                                                            
                "required": ["origin", "destination", "date", "reasoning"],
            },                                                                                                                                
        },      
    },
    {                                                                                                                                         
        "type": "function",
        "function": {                                                                                                                         
            "name": "get_weather",
            "description": "Get weather forecast in one location for each day between two dates",                                                
            "parameters": {                                                                                                                   
                "type": "object",
                "properties": {                                                                                                               
                    "location":   {
                        "type": "string", 
                        "description": "Town or City name, e.g. Auckland"
                    },
                    "start_date": {
                        "type": "string", 
                        "description": "Start date for forecast in YYYY-MM-DD format"
                    },                                          
                    "end_date":   {
                        "type": "string", 
                        "description": "End date for forecast in YYYY-MM-DD format"
                    },
                    "reasoning":   {"type": "string"},
                },                                                                                                                            
                "required": ["location", "start_date", "end_date", "reasoning"],
            },                                                                                                                                
        },      
    },  
    {                                                                                                                                         
        "type": "function",
        "function": {                                                                                                                         
            "name": "search_attractions",
            "description": "Find toruist attractions in a given location with costs and durations",                                                
            "parameters": {                                                                                                                   
                "type": "object",
                "properties": {                                                                                                               
                    "location":   {
                        "type": "string", 
                        "description": "Town or City name, e.g. Auckland",
                    },
                    "reasoning":   {"type": "string"},
                },                                                                                                                            
                "required": ["location", "reasoning"],
            },                                                                                                                                
        },      
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_total",
            "description": "Sum costs of selected items and check against budget. Returns the item to remove if over budget.",
            "parameters": {
                "type": "object",
                "properties": {
                    "items": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "cost_nzd": {"type": "number"},
                            },
                            "required": ["name", "cost_nzd"],
                        },
                        "description": "List of selected flights and activities with their names and costs",
                    },
                    "budget_nzd": {
                        "type": "number",
                        "description": "The budget in NZD to check against",
                    },
                    "reasoning":   {"type": "string"},
                },
                "required": ["items", "budget_nzd", "reasoning"],
            },
        },
    },
]

def calculate_total(items: list[dict[str, Any]], budget_nzd: float) -> dict[str, Any]:
    """Sum costs of named items and identify what to remove if over budget."""
    total = round(sum(item["cost_nzd"] for item in items), 2)
    over_budget = total > budget_nzd
    to_remove = None
    if over_budget:
        overage = total - budget_nzd
        activities = [i for i in items if not i["name"].startswith(("outbound:", "return:"))]
        # Find cheapest activity that covers the overage, or the most expensive if none covers it
        covering = [i for i in activities if i["cost_nzd"] >= overage]
        if covering:
            to_remove = min(covering, key=lambda x: x["cost_nzd"])
        elif activities:
            to_remove = max(activities, key=lambda x: x["cost_nzd"])
    return {
        "total_nzd": total,
        "budget_nzd": budget_nzd,
        "constraint_satisfied": not over_budget,
        "remaining_nzd": round(budget_nzd - total, 2),
        "remove_item": to_remove["name"] if to_remove else None,
        "approved_items": items,
    }


TOOLS: dict[str, Any] = {
    "search_flights": search_flights,
    "get_weather": get_weather,
    "search_attractions": search_attractions,
    "calculate_total": calculate_total,
}

def dispatch_tool(name:str, arguments_json: str)-> str:
    # Important, make sure the tool call is a valid one. Low risk but user could force LLM to call arbitary funciton names like delete_all()
    if name not in TOOLS:
        raise ValueError(f"Unknown tool requested: {name}")
    args = json.loads(arguments_json)
    args.pop("reasoning", None) 
    return json.dumps(TOOLS[name](**args))
