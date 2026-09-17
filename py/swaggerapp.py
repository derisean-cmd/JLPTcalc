from fastapi import FastAPI
from pydantic import BaseModel
import sqlite3
from datetime import datetime

# Start the system
app = FastAPI(title="JLPT Score API")

# Open database
def get_db_connection():
    conn = sqlite3.connect("jlpt.db")
    conn.row_factory = sqlite3.Row
    return conn

# What info a score has
class ScoreRecord(BaseModel):
    username: str
    paper_name: str
    vocab_grammar: float
    reading: float
    listening: float
    total: float
    passed: str

# ➕ CREATE: Save score (STUDENT USES THIS)
@app.post("/scores/")
def create_score(record: ScoreRecord):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO results 
        (username, paper_name, vocab_grammar, reading, listening, total, passed, date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        record.username, record.paper_name,
        record.vocab_grammar, record.reading, record.listening,
        record.total, record.passed,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))
    conn.commit()
    record_id = cursor.lastrowid
    conn.close()
    return {"id": record_id, "message": "Score saved ✅"}

# 📋 READ: View history (STUDENT USES THIS)
@app.get("/scores/{username}")
def read_scores(username: str):
    conn = get_db_connection()
    records = conn.execute("""
        SELECT * FROM results WHERE username = ? ORDER BY date DESC
    """, (username,)).fetchall()
    conn.close()
    return {"count": len(records), "results": [dict(r) for r in records]}