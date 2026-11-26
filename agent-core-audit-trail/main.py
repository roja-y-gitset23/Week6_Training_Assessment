import json
from agent import run_agent

audit = run_agent("Customer 5 asks for a refund for order 1042")

print("\n===== FULL AUDIT TRAIL =====")
for row in audit.rows:
    print(json.dumps(row, indent=2))