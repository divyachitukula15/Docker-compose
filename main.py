import os
import psycopg
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import JSONResponse

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

# GET - Read all tasks
@app.get("/tasks", description="Get all tasks")
def get_tasks():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM tasks")
    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    return [
        {
            "id": row[0],
            "title": row[1],
            "done": row[2]
        }
        for row in rows
    ]


# GET - Read one task
@app.get("/tasks/{task_id}", description="Get a single task by ID")
def get_task_using_id(task_id: int):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM tasks WHERE id = %s",
        (task_id,)
    )

    row = cursor.fetchone()

    cursor.close()
    conn.close()

    if row is None:
        return JSONResponse(
            status_code=404,
            content={"error": f"Task {task_id} not found"}
        )

    return {
        "id": row[0],
        "title": row[1],
        "done": row[2]
    }