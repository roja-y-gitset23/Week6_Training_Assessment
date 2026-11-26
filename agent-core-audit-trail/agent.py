import json
import re
from tools import TOOLS
from audit import AuditLog

MAX_ITERATIONS = 8


def plan(task, history):
    """Rule-based planner (stands in for the LLM). Returns thought, action, input."""
    order_id = int(re.search(r"order\s+(\d+)", task, re.I).group(1))
    done = {h["action"]: h for h in history}

    if "get_order" not in done:
        return "I need the order details first.", "get_order", {"order_id": order_id}
    order = done["get_order"]["result"]

    if "check_policy" not in done:
        return "Check whether the order is eligible for a refund.", "check_policy", {"order_id": order_id}
    policy = done["check_policy"]["result"]

    if policy["decision"] == "eligible" and "issue_refund" not in done:
        return "Order is eligible, so request the refund.", "issue_refund", \
            {"order_id": order_id, "amount": order["amount"]}

    return "No further action needed.", "final_answer", {"answer": "Done."}


def run_agent(task):
    audit = AuditLog()
    history = []
    print(f"Task: {task}\nRun ID: {audit.run_id}\n")

    for step in range(1, MAX_ITERATIONS + 1):
        thought, action, action_input = plan(task, history)

        if action == "final_answer":                       # stop: final answer
            audit.log(step, thought, action, action_input, action_input["answer"])
            print(f"Step {step}: final_answer")
            return audit

        tool = TOOLS[action]
        missing = set(tool["schema"]) - set(action_input)
        result = {"error": f"missing args {missing}"} if missing else tool["fn"](**action_input)

        audit.log(step, thought, action, action_input, json.dumps(result))
        history.append({"action": action, "result": result})
        print(f"Step {step}: {tool['show'](action_input, result)}")

        if tool["terminal"]:                               # stop: terminal tool signal
            return audit

    audit.log(MAX_ITERATIONS, "Iteration limit reached.", "stop", {}, "MAX_ITERATIONS")
    print("Stopped: iteration limit reached")             # stop: limit
    return audit