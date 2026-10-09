import os
import time
from google import genai

# Fetch Gemini API key securely from environment variables
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
client = genai.Client(api_key=GEMINI_API_KEY)

SCHEMA_CONTEXT = """
You are a SQL expert. Generate executable SQLite queries based ONLY on the following schema:

Table users:
- id (INTEGER, Primary Key)
- name (TEXT)
- email (TEXT)
- created_at (DATETIME)

Table products:
- id (INTEGER, Primary Key)
- name (TEXT)
- category (TEXT)
- price (REAL)
- stock (INTEGER)

Table orders:
- id (INTEGER, Primary Key)
- user_id (INTEGER, Foreign Key -> users.id)
- product_id (INTEGER, Foreign Key -> products.id)
- quantity (INTEGER)
- total_amount (REAL)
- order_date (DATETIME)

Rules:
1. Return ONLY the raw SQL statement.
2. Do NOT wrap the query in markdown code blocks like ```sql or ```.
3. Do NOT include explanations or extra text.
"""

def generate_sql(user_prompt: str) -> str:
    full_prompt = f"{SCHEMA_CONTEXT}\n\nUser Question: {user_prompt}\nSQL Query:"

    # Primary and secondary active Gemini 3.5 models
    models_to_try = ["gemini-3.5-flash", "gemini-3.5-flash-lite"]
    response = None
    last_error = None

    for model_name in models_to_try:
        max_retries = 3
        backoff_delay = 1
        
        for attempt in range(max_retries):
            try:
                print(f"[LLM] Contacting model: {model_name} (Attempt {attempt + 1})...")
                response = client.models.generate_content(
                    model=model_name,
                    contents=full_prompt
                )
                if response and response.text:
                    print(f"[LLM] Success with {model_name}!")
                    break
            except Exception as e:
                last_error = e
                # Handle temporary high demand (503) gracefully
                if "503" in str(e) and attempt < max_retries - 1:
                    print(f"[LLM 503 Busy] Retrying {model_name} in {backoff_delay}s...")
                    time.sleep(backoff_delay)
                    backoff_delay *= 2
                    continue
                print(f"[LLM Error on {model_name}]: {e}")
                break

        if response and response.text:
            break

    if not response or not response.text:
        raise Exception(f"LLM Generation Failed. Details: {last_error}")

    sql_query = response.text.strip()

    # Clean markdown formatting if present
    if sql_query.startswith("```sql"):
        sql_query = sql_query[len("```sql"):].strip()
    elif sql_query.startswith("```"):
        sql_query = sql_query[len("```"):].strip()

    if sql_query.endswith("```"):
        sql_query = sql_query[:-3].strip()

    print(f"[LLM] Generated SQL: {sql_query}")

    validate_sql_security(sql_query)
    return sql_query


def validate_sql_security(sql: str):
    forbidden_keywords = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "TRUNCATE"]
    upper_sql = sql.upper()
    
    if not upper_sql.startswith("SELECT") and not upper_sql.startswith("WITH"):
        raise ValueError("Security Violation: Only SELECT database queries are permitted.")
        
    for word in forbidden_keywords:
        if word in upper_sql:
            raise ValueError(f"Security Violation: '{word}' statements are strictly blocked.")