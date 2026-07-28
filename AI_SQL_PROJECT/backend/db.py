import os
import re
from sqlalchemy import create_engine, MetaData, text
from sqlalchemy.exc import SQLAlchemyError

# Using SQLite for local dev. Can easily swap to postgresql://user:pass@host/db
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data.db")

engine = create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)
metadata = MetaData()

def get_schema_info() -> str:
    """Extracts table names and column details to provide as context to the LLM."""
    try:
        metadata.reflect(bind=engine)
        schema_text = ""
        for table_name, table in metadata.tables.items():
            schema_text += f"Table: {table_name}\nColumns:\n"
            for column in table.columns:
                schema_text += f" - {column.name} ({column.type})\n"
            schema_text += "\n"
        return schema_text.strip()
    except Exception as e:
        print(f"Error getting schema info: {e}")
        return "No schema available."

def is_destructive(sql: str) -> bool:
    """Simple check to see if the query might be destructive."""
    sql_upper = sql.upper()
    destructive_keywords = ["INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE", "REPLACE"]
    # Check if any destructive keyword is in the query as a standalone word
    for keyword in destructive_keywords:
        if re.search(rf'\b{keyword}\b', sql_upper):
            return True
    return False

def execute_query(sql: str, confirmed: bool = False) -> dict:
    """Executes a SQL query against the database."""
    destructive = is_destructive(sql)
    
    if destructive and not confirmed:
        return {
            "success": False,
            "requires_confirmation": True,
            "error": "This query appears to be destructive. Please confirm execution."
        }
        
    try:
        with engine.connect() as conn:
            # We enforce a limit for safety if it's a select statement
            if sql.upper().strip().startswith("SELECT") and "LIMIT" not in sql.upper():
                sql = f"SELECT * FROM ({sql}) LIMIT 100"
                
            result = conn.execute(text(sql))
            
            # If it's a DML statement, we need to commit
            if destructive:
                conn.commit()
                return {
                    "success": True,
                    "requires_confirmation": False,
                    "rows": [],
                    "columns": [],
                    "message": f"Query executed successfully. {result.rowcount} row(s) affected."
                }
                
            if result.returns_rows:
                columns = list(result.keys())
                # fetchall returns Row objects which can be converted to dicts (using _mapping in newer SQLAlchemy or just dict())
                rows = [dict(zip(columns, row)) for row in result.fetchall()]
                return {
                    "success": True,
                    "requires_confirmation": False,
                    "rows": rows,
                    "columns": columns
                }
            else:
                return {
                    "success": True,
                    "requires_confirmation": False,
                    "rows": [],
                    "columns": [],
                    "message": "Query executed successfully. No rows returned."
                }
    except SQLAlchemyError as e:
        return {
            "success": False,
            "requires_confirmation": False,
            "error": str(e)
        }
    except Exception as e:
        return {
            "success": False,
            "requires_confirmation": False,
            "error": str(e)
        }
