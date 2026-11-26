import asyncio
import time

from agents import AGENTS, check_refund_eligibility, fetch_order_status
from router import route

TESTS = [
    # refund
    ("I want a refund for order 1042", "refund"),
    ("Please give me my money back for the damaged item", "refund"),
    ("Can I return this product and get reimbursed?", "refund"),
    # order status
    ("Where is my order 1042?", "order_status"),
    ("Track my package please", "order_status"),
    ("What is the delivery status of order 1050?", "order_status"),
    # general info
    ("What are your opening hours?", "general_info"),
    ("How can I contact customer support?", "general_info"),
    ("What payment methods do you accept?", "general_info"),
]

DESIGN = [
    "1. Orchestrator: one small router/planner agent reads the request and picks a specialist.",
    "2. Sub-agents: refund, order-status and general-info each get their own tools and prompt.",
    "3. Independent sub-tasks (status lookup, policy check) run in parallel with asyncio.gather.",
    "4. The orchestrator aggregates the sub-agent results into one final answer for the user.",
    "5. High-risk tools (issue_refund) stay behind human approval, only in the refund agent.",
    "6. Worth it when tools/prompts grow large or tasks are independent; not for tiny systems.",
]


async def main():
    # ---- Part 1: routing test ----
    print("=== Routing test (9 requests) ===")
    correct = 0
    for request, expected in TESTS:
        got = route(request)
        ok = got == expected
        correct += ok
        print(f"[{'OK' if ok else 'WRONG'}] {request!r:55} -> {got}")
        reply = await AGENTS[got](request)
    print(f"\nRouting accuracy {correct}/{len(TESTS)}")

    # ---- Part 2: orchestrator / sub-agent design (6 lines) ----
    print("\n=== Orchestrator and sub-agents (6 lines) ===")
    for line in DESIGN:
        print(line)

    # ---- Part 3: 2 independent sub-tasks in parallel ----
    print("\n=== Parallel sub-tasks ===")
    order_id = 1042

    start = time.perf_counter()
    await fetch_order_status(order_id)
    await check_refund_eligibility(order_id)
    sequential = time.perf_counter() - start

    start = time.perf_counter()
    status, eligibility = await asyncio.gather(
        fetch_order_status(order_id), check_refund_eligibility(order_id))
    parallel = time.perf_counter() - start

    print(f"Sequential {sequential:.1f} s | Parallel {parallel:.1f} s")
    print(f"Aggregated answer: {status}; {eligibility}.")


if __name__ == "__main__":
    asyncio.run(main())