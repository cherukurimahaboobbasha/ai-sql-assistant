from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from llm_service import generate_sql
import sqlite3
import anyio

app = FastAPI(title="AI SQL Assistant API", version="0.1.0")

# Enable CORS for local frontend execution
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class NaturalLanguageRequest(BaseModel):
    prompt: str

def execute_raw_sql(sql_query: str):
    try:
        conn = sqlite3.connect("app_data.db")
        cursor = conn.cursor()
        cursor.execute(sql_query)
        
        columns = [description[0] for description in cursor.description] if cursor.description else []
        rows = cursor.fetchall()
        conn.close()
        
        return {
            "success": True,
            "columns": columns,
            "data": rows,
            "row_count": len(rows),
            "error": None
        }
    except Exception as e:
        return {
            "success": False,
            "columns": [],
            "data": [],
            "row_count": 0,
            "error": str(e)
        }

@app.get("/")
def read_root():
    return {"status": "online", "message": "AI SQL Assistant API is running"}

@app.post("/api/generate-and-execute")
async def generate_and_execute(req: NaturalLanguageRequest):
    try:
        # Run blocking LLM call asynchronously off the main event loop
        generated_sql = await anyio.to_thread.run_sync(generate_sql, req.prompt)
        execution_result = execute_raw_sql(generated_sql)
        
        return {
            "user_prompt": req.prompt,
            "generated_sql": generated_sql,
            "execution": execution_result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))