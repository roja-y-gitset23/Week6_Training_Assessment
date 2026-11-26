import json

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

import agent
import db
from guards import RateLimiter, input_guard

db.init()
app = FastAPI(title="HITL and Safety Guards")
limiter = RateLimiter(limit=5, window=3600)   # 5 runs per user per hour


class RunBody(BaseModel):
    user: str
    message: str


@app.post("/agent/run")
def run_agent(body: RunBody):
    ok, reason = input_guard(body.message)            # input guard first
    if not ok:
        raise HTTPException(400, f"Input guard: {reason}")
    if not limiter.allow(body.user):                  # then rate limit
        raise HTTPException(429, "Rate limit: max 5 agent runs per user per hour")
    return agent.start_run(body.user, body.message)


@app.get("/pending-actions")
def pending_actions():
    rows = db.query("SELECT * FROM pending_actions WHERE status='PENDING'")
    for r in rows:
        r["tool_input"] = json.loads(r["tool_input"])
    return rows


def _decide(pending_id, decision):
    result, err = agent.resume(pending_id, decision)
    if err == "not found":
        raise HTTPException(404, "pending action not found")
    if err:
        raise HTTPException(409, "pending action already decided")
    return result


@app.post("/pending-actions/{pending_id}/approve")
def approve(pending_id: int):
    return _decide(pending_id, "approve")


@app.post("/pending-actions/{pending_id}/reject")
def reject(pending_id: int):
    return _decide(pending_id, "reject")


@app.get("/runs/{run_id}")
def get_run(run_id: str):
    rows = db.query("SELECT * FROM runs WHERE run_id=?", (run_id,))
    if not rows:
        raise HTTPException(404, "run not found")
    return rows[0]