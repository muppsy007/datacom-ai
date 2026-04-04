"""
Task 3.3 - Planning Agent with Tool Calling
This logs record of tool use in our SQLite database. It creates a new table called agent_runs that
stores record of prompts, executed tools, token counts and est. cost.
"""
import sqlite3

def init_db(db_path: str)-> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute("""
       CREATE TABLE IF NOT EXISTS agent_runs (
            id INTEGER PRIMARY KEY,
            prompt TEXT,
            tools_used TEXT,
            tokens_used INTEGER,
            est_cost_usd FLOAT,
            constraint_satisfied INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )              
    """)
    conn.commit()
    return conn

def log_run(
    conn: sqlite3.Connection, 
    prompt: str, 
    tools: str, 
    token_count: int, 
    estimated_cost: float,
    constraint_satisfied: int
)-> None:
    conn.execute(
        """INSERT INTO agent_runs                                                                                                             
             (prompt, tools_used, tokens_used, est_cost_usd, constraint_satisfied)                                                              
             VALUES (?, ?, ?, ?, ?)""", 
        (prompt, tools, token_count, estimated_cost, constraint_satisfied)
    )
    conn.commit()