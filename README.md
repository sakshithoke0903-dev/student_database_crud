# Students Database CRUD API

A Python backend project for the **EWB Edu Tech Pvt. Ltd. Python Backend Development internship assignment**. It manages student records using **FastAPI** and **SQLite**, with an optional local AI question-answer endpoint powered by Ollama.

## Features

- Create, list, retrieve, update, and delete student records.
- SQLite persistence; the database is created automatically on startup.
- Filter students by name, course, or date of birth (`born_after`).
- Validated email/date fields, unique email addresses, pagination, and useful HTTP errors.
- Interactive API documentation and automated tests.
- Optional `/ask` endpoint that sends retrieved student records to a local Ollama model; the model does not execute SQL.

## Requirements

- Python 3.10 or newer
- pip
- Optional AI feature: [Ollama](https://ollama.com/)

## Run locally

1. Download or clone this repository.
2. Open a terminal in the project directory.
3. Create and activate a virtual environment:

   **Windows (PowerShell)**
   ```powershell
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   ```

   **macOS/Linux**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

4. Install dependencies:
   ```bash
   python -m pip install -r requirements.txt
   ```
5. Start the API:
   ```bash
   uvicorn main:app --reload
   ```
6. Open **http://127.0.0.1:8000/docs** to test the endpoints interactively.

The default database file is `students.db` in the current directory. It is intentionally excluded from Git. To use another location, set the `DATABASE_PATH` environment variable before starting the server.

## API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/` | API welcome message |
| `GET` | `/health` | Health check |
| `POST` | `/students` | Create a student |
| `GET` | `/students` | List students, with optional filters |
| `GET` | `/students/{student_id}` | Get one student |
| `PUT` | `/students/{student_id}` | Replace all editable student fields |
| `PATCH` | `/students/{student_id}` | Update selected fields |
| `DELETE` | `/students/{student_id}` | Delete a student |
| `POST` | `/ask?question=...` | Optional Ollama natural-language Q&A |

Student fields: `name`, `date_of_birth`, `email` (unique), `phone`, `course`, `address`, and `enrollment_date`. Dates use ISO format `YYYY-MM-DD`.

### Example: create a student

```bash
curl -X POST "http://127.0.0.1:8000/students" \
  -H "Content-Type: application/json" \
  -d '{"name":"Alex Student","date_of_birth":"2004-05-12","email":"alex@example.com","phone":"9876543210","course":"Computer Science","address":"Pune","enrollment_date":"2023-08-01"}'
```

### Example: list and filter

```bash
curl "http://127.0.0.1:8000/students"
curl "http://127.0.0.1:8000/students?name=alex"
curl "http://127.0.0.1:8000/students?course=computer&born_after=2000-01-01"
```

### Example: update and delete

```bash
curl -X PATCH "http://127.0.0.1:8000/students/1" \
  -H "Content-Type: application/json" -d '{"course":"Automation and Robotics"}'
curl -X DELETE "http://127.0.0.1:8000/students/1"
```

Use IDs returned by the API; the examples assume the created record has ID `1`.

## Optional AI extension (Ollama)

The core CRUD API works without Ollama. To enable `/ask`:

1. Install and start Ollama from [ollama.com](https://ollama.com/).
2. Download the example model:
   ```bash
   ollama pull llama3.2:1b
   ```
3. Start the API as above. Optionally set `OLLAMA_MODEL` to another local model name.
4. Ask a question, for example:
   ```bash
   curl -X POST "http://127.0.0.1:8000/ask?question=How%20many%20students%20are%20there%3F"
   ```

The endpoint retrieves a limited set of records from SQLite and supplies them as context. It does not allow the model to run SQL. Because language models can still make mistakes, verify answers against the API/database.

## Run tests

```bash
pytest -q
```

Tests use a temporary SQLite database and do not modify your local student database. GitHub Actions runs them on pushes and pull requests.

## Upload to GitHub

1. Create a **new empty repository** on GitHub (for example, `students-database-crud`). Do not add a README on GitHub if you already have this one.
2. Extract this project ZIP.
3. In a terminal opened inside the extracted `students-database-crud` folder, run:

   ```bash
   git init
   git add .
   git commit -m "Build students CRUD API with FastAPI and SQLite"
   git branch -M main
   git remote add origin https://github.com/YOUR-USERNAME/students-database-crud.git
   git push -u origin main
   ```

4. Replace `YOUR-USERNAME` with your GitHub username. Confirm the files appear in the repository.

## Security notes

- Use dummy data for demonstrations. Do not upload real student personal information, credentials, `.env` files, or the generated SQLite database.
- `.gitignore` excludes database files, virtual environments, and environment files.
- This is an internship/demo project. Add authentication, authorization, rate limiting, and deployment-specific configuration before using it for real student records.

## Project structure

```text
students-database-crud/
├── .github/workflows/tests.yml
├── tests/test_api.py
├── .env.example
├── .gitignore
├── main.py
├── requirements.txt
└── README.md
```
