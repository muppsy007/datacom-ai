"""
Task 3.3 - Planning Agent with Tool Calling
This is the primary entry point for our travel_agent. Where we give the agent details of what we 
want as a prompt. Aside from interacting with the agent, it will log scratchpad logic for each
request in the metrics database.
"""
import json
import os
import re

from dotenv import load_dotenv
from rich.console import Console
from rich.prompt import Prompt

from travel_agent import run_agent
from travel_agent_logger import init_db, log_run

console = Console()
prompt = Prompt()

def main():
    load_dotenv()

    # Load the db path and connect
    db_path = os.getenv("CHAT_DB_PATH") or "metrics.db"
    conn = init_db(db_path=db_path)

    # As the user what kind of trip they are looking for
    user_prompt = prompt.ask("[cyan]Hello! Tell me what trip you want to plan: ")

    # extract the budget from the user prompt. Default to $500 if it can't be found
    budget_match = re.search(r'(?:NZ)?\$(\d+(?:\.\d+)?)', user_prompt)
    budget = float(budget_match.group(1)) if budget_match else 500.0

    # Make the call to the agent with the prompt and budget
    agent_output = run_agent(prompt=user_prompt, budget_nzd=budget, db_path=db_path)

    # LOGGING costs and scratchpad
    console.print(agent_output["steps_scratchpad"])
    
    itinerary = json.loads(agent_output["itinerary"])   
    itinerary_actual_cost_nzd = itinerary["actual_cost_nzd"]                                                                                          
    tools_used = ", ".join(s["tool"] for s in agent_output["steps_scratchpad"])                                                                   
    token_count = agent_output["prompt_tokens"] + agent_output["completion_tokens"]                                                               
    estimated_cost = calculate_cost(agent_output["prompt_tokens"], agent_output["completion_tokens"])                                             
    constraint_satisfied = int(itinerary["constraint_satisfied"])                                                                                 
    scratchpad = json.dumps(agent_output["steps_scratchpad"])

    log_run(        
        conn=conn,                                                                                                                                
        prompt=user_prompt,
        tools=tools_used,
        token_count=token_count,
        estimated_cost=estimated_cost,
        itinerary_actual_cost_nzd=itinerary_actual_cost_nzd,
        constraint_satisfied=constraint_satisfied,
        scratchpad=scratchpad,                                                                                                                    
    )


def calculate_cost(prompt_tokens: int, completion_tokens: int) -> float:
    """Work out the $ cost of the LLM operation after all tool calls.
    Rates are hardcoded here for observability. In a production system we would manage these in a DB
    model/cost matrix so costs adjust with model changes"""
    cost_usd = (prompt_tokens / 1000 * 0.0025) + (completion_tokens / 1000 * 0.01) 
    return cost_usd


if __name__ == "__main__":
    main()