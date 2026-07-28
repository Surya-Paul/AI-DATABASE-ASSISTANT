import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from db import get_schema_info, execute_query, is_destructive
from llm import generate_sql, explain_sql, optimize_sql, correct_sql

app = FastAPI(title="AI SQL Assistant")

# ---------- Resolve the frontend directory ----------
# Works both locally (backend/../frontend) and in Docker (/app/frontend)
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
if not FRONTEND_DIR.exists():
    FRONTEND_DIR = Path("/app/frontend")  # Docker fallback

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For dev, allow all
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    question: str
    confirmed: bool = False
    sql: Optional[str] = None # If the user is retrying or confirming

@app.get("/test_query")
def test_query(q: str = "highest paid"):
    schema = get_schema_info()
    sql_to_run = generate_sql(q, schema)
    result = execute_query(sql_to_run)
    return {"sql": sql_to_run, "result": result}

class ExplainRequest(BaseModel):
    sql: str

class OptimizeRequest(BaseModel):
    sql: str

class CorrectRequest(BaseModel):
    question: str
    sql: str
    error: str

@app.post("/query")
def run_query(req: QueryRequest):
    schema = get_schema_info()
    
    # 1. Generate SQL if not provided
    sql_to_run = req.sql
    if not sql_to_run:
        try:
            sql_to_run = generate_sql(req.question, schema)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"LLM Generation failed: {str(e)}")

    # 2. Check if destructive and unconfirmed
    destructive = is_destructive(sql_to_run)
    if destructive and not req.confirmed:
        return {
            "sql": sql_to_run,
            "success": False,
            "requires_confirmation": True,
            "message": "This query appears to be destructive. Please confirm execution."
        }
        
    # 3. Execute
    result = execute_query(sql_to_run, req.confirmed)
    
    # Attach generated SQL so UI can show it
    result["sql"] = sql_to_run
    
    return result

@app.post("/explain")
def explain_query(req: ExplainRequest):
    schema = get_schema_info()
    try:
        explanation = explain_sql(req.sql, schema)
        return {"explanation": explanation}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/optimize")
def optimize_query(req: ExplainRequest): # Re-use ExplainRequest since we only need sql
    schema = get_schema_info()
    
    # Generate query plan (SQLite specific)
    try:
        plan_result = execute_query(f"EXPLAIN QUERY PLAN {req.sql}")
        if not plan_result.get("success"):
            plan_str = f"Could not generate query plan: {plan_result.get('error')}"
        else:
            plan_str = "\n".join([str(row) for row in plan_result.get("rows", [])])
    except Exception as e:
        plan_str = f"Error getting plan: {str(e)}"
        
    try:
        suggestions = optimize_sql(req.sql, schema, plan_str)
        return {"optimization": suggestions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/correct")
def correct_query(req: CorrectRequest):
    schema = get_schema_info()
    try:
        corrected = correct_sql(req.question, req.sql, req.error, schema)
        # Execute corrected query (without confirmation for now, as it's typically SELECT)
        # However, to be safe, we just return the new SQL and let the frontend send it back to /query
        return {"sql": corrected}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/schema")
def get_schema():
    return {"schema": get_schema_info()}

# ---------- Serve Frontend Static Files ----------
# Mount AFTER all API routes so /query, /explain, etc. aren't shadowed.
# The static mount serves CSS, JS, and other assets.
app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

@app.get("/{full_path:path}")
def serve_frontend(full_path: str):
    """Catch-all: serve specific files if they exist, otherwise index.html."""
    file_path = FRONTEND_DIR / full_path
    if full_path and file_path.is_file():
        return FileResponse(str(file_path))
    return FileResponse(str(FRONTEND_DIR / "index.html"))
