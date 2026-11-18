"""FastAPI application for the Log Analyzer."""

import os
from typing import Optional

from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

import db
from parser import parse_content

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")

app = FastAPI(title="Log Analyzer", version="1.0.0")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

MAX_UPLOAD_BYTES = 20 * 1024 * 1024  # 20 MB
ALLOWED_EXTENSIONS = {".log", ".txt"}

SAMPLE_LOG = """\
2026-11-18 08:00:01 INFO Server started on port 8000
2026-11-18 08:00:03 INFO Connected to SQLite database
2026-11-18 08:00:10 DEBUG Cache warmed with 1,240 entries
2026-11-18 08:01:15 WARNING High memory usage detected (82%)
2026-11-18 08:02:30 ERROR Failed to reach upstream auth service: timeout after 5000ms
2026-11-18 08:02:31 ERROR Connection refused on port 5432
this line is completely malformed and should be stored as RAW
2026-11-18 08:03:00 INFO Retrying connection (attempt 2 of 3)
2026-11-18 08:03:12 WARN Deprecated API endpoint /v1/legacy called by client 10.0.4.21
2026-11-18 08:03:45 INFO Health check passed
2026-11-18 08:04:00 CRITICAL Disk space below 5% on /var/log
another raw unstructured line without timestamp
2026-11-18 08:05:20 INFO Scheduled backup completed successfully
"""


@app.on_event("startup")
def startup() -> None:
    db.init_db()


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


@app.post("/api/upload")
async def upload_log(file: UploadFile = File(...)) -> dict:
    filename = file.filename or "upload.log"
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Only .log and .txt files are allowed")

    data = await file.read()
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File exceeds the 20 MB limit")

    content = data.decode("utf-8", errors="replace")
    entries = parse_content(content)
    session_id = db.store_session(filename, entries)
    return {"session_id": session_id, "filename": filename, "entries": len(entries)}


@app.post("/api/sample")
def load_sample() -> dict:
    entries = parse_content(SAMPLE_LOG)
    session_id = db.store_session("sample_server.log", entries)
    return {"session_id": session_id, "filename": "sample_server.log", "entries": len(entries)}


@app.get("/api/sessions")
def get_sessions() -> list[dict]:
    return db.list_sessions()


@app.get("/api/logs/{session_id}")
def get_logs(
    session_id: int,
    level: Optional[str] = Query(default=None),
    q: Optional[str] = Query(default=None),
) -> dict:
    if session_id < 1:
        raise HTTPException(status_code=400, detail="Invalid session id")
    sessions = {s["id"] for s in db.list_sessions()}
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    return db.get_session_logs(session_id, level=level, query=q)


@app.delete("/api/sessions/{session_id}")
def delete_session(session_id: int) -> dict:
    if not db.delete_session(session_id):
        raise HTTPException(status_code=404, detail="Session not found")
    return {"deleted": session_id}
