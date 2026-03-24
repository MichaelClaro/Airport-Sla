from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import sqlite3

app = FastAPI()
DB_PATH = "airport.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS gates (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        project_name TEXT NOT NULL,
        group_name TEXT NOT NULL,
        status TEXT NOT NULL
    )
    """)

    cur.execute("SELECT COUNT(*) as total FROM gates")
    total = cur.fetchone()["total"]

   if True:
    cur.executemany("""
    INSERT INTO gates (id, name, project_name, group_name, status)
    VALUES (?, ?, ?, ?, ?)
    """, [
        (1, "SCP 11", "ANASEAMLESS", "Security", "Operational"),
        (2, "SCP 12", "ANASEAMLESS", "Security", "Operational"),
        (3, "SCP 14", "ANASEAMLESS", "Security", "Operational"),
        (4, "SCP 15", "ANASEAMLESS", "Security", "Operational"),
        (5, "SCP 16", "ANASEAMLESS", "Security", "Operational"),
        (6, "SCP 17", "ANASEAMLESS", "Security", "Operational"),
        (7, "SCP 21", "ANASEAMLESS", "Security", "Operational"),
        (8, "SCP 22", "ANASEAMLESS", "Security", "Operational"),
        (9, "SCP 23", "ANASEAMLESS", "Security", "Operational"),
        (10, "SCP 24", "ANASEAMLESS", "Security", "Operational"),
        (11, "SCP 25", "ANASEAMLESS", "Security", "Operational"),
        (12, "SCP 28", "ANASEAMLESS", "Security", "Operational"),
        (13, "SCP 29", "ANASEAMLESS", "Security", "Operational"),
        (14, "SCP 30", "ANASEAMLESS", "Security", "Operational"),
        (15, "SCP 31", "ANASEAMLESS", "Security", "Operational"),

        (16, "KIOSK 01", "ANASEAMLESS", "Enrollment", "Operational"),
        (17, "KIOSK 03", "ANASEAMLESS", "Enrollment", "Operational"),
        (18, "KIOSK 04", "ANASEAMLESS", "Enrollment", "Operational"),
        (19, "KIOSK 05", "ANASEAMLESS", "Enrollment", "Operational"),
        (20, "KIOSK 06", "ANASEAMLESS", "Enrollment", "Operational"),

        (21, "SBG25-01", "ANASEAMLESS", "Boarding", "Operational"),
        (22, "SBG25-02", "ANASEAMLESS", "Boarding", "Operational"),
        (23, "SBG46-01", "ANASEAMLESS", "Boarding", "Operational"),
        (24, "SBG46-02", "ANASEAMLESS", "Boarding", "Operational"),
        (25, "SBG47-01", "ANASEAMLESS", "Boarding", "Operational"),
        (26, "SBG47-02", "ANASEAMLESS", "Boarding", "Operational"),
    ])

    conn.commit()
    conn.close()


init_db()


class StatusUpdate(BaseModel):
    status: str


@app.get("/api/gates")
def get_gates():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT
            id,
            name,
            project_name as project,
            group_name as "group",
            status
        FROM gates
        ORDER BY id
    """)
    rows = [dict(row) for row in cur.fetchall()]
    conn.close()
    return rows


@app.post("/api/gates/{gate_id}/status")
def update_gate_status(gate_id: int, payload: StatusUpdate):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT id FROM gates WHERE id = ?", (gate_id,))
    row = cur.fetchone()

    if not row:
        conn.close()
        return JSONResponse(
            status_code=404,
            content={"success": False, "message": "Gate not found"}
        )

    cur.execute(
        "UPDATE gates SET status = ? WHERE id = ?",
        (payload.status, gate_id)
    )
    conn.commit()

    cur.execute("""
        SELECT
            id,
            name,
            project_name as project,
            group_name as "group",
            status
        FROM gates
        WHERE id = ?
    """, (gate_id,))
    gate = dict(cur.fetchone())

    conn.close()
    return {"success": True, "gate": gate}


app.mount("/", StaticFiles(directory="static", html=True), name="static")
