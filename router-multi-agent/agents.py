import asyncio

DELAY = 1.0   # each lookup takes 1 second


# ---- 3 specialist agents ----
async def refund_agent(request):
    return "Refund agent: I checked the refund policy and will start your refund request."


async def order_status_agent(request):
    return "Order-status agent: your order is on its way."


async def general_info_agent(request):
    return "General-info agent: here is the information you asked for."


AGENTS = {
    "refund": refund_agent,
    "order_status": order_status_agent,
    "general_info": general_info_agent,
}


# ---- 2 independent sub-tasks (run in parallel by the orchestrator) ----
async def fetch_order_status(order_id):
    await asyncio.sleep(DELAY)
    return f"Order {order_id} was delivered 10 days ago"


async def check_refund_eligibility(order_id):
    await asyncio.sleep(DELAY)
    return f"Order {order_id} is eligible for a refund (within 30 days)"