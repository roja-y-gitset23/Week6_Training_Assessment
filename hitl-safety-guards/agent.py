import json
import re
import uuid
from datetime import datetime, timezone

import db
from guards import is_injection, output_guard
from tools import TOOLS, run_tool


def now():
    return datetime.now(timezone.utc).isoformat()


def finish(run_id, status, reply, events, pending_id=None):
    db.execute("UPDATE runs SET status=?, reply=?, events=? WHERE run_id=?",
               (status, reply, "; ".join(events), run_id))
    return {"run_id": run_id, "status": status, "reply": reply,
            "pending_action_id": pending_id, "events": events}


def start_run(user, task):
    run_id = "run_" + uuid.uuid4().hex[:8]
    events = []
    db.execute("INSERT INTO runs VALUES (?,?,?,?,?,?,?)",
               (run_id, user, task, "RUNNING", "", "", now()))

    m = re.search(r"order\s+(\d+)", task, re.I)
    if not m:
        return finish(run_id, "COMPLETED", "Please mention an order id.", events)
    order_id = int(m.group(1))

    order = run_tool("get_order", {"order_id": order_id})          # READ: automatic
    if "error" in order:
        return finish(run_id, "COMPLETED", "Order not found.", events)

    # Prompt-injection defence: order notes are DATA, never instructions
    if is_injection(order.get("note", "")):
        events.append("Injection note ignored")

    policy = run_tool("check_policy", {"order_id": order_id})      # READ: automatic
    if policy["decision"] != "eligible":
        return finish(run_id, "COMPLETED", "Order is not eligible for a refund.", events)

    amount = order["amount"]   # amount ALWAYS comes from the order record, never from notes
    assert TOOLS["issue_refund"]["level"] == "DELETE_SEND"
    pid = db.execute(
        "INSERT INTO pending_actions(run_id, tool, tool_input, status, created_at) VALUES (?,?,?,?,?)",
        (run_id, "issue_refund", json.dumps({"order_id": order_id, "amount": amount}),
         "PENDING", now()))
    reply = output_guard(f"Refund of ${amount:.2f} for order {order_id} is waiting for human approval.", False)
    return finish(run_id, "WAITING_APPROVAL", reply, events, pid)


def resume(pending_id, decision):
    rows = db.query("SELECT * FROM pending_actions WHERE id=?", (pending_id,))
    if not rows:
        return None, "not found"
    p = rows[0]
    if p["status"] != "PENDING":
        return None, "already decided"

    inputs = json.loads(p["tool_input"])
    if decision == "approve":
        run_tool(p["tool"], {**inputs, "run_id": p["run_id"]}, approved=True)
        reply = output_guard(f"Refund of ${inputs['amount']:.2f} issued for order {inputs['order_id']}.", True)
        new_status = "APPROVED"
    else:
        reply = output_guard(f"Refund not issued for order {inputs['order_id']}.", False)
        new_status = "REJECTED"

    db.execute("UPDATE pending_actions SET status=?, decided_at=? WHERE id=?",
               (new_status, now(), pending_id))
    db.execute("UPDATE runs SET status='COMPLETED', reply=? WHERE run_id=?", (reply, p["run_id"]))
    return {"pending_action_id": pending_id, "decision": new_status,
            "run_id": p["run_id"], "run_status": "COMPLETED", "reply": reply}, None