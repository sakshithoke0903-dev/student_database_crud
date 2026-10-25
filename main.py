"""Students Database CRUD API built with FastAPI and SQLite."""
from contextlib import asynccontextmanager
from datetime import date
import os
import sqlite3
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Query, Response, status
from pydantic import BaseModel, ConfigDict, EmailStr, Field

DB_PATH = Path(os.getenv("DATABASE_PATH", "students.db"))


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                date_of_birth TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                phone TEXT,
                course TEXT,
                address TEXT,
                enrollment_date TEXT
            )
        """)


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield

app = FastAPI(
    title="Students Database CRUD API",
    description="A student records API using FastAPI and SQLite, created for the EWB Edu Tech Python Backend Development assignment.",
    version="1.0.0",
    lifespan=lifespan,
)


class StudentBase(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    date_of_birth: date
    email: EmailStr
    phone: Optional[str] = Field(default=None, max_length=30)
    course: Optional[str] = Field(default=None, max_length=120)
    address: Optional[str] = Field(default=None, max_length=300)
    enrollment_date: Optional[date] = None

    @classmethod
    def _clean(cls, value):
        return value


class StudentCreate(StudentBase):
    pass


class StudentUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    date_of_birth: Optional[date] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(default=None, max_length=30)
    course: Optional[str] = Field(default=None, max_length=120)
    address: Optional[str] = Field(default=None, max_length=300)
    enrollment_date: Optional[date] = None


class Student(StudentBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


def row_to_student(row: sqlite3.Row) -> dict:
    result = dict(row)
    for key in ("date_of_birth", "enrollment_date"):
        if result.get(key):
            result[key] = date.fromisoformat(result[key])
    return result


def fetch_student(student_id: int):
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM students WHERE id = ?", (student_id,)).fetchone()
    return row_to_student(row) if row else None


@app.get("/", tags=["General"])
def root():
    return {"message": "Students Database CRUD API is running", "docs": "/docs", "health": "/health"}


@app.get("/health", tags=["General"])
def health():
    return {"status": "ok"}


@app.post("/students", response_model=Student, status_code=status.HTTP_201_CREATED, tags=["Students"])
def create_student(student: StudentCreate):
    data = student.model_dump(mode="json")
    try:
        with get_connection() as conn:
            cursor = conn.execute(
                """INSERT INTO students (name, date_of_birth, email, phone, course, address, enrollment_date)
                   VALUES (:name, :date_of_birth, :email, :phone, :course, :address, :enrollment_date)""",
                data,
            )
            student_id = cursor.lastrowid
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=409, detail="A student with this email already exists.")
    return fetch_student(student_id)


@app.get("/students", response_model=list[Student], tags=["Students"])
def list_students(
    name: Optional[str] = Query(default=None, description="Filter by part of a student's name"),
    course: Optional[str] = Query(default=None, description="Filter by course"),
    born_after: Optional[date] = Query(default=None, description="Only students born after this date"),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
):
    clauses, params = [], []
    if name:
        clauses.append("LOWER(name) LIKE LOWER(?)")
        params.append(f"%{name}%")
    if course:
        clauses.append("LOWER(course) LIKE LOWER(?)")
        params.append(f"%{course}%")
    if born_after:
        clauses.append("date_of_birth > ?")
        params.append(born_after.isoformat())
    where = " WHERE " + " AND ".join(clauses) if clauses else ""
    params.extend([limit, offset])
    with get_connection() as conn:
        rows = conn.execute(f"SELECT * FROM students{where} ORDER BY id LIMIT ? OFFSET ?", params).fetchall()
    return [row_to_student(row) for row in rows]


@app.get("/students/{student_id}", response_model=Student, tags=["Students"])
def get_student(student_id: int):
    student = fetch_student(student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found.")
    return student


@app.patch("/students/{student_id}", response_model=Student, tags=["Students"])
def update_student(student_id: int, updates: StudentUpdate):
    current = fetch_student(student_id)
    if not current:
        raise HTTPException(status_code=404, detail="Student not found.")
    changes = updates.model_dump(exclude_unset=True, mode="json")
    if not changes:
        raise HTTPException(status_code=400, detail="Provide at least one field to update.")
    columns = ", ".join(f"{key} = ?" for key in changes)
    values = list(changes.values()) + [student_id]
    try:
        with get_connection() as conn:
            conn.execute(f"UPDATE students SET {columns} WHERE id = ?", values)
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=409, detail="A student with this email already exists.")
    return fetch_student(student_id)


@app.put("/students/{student_id}", response_model=Student, tags=["Students"], include_in_schema=True)
def replace_student(student_id: int, student: StudentCreate):
    if not fetch_student(student_id):
        raise HTTPException(status_code=404, detail="Student not found.")
    data = student.model_dump(mode="json")
    try:
        with get_connection() as conn:
            conn.execute("""UPDATE students SET name=:name, date_of_birth=:date_of_birth, email=:email,
                phone=:phone, course=:course, address=:address, enrollment_date=:enrollment_date WHERE id=:id""",
                {**data, "id": student_id})
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=409, detail="A student with this email already exists.")
    return fetch_student(student_id)


@app.delete("/students/{student_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Students"])
def delete_student(student_id: int):
    with get_connection() as conn:
        cursor = conn.execute("DELETE FROM students WHERE id = ?", (student_id,))
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Student not found.")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.post("/ask", tags=["Optional AI"])
def ask_students(question: str = Query(min_length=3, max_length=500)):
    """Optional local Ollama Q&A. Requires Ollama and a downloaded model."""
    import requests
    model = os.getenv("OLLAMA_MODEL", "llama3.2:1b")
    try:
        with get_connection() as conn:
            rows = conn.execute("SELECT id, name, date_of_birth, email, course FROM students ORDER BY id LIMIT 500").fetchall()
        context = [dict(row) for row in rows]
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": model, "stream": False,
                  "prompt": "Answer only from the student data below. If the data does not answer the question, say so. Do not execute SQL.\n"
                            f"Student data: {context}\nQuestion: {question}"},
            timeout=60,
        )
        response.raise_for_status()
        return {"answer": response.json().get("response", ""), "model": model}
    except requests.RequestException as exc:
        raise HTTPException(status_code=503, detail=f"Ollama is unavailable. Start Ollama and pull {model}.") from exc
