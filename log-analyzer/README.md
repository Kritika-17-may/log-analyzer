# Log Analyzer

A clean, professional web dashboard for uploading, parsing, searching and filtering log files (`.log`, `.txt`). Built with Python, FastAPI, SQLite, HTML, CSS and vanilla JavaScript.

## Features

- Upload `.log` and `.txt` files (up to 20 MB)
- Automatic parsing of timestamps, log levels (INFO, WARNING, ERROR, DEBUG, CRITICAL, RAW, etc.) and messages
- Malformed lines are safely stored as `RAW` — the parser never crashes
- Dashboard statistics: total, ERROR, WARNING and INFO counts
- Filter by severity level and keyword search (debounced)
- "Load Sample Logs" button with a built-in demo log
- All uploaded sessions persisted in SQLite (`logs.db`)
- Session list with per-session delete

## Project structure

```
log-analyzer/
├── main.py            # FastAPI app and API routes
├── parser.py          # Log line parsing, levels, filtering
├── db.py              # SQLite schema and queries
├── static/
│   ├── index.html     # Dashboard markup
│   ├── style.css      # Dark professional theme
│   └── app.js         # Frontend logic
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── README.md
```

## Run locally

```bash
pip install -r requirements.txt
uvicorn main:app --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000

## Run with Docker

```bash
docker compose up --build
```

Then open http://localhost:8000. SQLite data is persisted in the `log-data` volume (`/app/data/logs.db`).

## API endpoints

| Method | Path                    | Description                                  |
|--------|-------------------------|----------------------------------------------|
| GET    | `/`                     | Dashboard UI                                 |
| POST   | `/api/upload`           | Upload a `.log`/`.txt` file (multipart)      |
| POST   | `/api/sample`           | Load built-in sample log                     |
| GET    | `/api/sessions`         | List stored sessions                         |
| GET    | `/api/logs/{id}`        | Get logs; query params: `level`, `q`         |
| DELETE | `/api/sessions/{id}`    | Delete a session and its entries             |

## Log format

Lines matching `YYYY-MM-DD HH:MM:SS LEVEL message` (ISO `T` separator and fractional seconds also supported) are parsed into structured entries. `WARN` maps to `WARNING`, `FATAL` to `CRITICAL`. Anything else is stored as `RAW`.
