import os
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("ANTHROPIC_API_KEY")
if not api_key:
    print("Warning: ANTHROPIC_API_KEY is not set in environment.")

client = Anthropic(api_key=api_key)
MODEL = "claude-3-haiku-20240307" # Using haiku for speed, but ops can change it

def generate_sql(question: str, schema: str) -> str:
    if not api_key or api_key == "your_api_key_here":
        # Fallback mock for testing without an API key
        if "highest" in question.lower() or "paid" in question.lower():
            return "SELECT * FROM Employee ORDER BY Salary DESC LIMIT 5;"
        elif "delete" in question.lower():
            return "DELETE FROM Employee WHERE Department = 'HR';"
        else:
            return "SELECT * FROM Employee LIMIT 10;"

    prompt = f"""You are an expert SQL assistant. Your task is to write a SQL query that answers the user's question based on the provided database schema.
The database is SQLite. Do not include markdown formatting like ```sql in your response, return ONLY the raw SQL query.
Use standard SQL. Only query the tables and columns provided in the schema.

Schema:
{schema}

User Question: {question}

Raw SQL Query:"""
    
    response = client.messages.create(
        model=MODEL,
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}]
    )
    # Just in case the model adds markdown formatting, strip it
    sql = response.content[0].text.strip()
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

    prompt = f"""You are an expert SQL assistant. Explain the following SQL query clause by clause in simple, non-technical plain English so a business user can understand it.

Schema:
{schema}

SQL Query:
{sql}

Explanation:"""
    
    response = client.messages.create(
        model=MODEL,
        max_tokens=800,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.content[0].text.strip()

def optimize_sql(sql: str, schema: str, query_plan: str) -> str:
    if not api_key or api_key == "your_api_key_here":
        return "*(Mock Optimization)*: Consider adding an index to the columns used in the WHERE or ORDER BY clauses. Ensure you are only SELECTing the columns you need."

    prompt = f"""You are an expert SQL performance tuner. Given the SQL query, database schema, and the EXPLAIN QUERY PLAN output, provide concrete suggestions for optimizing the query. Point out missing indexes, unnecessary subqueries, or suboptimal functions.

Schema:
{schema}

SQL Query:
{sql}

EXPLAIN QUERY PLAN Output:
{query_plan}

Optimization Suggestions:"""

    response = client.messages.create(
        model=MODEL,
        max_tokens=800,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.content[0].text.strip()

def correct_sql(question: str, sql: str, error: str, schema: str) -> str:
    if not api_key or api_key == "your_api_key_here":
        # Just return a very basic query to fix the failure
        return "SELECT * FROM Employee LIMIT 5;"

    prompt = f"""You are an expert SQL assistant. The user tried to answer a question with a SQL query, but it failed with an error. 
Please provide a corrected SQL query. The database is SQLite. Return ONLY the raw SQL query without markdown blocks.

Schema:
{schema}

User Question: {question}

Failed SQL Query:
{sql}

Error Message:
{error}

Corrected Raw SQL Query:"""

    response = client.messages.create(
        model=MODEL,
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}]
    )
    corrected_sql = response.content[0].text.strip()
    if corrected_sql.startswith("```sql"):
        corrected_sql = corrected_sql[6:]
    if corrected_sql.startswith("```"):
        corrected_sql = corrected_sql[3:]
    if corrected_sql.endswith("```"):
        corrected_sql = corrected_sql[:-3]
    return corrected_sql.strip()
