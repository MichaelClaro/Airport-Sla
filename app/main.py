from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import sqlite3

app = FastAPI()

DB_PATH = "airport_v2.db"


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

    cur.execute("DELETE FROM gates")

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
        (21, "SBG25-01", "ANASEAMLESS", "Boarding SBG25", "Operational"),
        (22, "SBG25-02", "ANASEAMLESS", "Boarding SBG25", "Operational"),
        (23, "SBG46-01", "ANASEAMLESS", "Boarding SBG46", "Operational"),
        (24, "SBG46-02", "ANASEAMLESS", "Boarding SBG46", "Operational"),
        (25, "SBG47-01", "ANASEAMLESS", "Boarding SBG47", "Operational"),
        (26, "SBG47-02", "ANASEAMLESS", "Boarding SBG47", "Operational"),
    ])

    conn.commit()
    conn.close()


def calculate_priority(group_name, down_count):
    if group_name.startswith("Boarding"):
        if down_count >= 2:
            return "P1"
        elif down_count == 1:
            return "P2"
        return "OK"

    if group_name == "Security":
        if down_count >= 12:
            return "P1"
        elif down_count >= 8:
            return "P2"
        elif down_count >= 4:
            return "P3"
        elif down_count >= 1:
            return "P4"
        return "OK"

    if group_name == "Enrollment":
        if down_count >= 1:
            return "P4"
        return "OK"

    return "OK"


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


@app.get("/api/groups")
def get_groups():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    SELECT
        group_name,
        COUNT(*) as total_gates,
        SUM(CASE WHEN status = 'Down' THEN 1 ELSE 0 END) as down_count
    FROM gates
    GROUP BY group_name
    ORDER BY group_name
    """)

    rows = []
    for row in cur.fetchall():
        down_count = row["down_count"]
        rows.append({
            "group": row["group_name"],
            "total_gates": row["total_gates"],
            "down_count": down_count,
            "priority": calculate_priority(row["group_name"], down_count)
        })

    conn.close()
    return rows


@app.post("/api/gates/{gate_id}/status")
def update_gate_status(gate_id: int, payload: StatusUpdate):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT id, group_name FROM gates WHERE id = ?", (gate_id,))
    existing = cur.fetchone()

    if not existing:
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

    group_name = existing["group_name"]

    cur.execute("""
    SELECT COUNT(*) as total
    FROM gates
    WHERE group_name = ? AND status = 'Down'
    """, (group_name,))
    down_count = cur.fetchone()["total"]

    priority = calculate_priority(group_name, down_count)

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

    return {
        "success": True,
        "gate": gate,
        "group_summary": {
            "group": group_name,
            "down_count": down_count,
            "priority": priority
        }
    }


app.mount("/", StaticFiles(directory="static", html=True), name="static")
