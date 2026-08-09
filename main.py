import os
import psycopg
from dotenv import load_dotenv
from fastapi import FastAPI

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

def get_db():
    return psycopg.connect(DATABASE_URL)

# Test PostgreSQL connection
conn = get_db()
print("PostgreSQL connection successful!")
conn.close()

# Create table and seed tasks
conn = get_db()
cursor = conn.cursor()

cursor.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        id SERIAL PRIMARY KEY,
        title TEXT NOT NULL,
        done BOOLEAN NOT NULL DEFAULT FALSE
    )
""")

cursor.execute("SELECT COUNT(*) FROM tasks")
count = cursor.fetchone()[0]

if count == 0:
    cursor.execute(
        "INSERT INTO tasks (title, done) VALUES (%s, %s)",
        ("Learn PostgreSQL", False)
    )

    cursor.execute(
        "INSERT INTO tasks (title, done) VALUES (%s, %s)",
        ("Build CRUD API", False)
    )

    cursor.execute(
        "INSERT INTO tasks (title, done) VALUES (%s, %s)",
        ("Push project to GitHub", False)
    )

conn.commit()
cursor.close()
conn.close()

print("PostgreSQL table and seed data ready!")

app = FastAPI()