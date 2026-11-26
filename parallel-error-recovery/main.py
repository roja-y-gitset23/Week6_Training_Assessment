import asyncio
import random
import time

import tools

MAX_RETRIES = 2
RETRY_WAIT = 0.2


async def call_with_retry(name, make_call):
    """Call a tool. On failure, retry up to MAX_RETRIES times.
    Never raises: errors are returned as the observation."""
    try:
        return {"tool": name, "ok": True, "observation": await make_call()}
    except Exception as e:
        err = str(e) or type(e).__name__
    msg = f"Tool failed: {err}"

    for n in range(1, MAX_RETRIES + 1):
        await asyncio.sleep(RETRY_WAIT)
        try:
            result = await make_call()
            print(f"{msg} -> retry {n} succeeded")
            return {"tool": name, "ok": True, "observation": result}
        except Exception as e:
            err = str(e) or type(e).__name__
            msg += f" -> retry {n} failed"

    print(f"{msg} -> giving up")
    return {"tool": name, "ok": False, "observation": f"ERROR: {err}"}


async def timing_demo():
    # Reliable calls (flaky=False) so only the timing is compared
    calls = [
        lambda: tools.get_order(1042),
        lambda: tools.get_customer(5),
        lambda: tools.check_policy(1042, flaky=False),
    ]

    start = time.perf_counter()
    for c in calls:
        await c()
    sequential = time.perf_counter() - start

    start = time.perf_counter()
    await asyncio.gather(*(c() for c in calls))
    parallel = time.perf_counter() - start

    print(f"Sequential {sequential:.1f} s | Parallel {parallel:.1f} s")


async def agent_run(run_no):
    print(f"\n--- Run {run_no} ---")
    results = await asyncio.gather(
        call_with_retry("get_order", lambda: tools.get_order(1042)),
        call_with_retry("get_customer", lambda: tools.get_customer(5)),
        call_with_retry("check_policy", lambda: tools.check_policy(1042)),
    )
    for r in results:
        status = "OK" if r["ok"] else "FAILED (error sent to model)"
        print(f"  {r['tool']}: {status}")
    print(f"Run {run_no} finished without crashing")


async def main():
    random.seed(7)
    await timing_demo()

    tools.STATE["force_fail_once"] = True   # run 1 shows: timeout -> retry 1 succeeded
    crashes = 0
    for i in range(1, 4):
        try:
            await agent_run(i)
        except Exception as e:
            crashes += 1
            print(f"Run {i} CRASHED: {e}")

    print(f"\n3 runs completed | crashes: {crashes}")


if __name__ == "__main__":
    asyncio.run(main())