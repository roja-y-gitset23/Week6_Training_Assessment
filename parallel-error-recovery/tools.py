import asyncio
import random

DELAY = 1.0        # each lookup takes 1 second
FAIL_RATE = 0.5    # check_policy fails randomly 50% of the time

# Used once so the demo always shows a failure followed by a successful retry
STATE = {"force_fail_once": False}


async def get_order(order_id):
    await asyncio.sleep(DELAY)
    return {"order_id": order_id, "customer_id": 5, "amount": 49.99, "status": "delivered"}


async def get_customer(customer_id):
    await asyncio.sleep(DELAY)
    return {"customer_id": customer_id, "name": "Asha Raman"}


async def check_policy(order_id, flaky=True):
    await asyncio.sleep(DELAY)
    if flaky:
        if STATE["force_fail_once"]:
            STATE["force_fail_once"] = False
            raise TimeoutError("timeout")
        if random.random() < FAIL_RATE:
            raise TimeoutError("timeout")
    return {"order_id": order_id, "decision": "eligible"}