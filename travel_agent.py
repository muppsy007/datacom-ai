
"""
Task 3.3 - Planning Agent with Tool Calling
This is the main agent for the task. It uses the tools defined in tools.py to reason on providing 
the user with the optimal travel plan.
"""
import json
import os

import dotenv
from openai import OpenAI
from typing import Any
from rich.console import Console

from tools import TOOL_SCHEMAS, dispatch_tool

dotenv.load_dotenv()
console = Console()

client = OpenAI(
    api_key=os.environ["OPENAI_API_KEY"],
    base_url=os.environ["OPENAI_BASE_URL"],
)

# Define the schema we expect in the final response
ITINERARY_SCHEMA: dict[str, Any] = {                                                                                                                          
    "destination": "string, e.g. Auckland",
    "origin": "string, e.g. Christchurch",                                                                                                    
    "start_date": "YYYY-MM-DD",
    "end_date": "YYYY-MM-DD",                                                                                                                 
    "duration_days": "integer",                                                                                                               
    "budget_nzd": "float",
    "actual_cost_nzd": "float",                                                                                                               
    "constraint_satisfied": "boolean",
    "flights": {                                                                                                                              
        "outbound": [
            {                                                                                                                                 
                "flight_number": "string",
                "origin": "string",                                                                                                           
                "destination": "string",
                "departure_datetime": "ISO 8601 datetime",                                                                                    
                "arrival_datetime": "ISO 8601 datetime",
                "airline": "string",                                                                                                          
                "cost_nzd": "float",
                "duration_minutes": "integer"                                                                                                 
            }   
        ],
        "return": [
            {
                "flight_number": "string",
                "origin": "string",
                "destination": "string",
                "departure_datetime": "ISO 8601 datetime",
                "arrival_datetime": "ISO 8601 datetime",
                "airline": "string",
                "cost_nzd": "float",
                "duration_minutes": "integer"
            }
        ]
    },
    "days": [
        {
            "day": "integer",
            "date": "YYYY-MM-DD",
            "activities": [                                                                                                                   
                {
                    "time": "HH:MM",                                                                                                          
                    "description": "string",
                    "cost_nzd": "float",
                    "source_tool": "string, name of tool that provided this activity"                                                         
                }                                                                                                                             
            ]                                                                                                                                 
        }                                                                                                                                     
    ],          
    "weather_summary": "string",
    "notes": "string"
}

def run_agent(prompt: str, budget_nzd: float, db_path: str) -> str:
    # system_prompt = (
    #     "You are a travel planner assistant. The user will provide a brief travel plan and you "
    #     "will use tools to plan a trip within the user's location, date and budget constraints. "
    #     "You must use <scratchpad>...</scratchpad> blocks to show reasoning before each tool call. "
    #     "You must track costs as you go and respect budget constraints. "
    #     "You must select exactly one outbound and exactly one return flight. "
    #     "You must select at least one attraction per day of the trip. "
    #     "Before producing the final JSON, you must call calculate_total "
    #     "with the cost_nzd of every selected flight and activity and the budget. "                                                                    
    #     "If constraint_satisfied is false, remove the most expensive activity "                                                                       
    #     "and call calculate_total again. Repeat until constraint_satisfied is true "                                                                  
    #     "or no activities remain. Use the returned total_nzd as actual_cost_nzd "                                                                     
    #     "and constraint_satisfied in the final JSON. "
    #     "If budget is exceeded, you must remove activities to bring budget down. "
    #     "You may repeat flight search to bring total cost under budget. "
    #     "When you have enough information to respond, you must respond with a single JSON block "
    #     "with nothing else and no prose around it. The schema for this JSON response is as follows:"
    #     "Before producing the final JSON, you must use a <scratchpad> to add up costs: "                                                              
    #     "list each selected item and its cost_nzd, sum them, compare to budget, then set "                                                            
    #     "actual_cost_nzd to that exact sum and constraint_satisfied accordingly. "
    #     + json.dumps(ITINERARY_SCHEMA, indent=2)
    # )
    system_prompt = (                                                                                                                             
        "You are a travel planning agent. Follow these steps in order:\n"                                                                     
        "1. Call search_flights for the outbound leg (origin to destination).\n"                                                              
        "2. Call search_flights for the return leg (destination to origin).\n"                                                                
        "3. Call get_weather for the destination covering the trip dates.\n"                                                                  
        "4. Call search_attractions for the destination.\n"                                                                                   
        "5. From the flight results, pick exactly one outbound and one return flight — "
        "the cheapest in each direction. Note their exact flight_number and cost_nzd. "
        "Do NOT add flights to the days array. "
        "Select ALL activities from search_attractions, sorted cheapest first, spread across all days. "
        "Every day must have at least one activity. "
        "Start with all attractions selected — only remove them in step 7 if over budget. "
        "Assign realistic times based on flight arrival times and activity durations.\n"
        "6. Call calculate_total with every selected item — the two flights and all activities — "
        "using the exact same cost_nzd values you will put in the final JSON. "
        "Each item must have a 'name' and 'cost_nzd'.\n"
        "7. If constraint_satisfied is false, remove only the activity named in remove_item from the days array. "
        "Do not change flight selections. "
        "Call calculate_total again with the updated list. "
        "If constraint_satisfied is now true, stop immediately — do not remove any more activities. "
        "Only continue removing if constraint_satisfied is still false.\n"
        "8. The flights and activities in the final JSON must use the exact cost_nzd values from approved_items "
        "in the final calculate_total response — do not use any other values. "
        "Use total_nzd as actual_cost_nzd and constraint_satisfied from the final calculate_total response.\n"
        "9. Output the JSON block exactly once and nothing else. "
        "The schema is:\n"                                                                                                                    
        + json.dumps(ITINERARY_SCHEMA, indent=2)
    )   

    # Full conversation history sent to the model on every call.
    # ReAct pattern: https://www.promptingguide.ai/techniques/react
    messages: list[Any] = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"{prompt}\n\nBudget: NZ${budget_nzd}"},
    ]

    while True:
        # Make the LLM call to work out tools to call (or a file answer)
        response = client.chat.completions.create(
            model=os.environ["MODEL_NAME"],
            messages=messages,
            tools=TOOL_SCHEMAS,
        )
        response_message = response.choices[0].message

        # If the LLM did not return a tool_call, it is the final answer
        if not response_message.tool_calls:
            return response_message.content or ""

        # Add the current tool call message to the message history
        messages.append(response_message)

        # Make the tool calls via the dispatch_tool function in tools.py
        for tool_call in response_message.tool_calls:
            console.print(f"[dim]calling {tool_call.function.name}({tool_call.function.arguments})[/dim]")
            result = dispatch_tool(tool_call.function.name, tool_call.function.arguments)
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result,
            })

if __name__ == "__main__":
      result = run_agent(                                                                                                                       
          prompt="Plan a 2-day trip to Auckland from Christchurch, departing 2025-06-01 and returning 2025-06-03, for under NZ$500",                                                                              
          budget_nzd=500.0,                                                                                                                     
          db_path="metrics.db",
      )                                                                                                                                         
      print(result)