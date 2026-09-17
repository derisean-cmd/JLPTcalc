# This is and simple file that stores:
# Users (login info)
# Your test papers (answer keys, scoring)
# Every user's past scores (history)
# Why: Saves everything permanently — data stays even after you close the app.

import sqlite3

# Connect to (or create) database file
conn = sqlite3.connect("jlpt.db")
c = conn.cursor()

# --- Table 1: Registered Users ---
c.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
)
""")

# --- Table 2: Your Paper Library ---
c.execute("""
CREATE TABLE IF NOT EXISTS papers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    paper_name TEXT NOT NULL,
    folder_path TEXT NOT NULL,
    answer_key TEXT NOT NULL,
    scoring_weights TEXT NOT NULL,
    page_guide TEXT NOT NULL
)
""")

# --- Table 3: User Score History ---
c.execute("""
CREATE TABLE IF NOT EXISTS results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    paper_name TEXT NOT NULL,
    vocab_grammar REAL,
    reading REAL,
    listening REAL,
    total REAL,
    passed TEXT,
    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

conn.commit()
conn.close()
print("✅ Database created successfully!")