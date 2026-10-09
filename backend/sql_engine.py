from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from database import engine

def execute_sql_query(query_str: str):
    """
    Executes a SQL query string against the SQLite database safely.
    Returns a dictionary containing column headers, row data, and execution status.
    """
    # Clean up formatting whitespace or trailing semicolons
    cleaned_query = query_str.strip()
    
    # Simple safety check: prevent destructive operations for now
    forbidden_keywords = ["DROP", "DELETE", "TRUNCATE", "ALTER"]
    if any(keyword in cleaned_query.upper() for keyword in forbidden_keywords):
        return {
            "success": False,
            "error": "Destructive query detected. Only SELECT and safe operations are permitted.",
            "columns": [],
            "data": []
        }

    try:
        with engine.connect() as connection:
            result = connection.execute(text(cleaned_query))
            
            # If the query returns rows (e.g., SELECT statements)
            if result.returns_rows:
                columns = list(result.keys())
                rows = [dict(zip(columns, row)) for row in result.fetchall()]
                return {
                    "success": True,
                    "columns": columns,
                    "data": rows,
                    "row_count": len(rows),
                    "error": None
                }
            else:
                # For non-selecting commands like INSERT or UPDATE
                connection.commit()
                return {
                    "success": True,
                    "columns": [],
                    "data": [],
                    "row_count": result.rowcount,
                    "error": None
                }

    except SQLAlchemyError as e:
        return {
            "success": False,
            "error": str(e.orig) if hasattr(e, "orig") else str(e),
            "columns": [],
            "data": []
        }