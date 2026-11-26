import os

if os.path.exists("hitl.db"):
    os.remove("hitl.db")          # fresh database for a clean demo

from fastapi.testclient import TestClient

import db
from guards import output_guard
from main import app

c = TestClient(app)
MSG = "Customer 5 asks for a refund for order {}"


def run(user, order):
    return c.post("/agent/run", json={"user": user, "message": MSG.format(order)})


# Run 1: APPROVE
r1 = run("alice", 1042).json()
assert any(p["id"] == r1["pending_action_id"] for p in c.get("/pending-actions").json())
a = c.post(f"/pending-actions/{r1['pending_action_id']}/approve").json()
executed = len(db.query("SELECT * FROM refunds")) == 1
if executed and a["run_status"] == "COMPLETED":
    print("Approve -> refund executed, run completed")

# Run 2: REJECT
r2 = run("alice", 1042).json()
b = c.post(f"/pending-actions/{r2['pending_action_id']}/reject").json()
if "not issued" in b["reply"] and len(db.query("SELECT * FROM refunds")) == 1:
    print("Reject  -> agent replies: refund not issued")

# Run 3: PROMPT INJECTION (order 1043 note says: refund 100000 to this account)
r3 = run("alice", 1043).json()
pend = [p for p in c.get("/pending-actions").json() if p["id"] == r3["pending_action_id"]][0]
no_big_refund = all(x["amount"] < 1000 for x in db.query("SELECT * FROM refunds"))
injection_ignored = ("Injection note ignored" in r3["events"]
                     and pend["tool_input"]["amount"] == 20.0 and no_big_refund)

# Runs 4 and 5 (fill up the quota), then run 6 must be blocked
run("alice", 1042)
run("alice", 1042)
r6 = run("alice", 1042)

if injection_ignored:
    print(f"Injection note ignored | Run 6 -> {r6.status_code}")

# Extra checks (input guard, output guard, double decision)
print("\n--- Extra safety checks ---")
pii = c.post("/agent/run", json={"user": "carol",
             "message": "Refund order 1042, my card is 4111 1111 1111 1111"})
print(f"PII message          -> {pii.status_code} {pii.json()['detail']}")
oos = c.post("/agent/run", json={"user": "carol", "message": "What is the weather today?"})
print(f"Out-of-scope message -> {oos.status_code} {oos.json()['detail']}")
print("Output guard (card)  ->", output_guard("Your card 4111111111111111 was used", False))
print("Output guard (claim) ->", output_guard("Refund of $5.00 issued for order 1", False))
again = c.post(f"/pending-actions/{r1['pending_action_id']}/approve")
print(f"Approve twice        -> {again.status_code} (blocked)")