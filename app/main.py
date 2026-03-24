from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from pydantic import BaseModel

app = FastAPI()

gates = [
    {"id": 1, "name": "SCP 21", "project": "ANASEAMLESS", "group": "Security", "status": "Operational"},
    {"id": 2, "name": "SCP 22", "project": "ANASEAMLESS", "group": "Security", "status": "Down"},
    {"id": 3, "name": "KIOSK 01", "project": "ANASEAMLESS", "group": "Enrollment", "status": "Operational"},
    {"id": 4, "name": "SBG25-01", "project": "ANASEAMLESS", "group": "Boarding", "status": "Operational"},
]

class StatusUpdate(BaseModel):
    status: str

@app.get("/api/gates")
def get_gates():
    return gates

@app.post("/api/gates/{gate_id}/status")
def update_gate_status(gate_id: int, payload: StatusUpdate):
    for gate in gates:
        if gate["id"] == gate_id:
            gate["status"] = payload.status
            return {"success": True, "gate": gate}
    return JSONResponse(status_code=404, content={"success": False, "message": "Gate not found"})

app.mount("/", StaticFiles(directory="static", html=True), name="static")
