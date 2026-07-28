"""
Vercel Serverless Entry Point
=============================
This file is the single serverless function that Vercel calls for all API routes.
It creates a FastAPI app with all endpoints and auto-seeds a SQLite database
in /tmp on each cold start (Vercel's filesystem is read-only except /tmp).
"""

import os
import re
import sqlite3

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

from groq import Groq
from dotenv import load_dotenv
from sqlalchemy import create_engine, MetaData, text
from sqlalchemy.exc import SQLAlchemyError

# ──────────────────────────────────────────────
# 1. Configuration
# ──────────────────────────────────────────────
load_dotenv()

# Vercel writable directory
DB_PATH = "/tmp/data.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)
db_metadata = MetaData()

# LLM
api_key = os.getenv("GROQ_API_KEY")
client = Groq(api_key=api_key) if api_key else None
MODEL = "llama-3.1-8b-instant"


# ──────────────────────────────────────────────
# 2. Auto-Seed Database on Cold Start
# ──────────────────────────────────────────────
def _seed_if_needed():
    """Create and seed the Employee table if it doesn't exist yet."""
    if os.path.exists(DB_PATH):
        # Quick check: does Employee table already exist?
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='Employee'")
        if cur.fetchone():
            conn.close()
            return  # Already seeded
        conn.close()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Employee (
        EmployeeID INTEGER PRIMARY KEY AUTOINCREMENT,
        Name TEXT NOT NULL,
        Department TEXT NOT NULL,
        Salary INTEGER NOT NULL,
        HireDate DATE NOT NULL
    )
    """)

    employees = [
        ("Alice Smith", "Engineering", 120000, "2020-01-15"),
        ("Bob Johnson", "Engineering", 115000, "2021-03-22"),
        ("Charlie Brown", "Sales", 85000, "2019-11-01"),
        ("Diana Prince", "Management", 150000, "2018-05-10"),
        ("Evan Wright", "Marketing", 90000, "2022-08-14"),
        ("Fiona Gallagher", "Sales", 95000, "2020-07-19"),
        ("George Costanza", "Sales", 75000, "2023-01-05"),
        ("Hannah Abbott", "Engineering", 110000, "2021-09-09"),
        ("Ian Malcolm", "Research", 140000, "2017-02-14"),
        ("Julia Child", "Marketing", 92000, "2020-11-20"),
        ("Kevin Scott", "Engineering", 105000, "2022-04-11"),
        ("Laura Palmer", "HR", 80000, "2019-06-30"),
        ("Michael Scott", "Management", 130000, "2015-03-15"),
        ("Nina Dobrev", "Engineering", 125000, "2018-09-17"),
        ("Oscar Martinez", "Finance", 115000, "2016-08-08"),
        ("Pam Beesly", "Sales", 82000, "2019-02-14"),
        ("Quinn Fabray", "Marketing", 88000, "2021-12-01"),
        ("Rachel Green", "Sales", 89000, "2020-10-10"),
        ("Steve Rogers", "Management", 145000, "2017-07-04"),
        ("Tony Stark", "Engineering", 160000, "2015-05-02"),
    ]

    cursor.executemany(
        "INSERT INTO Employee (Name, Department, Salary, HireDate) VALUES (?, ?, ?, ?)",
        employees,
    )

    conn.commit()
    conn.close()
    print("Database seeded in /tmp.")


# Seed on module import (cold start)
_seed_if_needed()


# ──────────────────────────────────────────────
# 3. DB Helper Functions
# ──────────────────────────────────────────────
def get_schema_info() -> str:
    try:
        db_metadata.clear()
        db_metadata.reflect(bind=engine)
        schema_text = ""
        for table_name, table in db_metadata.tables.items():
            schema_text += f"Table: {table_name}\nColumns:\n"
            for column in table.columns:
                schema_text += f" - {column.name} ({column.type})\n"
            schema_text += "\n"
        return schema_text.strip()
    except Exception as e:
        return f"No schema available: {e}"


def is_destructive(sql: str) -> bool:
    sql_upper = sql.upper()
    destructive_keywords = ["INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE", "REPLACE"]
    for keyword in destructive_keywords:
        if re.search(rf'\b{keyword}\b', sql_upper):
            return True
    return False


def execute_query(sql: str, confirmed: bool = False) -> dict:
    destructive = is_destructive(sql)
    if destructive and not confirmed:
        return {
            "success": False,
            "requires_confirmation": True,
            "error": "This query appears to be destructive. Please confirm execution.",
        }
    try:
        with engine.connect() as conn:
            if sql.upper().strip().startswith("SELECT") and "LIMIT" not in sql.upper():
                sql = f"SELECT * FROM ({sql}) LIMIT 100"
            result = conn.execute(text(sql))
            if destructive:
                conn.commit()
                return {
                    "success": True,
                    "requires_confirmation": False,
                    "rows": [],
                    "columns": [],
                    "message": f"Query executed successfully. {result.rowcount} row(s) affected.",
                }
            if result.returns_rows:
                columns = list(result.keys())
                rows = [dict(zip(columns, row)) for row in result.fetchall()]
                return {"success": True, "requires_confirmation": False, "rows": rows, "columns": columns}
            return {"success": True, "requires_confirmation": False, "rows": [], "columns": [], "message": "Query executed successfully."}
    except (SQLAlchemyError, Exception) as e:
        return {"success": False, "requires_confirmation": False, "error": str(e)}


# ──────────────────────────────────────────────
# 4. LLM Helper Functions (with Mock Fallback)
# ──────────────────────────────────────────────
def generate_sql(question: str, schema: str) -> str:
    if not api_key or api_key == "your_api_key_here":
        q = question.lower()
        if "highest" in q or "paid" in q or "salary" in q:
            return "SELECT * FROM Employee ORDER BY Salary DESC LIMIT 5;"
        elif "delete" in q or "drop" in q:
            return "DELETE FROM Employee WHERE Department = 'HR';"
        elif "department" in q:
            return "SELECT Department, COUNT(*) as count, AVG(Salary) as avg_salary FROM Employee GROUP BY Department;"
        elif "engineer" in q:
            return "SELECT * FROM Employee WHERE Department = 'Engineering' ORDER BY Salary DESC;"
        elif "hired" in q or "recent" in q or "new" in q:
            return "SELECT * FROM Employee ORDER BY HireDate DESC LIMIT 5;"
        elif "count" in q or "how many" in q:
            return "SELECT COUNT(*) as total_employees FROM Employee;"
        elif "average" in q or "avg" in q or "mean" in q:
            return "SELECT AVG(Salary) as average_salary FROM Employee;"
        else:
            return "SELECT * FROM Employee LIMIT 10;"
    prompt = f"""You are an expert SQL assistant. Write a SQL query for the user's question.
The database is SQLite. Return ONLY the raw SQL query, no markdown.

Schema:
{schema}

User Question: {question}

Raw SQL Query:"""
    response = client.chat.completions.create(model=MODEL, max_tokens=500, messages=[{"role": "user", "content": prompt}])
    sql = response.choices[0].message.content.strip()
    for prefix in ["```sql", "```"]:
        if sql.startswith(prefix):
            sql = sql[len(prefix):]
    if sql.endswith("```"):
        sql = sql[:-3]
    return sql.strip()


def explain_sql(sql: str, schema: str) -> str:
    if not api_key or api_key == "your_api_key_here":
        return "*(Mock Explanation)*: This query selects data from the Employee table. It may filter or sort the results based on the clauses provided."
    prompt = f"""Explain the following SQL query clause by clause in simple plain English.
Schema:
{schema}

SQL Query:
{sql}

Explanation:"""
    response = client.chat.completions.create(model=MODEL, max_tokens=800, messages=[{"role": "user", "content": prompt}])
    return response.choices[0].message.content.strip()


def optimize_sql(sql: str, schema: str, query_plan: str) -> str:
    if not api_key or api_key == "your_api_key_here":
        return "*(Mock Optimization)*: Consider adding an index to columns used in WHERE or ORDER BY. Only SELECT the columns you need."
    prompt = f"""Suggest optimizations for this SQL query.
Schema: {schema}
SQL: {sql}
Query Plan: {query_plan}

Suggestions:"""
    response = client.chat.completions.create(model=MODEL, max_tokens=800, messages=[{"role": "user", "content": prompt}])
    return response.choices[0].message.content.strip()


def correct_sql(question: str, sql: str, error: str, schema: str) -> str:
    if not api_key or api_key == "your_api_key_here":
        return "SELECT * FROM Employee LIMIT 5;"
    prompt = f"""Fix this SQL query. Return ONLY the corrected raw SQL.
Schema: {schema}
Question: {question}
Failed SQL: {sql}
Error: {error}

Corrected SQL:"""
    response = client.chat.completions.create(model=MODEL, max_tokens=500, messages=[{"role": "user", "content": prompt}])
    corrected = response.choices[0].message.content.strip()
    for prefix in ["```sql", "```"]:
        if corrected.startswith(prefix):
            corrected = corrected[len(prefix):]
    if corrected.endswith("```"):
        corrected = corrected[:-3]
    return corrected.strip()


# ──────────────────────────────────────────────
# 5. FastAPI App & Endpoints
# ──────────────────────────────────────────────
app = FastAPI(title="AI SQL Assistant")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class QueryRequest(BaseModel):
    question: str
    confirmed: bool = False
    sql: Optional[str] = None


class ExplainRequest(BaseModel):
    sql: str


class CorrectRequest(BaseModel):
    question: str
    sql: str
    error: str


@app.get("/")
def health():
    return {"status": "ok", "message": "AI SQL Assistant API is running on Vercel!"}


@app.post("/query")
def run_query(req: QueryRequest):
    schema = get_schema_info()
    sql_to_run = req.sql
    if not sql_to_run:
        try:
            sql_to_run = generate_sql(req.question, schema)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"LLM Generation failed: {e}")
    destructive = is_destructive(sql_to_run)
    if destructive and not req.confirmed:
        return {"sql": sql_to_run, "success": False, "requires_confirmation": True, "message": "⚠️ This query is destructive. Please confirm."}
    result = execute_query(sql_to_run, req.confirmed)
    result["sql"] = sql_to_run
    return result


@app.post("/explain")
def explain(req: ExplainRequest):
    schema = get_schema_info()
    try:
        return {"explanation": explain_sql(req.sql, schema)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/optimize")
def optimize(req: ExplainRequest):
    schema = get_schema_info()
    try:
        plan_result = execute_query(f"EXPLAIN QUERY PLAN {req.sql}")
        plan_str = "\n".join([str(r) for r in plan_result.get("rows", [])]) if plan_result.get("success") else "N/A"
    except Exception:
        plan_str = "N/A"
    try:
        return {"optimization": optimize_sql(req.sql, schema, plan_str)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/correct")
def correct(req: CorrectRequest):
    schema = get_schema_info()
    try:
        return {"sql": correct_sql(req.question, req.sql, req.error, schema)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/schema")
def get_schema():
    return {"schema": get_schema_info()}


@app.get("/test_query")
def test_query(q: str = "highest paid"):
    schema = get_schema_info()
    sql_to_run = generate_sql(q, schema)
    result = execute_query(sql_to_run)
    return {"sql": sql_to_run, "result": result}
