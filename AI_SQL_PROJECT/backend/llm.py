import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    print("Warning: GROQ_API_KEY is not set in environment.")

client = Groq(api_key=api_key) if api_key else None
MODEL = "llama-3.1-8b-instant" # Using a fast groq model

def generate_sql(question: str, schema: str) -> str:
    if not api_key or api_key == "your_api_key_here":
        # Fallback mock for testing without an API key
        if "highest" in question.lower() or "paid" in question.lower():
            return "SELECT * FROM Employee ORDER BY Salary DESC LIMIT 5;"
        elif "delete" in question.lower():
            return "DELETE FROM Employee WHERE Department = 'HR';"
        else:
            return "SELECT * FROM Employee LIMIT 10;"

    system_prompt = "You are an expert SQL assistant. The database is SQLite. Return ONLY the raw SQL query, no markdown. CRITICAL: You MUST wrap ALL table names and column names in double quotes (e.g., \"Order_ID\", \"Row_ID\"). Do NOT use brackets for quoting."
    prompt = f"""Schema:
{schema}

User Question: {question}

Raw SQL Query:"""
    
    response = client.chat.completions.create(
        model=MODEL,
        temperature=0.0,
        max_tokens=500,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
    )
    # Just in case the model adds markdown formatting, strip it
    sql = response.choices[0].message.content.strip()
    if sql.startswith("```sql"):
        sql = sql[6:]
    if sql.startswith("```"):
        sql = sql[3:]
    if sql.endswith("```"):
        sql = sql[:-3]
    return sql.strip()

def explain_sql(sql: str, schema: str) -> str:
    if not api_key or api_key == "your_api_key_here":
        return "*(Mock Explanation)*: This query selects data from the Employee table. It may filter or sort the results based on the clauses provided."

    system_prompt = "You are an expert SQL assistant. Explain SQL queries in simple, non-technical plain English."
    prompt = f"""Schema:
{schema}

SQL Query:
{sql}

Explanation:"""
    
    response = client.chat.completions.create(
        model=MODEL,
        temperature=0.2,
        max_tokens=800,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content.strip()

def optimize_sql(sql: str, schema: str, query_plan: str) -> str:
    if not api_key or api_key == "your_api_key_here":
        return "*(Mock Optimization)*: Consider adding an index to the columns used in the WHERE or ORDER BY clauses. Ensure you are only SELECTing the columns you need."

    system_prompt = "You are an expert SQL performance tuner."
    prompt = f"""Given the SQL query, database schema, and the EXPLAIN QUERY PLAN output, provide concrete suggestions for optimizing the query. Point out missing indexes, unnecessary subqueries, or suboptimal functions.

Schema:
{schema}

SQL Query:
{sql}

EXPLAIN QUERY PLAN Output:
{query_plan}

Optimization Suggestions:"""

    response = client.chat.completions.create(
        model=MODEL,
        temperature=0.2,
        max_tokens=800,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content.strip()

def correct_sql(question: str, sql: str, error: str, schema: str) -> str:
    if not api_key or api_key == "your_api_key_here":
        # Just return a very basic query to fix the failure
        return "SELECT * FROM Employee LIMIT 5;"

    system_prompt = "You are an expert SQL assistant. The database is SQLite. Return ONLY the corrected raw SQL query without markdown blocks. CRITICAL: You MUST wrap ALL table names and column names in double quotes (e.g., \"Order_ID\", \"Row_ID\"). Do NOT use brackets for quoting."
    prompt = f"""The user tried to answer a question with a SQL query, but it failed with an error. 
Please provide a corrected SQL query.

Schema:
{schema}

User Question: {question}

Failed SQL Query:
{sql}

Error Message:
{error}

Corrected Raw SQL Query:"""

    response = client.chat.completions.create(
        model=MODEL,
        temperature=0.0,
        max_tokens=500,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
    )
    corrected_sql = response.choices[0].message.content.strip()
    if corrected_sql.startswith("```sql"):
        corrected_sql = corrected_sql[6:]
    if corrected_sql.startswith("```"):
        corrected_sql = corrected_sql[3:]
    if corrected_sql.endswith("```"):
        corrected_sql = corrected_sql[:-3]
    return corrected_sql.strip()

def generate_chart_config(question: str, sql: str, columns: list, rows: list) -> dict:
    if not api_key or api_key == "your_api_key_here":
        # Mock response for when there is no API key
        if len(columns) >= 2:
            return {"type": "bar", "xAxis": columns[0], "yAxis": columns[1]}
        return {"type": "bar", "xAxis": "", "yAxis": ""}

    system_prompt = "You are a data visualization expert. Return ONLY a valid JSON object."
    sample_data = str(rows[:3]) if rows else "[]"
    prompt = f"""The user asked a question, a SQL query was executed, and data was returned.
Please suggest the best way to visualize this data using a chart. 
The JSON must have the following keys:
- "type": The type of chart ("bar", "line", or "pie")
- "xAxis": The column name to use for the X-axis (the label/category).
- "yAxis": The column name to use for the Y-axis (the numerical value).

User Question: {question}
SQL Query: {sql}
Columns: {columns}
Sample Data: {sample_data}"""

    response = client.chat.completions.create(
        model=MODEL,
        temperature=0.0,
        max_tokens=200,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
    )
    import json
    result_text = response.choices[0].message.content.strip()
    
    try:
        return json.loads(result_text.strip())
    except Exception:
        # Fallback if the LLM messes up
        if len(columns) >= 2:
            return {"type": "bar", "xAxis": columns[0], "yAxis": columns[1]}
        return {"type": "bar", "xAxis": "", "yAxis": ""}
