ORDERS = {
    1042: {"order_id": 1042, "customer_id": 5, "amount": 49.99,
           "status": "delivered", "delivered_days_ago": 10},
}
CUSTOMERS = {
    5: {"customer_id": 5, "name": "Asha Raman", "email": "asha.raman@example.com"},
}
REFUND_WINDOW_DAYS = 30


def get_order(order_id):
    order = ORDERS.get(int(order_id))
    return order if order else {"error": f"order {order_id} not found"}


def get_customer(customer_id):
    cust = CUSTOMERS.get(int(customer_id))
    return cust if cust else {"error": f"customer {customer_id} not found"}


def check_policy(order_id):
    order = ORDERS.get(int(order_id))
    if not order:
        return {"decision": "not_found"}
    ok = order["status"] == "delivered" and order["delivered_days_ago"] <= REFUND_WINDOW_DAYS
    return {"decision": "eligible" if ok else "not_eligible",
            "reason": f"delivered {order['delivered_days_ago']} days ago, window {REFUND_WINDOW_DAYS} days"}


def draft_email(customer_id, text):
    cust = CUSTOMERS.get(int(customer_id))
    if not cust:
        return {"error": "customer not found"}
    return {"to": cust["email"], "body": text, "status": "DRAFT (not sent)"}


def issue_refund(order_id, amount):
    # High risk: never executes directly, always needs human approval.
    return {"status": "PENDING APPROVAL", "order_id": int(order_id), "amount": float(amount)}


TOOLS = {
    "get_order": {
        "fn": get_order, "risk": "low", "terminal": False,
        "schema": {"order_id": "int"},
        "show": lambda i, r: f"get_order({i['order_id']})",
    },
    "get_customer": {
        "fn": get_customer, "risk": "low", "terminal": False,
        "schema": {"customer_id": "int"},
        "show": lambda i, r: f"get_customer({i['customer_id']})",
    },
    "check_policy": {
        "fn": check_policy, "risk": "low", "terminal": False,
        "schema": {"order_id": "int"},
        "show": lambda i, r: f"check_policy({i['order_id']}) -> {r['decision']}",
    },
    "draft_email": {
        "fn": draft_email, "risk": "medium", "terminal": False,
        "schema": {"customer_id": "int", "text": "str"},
        "show": lambda i, r: f"draft_email({i['customer_id']})",
    },
    "issue_refund": {
        "fn": issue_refund, "risk": "high", "terminal": True,  # terminal signal
        "schema": {"order_id": "int", "amount": "float"},
        "show": lambda i, r: f"issue_refund -> {r['status']}",
    },
}