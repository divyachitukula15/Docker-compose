import os
import psycopg
from dotenv import load_dotenv
from fastapi import FastAPI,HTTPException,status,Header,Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from typing import Optional
from supabase import create_client
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials


load_dotenv()

# Create FastAPI app
app = FastAPI()
security = HTTPBearer()


SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# supabase client creation
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

@app.get("/test-supabase")
def test_supabase():
    response = supabase.auth.get_session()
    return {"message": "Supabase connection working"}

class AuthRequest(BaseModel):
    email: str
    password: str


@app.post("/auth/signup", status_code=status.HTTP_201_CREATED)
def signup(data: AuthRequest):

    # Missing email/password
    if not data.email or not data.password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email and password are required"
        )

    try:
        response = supabase.auth.sign_up({
            "email": data.email,
            "password": data.password
        })

        return {
            "user": response.user
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@app.post("/auth/login")
def login(data: AuthRequest):

    # Missing email/password
    if not data.email or not data.password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email and password are required"
        )

    try:
        response = supabase.auth.sign_in_with_password({
            "email": data.email,
            "password": data.password
        })

        # Successful login → 200
        return {
            "access_token": response.session.access_token,
            "refresh_token": response.session.refresh_token
        }

    except Exception:
        # Wrong credentials → 401
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid login credentials"
        )

@app.get("/public/info")
def public_info():
    return {
        "message": "Welcome stranger! This info is public."
    }

@app.get("/protected/profile")
def protected_profile(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    token = credentials.credentials

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "Access token required"}
        )

    return {
        "message": "Protected profile accessed",
        "token": token
    }


DATABASE_URL = os.getenv("DATABASE_URL")

def get_db():
    return psycopg.connect(DATABASE_URL)



# Pydantic model 
class Task(BaseModel): 
    title: str 
    done: bool = False

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

@app.post("/tasks", status_code=201, description="Create a new task")
def create_task(task: Task):
    if not task.title.strip():
        raise HTTPException(
            status_code=400,
            detail="Title cannot be empty"
        )

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO tasks (title, done)
        VALUES (%s, %s)
        RETURNING id, title, done
        """,
        (task.title, task.done)
    )

    row = cursor.fetchone()

    conn.commit()

    cursor.close()
    conn.close()

    return {
        "id": row[0],
        "title": row[1],
        "done": row[2]
    }

@app.put("/tasks/{task_id}", description="Update a task by ID")
def update_task(task_id: int, task: Task):

    if not task.title.strip():
        raise HTTPException(
            status_code=400,
            detail="Title cannot be empty"
        )

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE tasks
        SET title = %s, done = %s
        WHERE id = %s
        RETURNING id, title, done
        """,
        (task.title, task.done, task_id)
    )

    row = cursor.fetchone()

    if row is None:
        conn.rollback()
        cursor.close()
        conn.close()

        raise HTTPException(
            status_code=404,
            detail=f"Task {task_id} not found"
        )

    conn.commit()

    cursor.close()
    conn.close()

    return {
        "id": row[0],
        "title": row[1],
        "done": row[2]
    }

@app.delete("/tasks/{task_id}", status_code=204, description="Delete a task by ID")
def delete_task(task_id: int):

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM tasks WHERE id = %s RETURNING id",
        (task_id,)
    )

    row = cursor.fetchone()

    if row is None:
        conn.rollback()
        cursor.close()
        conn.close()

        raise HTTPException(
            status_code=404,
            detail=f"Task {task_id} not found"
        )

    conn.commit()

    cursor.close()
    conn.close()

    return None


