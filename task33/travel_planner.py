"""
Task 3.3 - Planning Agent with Tool Calling
This is the primary entry point for our travel_agent. Where we give the agent details of what we 
want as a prompt. Aside from interacting with the agent, it will log scratchpad logic for each
request in the metrics database.
"""
import json
import os
import re
from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console
from rich.prompt import Prompt

from travel_agent import run_agent
from travel_agent_logger import init_db, log_run

console = Console()
prompt = Prompt()

def calculate_cost(prompt_tokens: int, completion_tokens: int) -> float:
    """Work out the $ cost of the LLM operation after all tool calls.
    Rates are hardcoded here for observability. In a production system we would manage these in a DB
    model/cost matrix so costs adjust with model changes"""
    cost_usd = (prompt_tokens / 1000 * 0.0025) + (completion_tokens / 1000 * 0.01) 
    return cost_usd

def plan_trip(user_prompt: str) -> dict:
    """Run the travel planning agent and return structured results.

    Returns a dict with keys: itinerary, scratchpad, budget, cost
    """
    load_dotenv()

    default_db_path = str(Path(__file__).resolve().parent.parent / "metrics.db")
    db_path = os.getenv("MAIN_DB_PATH") or default_db_path

    # extract the budget from the user prompt. Default to $500 if it can't be found
    budget_match = re.search(r'(?:NZ)?\$(\d+(?:\.\d+)?)', user_prompt)
    budget = float(budget_match.group(1)) if budget_match else 500.0

    # Make the call to the agent with the prompt and budget
    agent_output = run_agent(prompt=user_prompt, budget_nzd=budget, db_path=db_path)

    itinerary = json.loads(agent_output["itinerary"])
    token_count = agent_output["prompt_tokens"] + agent_output["completion_tokens"]
    estimated_cost = calculate_cost(agent_output["prompt_tokens"], agent_output["completion_tokens"])

    # Log to database
    conn = init_db(db_path=db_path)
    log_run(
        conn=conn,
        prompt=user_prompt,
        tools=", ".join(s["tool"] for s in agent_output["steps_scratchpad"]),
        token_count=token_count,
        estimated_cost=estimated_cost,
        itinerary_actual_cost_nzd=itinerary["actual_cost_nzd"],
        constraint_satisfied=int(itinerary["constraint_satisfied"]),
        scratchpad=json.dumps(agent_output["steps_scratchpad"]),
    )

    return {
        "itinerary": itinerary,
        "scratchpad": agent_output["steps_scratchpad"],
        "budget": budget,
        "cost": estimated_cost,
    }


def main():
    # As the user what kind of trip they are looking for
    user_prompt = prompt.ask("[cyan]Hello! Tell me what trip you want to plan: ")

    result = plan_trip(user_prompt)

    # LOGGING costs and scratchpad
    console.rule("[bold cyan]Agent Scratchpad (logged in /metrics.db->agent_runs)")
    for i, step in enumerate(result["scratchpad"], 1):
        console.print(f"[bold]Step {i}[/bold] | tool: [yellow]{step['tool']}[/yellow]")
        console.print(f"  reasoning: {step['reasoning']}")
    console.rule()

    console.rule("[bold cyan]Itinerary")
    console.print_json(json.dumps(result["itinerary"]))

if __name__ == "__main__":
    main()