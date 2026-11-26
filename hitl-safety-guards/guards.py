import re
import time

CARD_RE = re.compile(r"\b(?:\d[ -]?){13,16}\b")
SSN_RE = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
SCOPE_WORDS = ("refund", "order", "customer", "email", "policy")
INJECTION_RE = re.compile(
    r"ignore (all|any|previous) (rules|instructions)|refund \d+ to this account|system prompt",
    re.I)
CLAIM_RE = re.compile(r"refund of [^.]*\bissued\b|refund (has been|was) (issued|processed)", re.I)


def input_guard(message):
    """Returns (ok, reason)."""
    if CARD_RE.search(message) or SSN_RE.search(message):
        return False, "message contains PII (card/SSN)"
    if not any(w in message.lower() for w in SCOPE_WORDS):
        return False, "out of scope (only order/refund/customer requests)"
    return True, ""


def is_injection(text):
    return bool(INJECTION_RE.search(text or ""))


def output_guard(reply, refund_executed):
    """No card numbers, no unsupported claims."""
    reply = CARD_RE.sub("[CARD REMOVED]", reply)
    if CLAIM_RE.search(reply) and not refund_executed:
        return "Refund has not been issued yet."
    return reply


class RateLimiter:
    def __init__(self, limit=5, window=3600):
        self.limit, self.window, self.hits = limit, window, {}

    def allow(self, user):
        now = time.time()
        recent = [t for t in self.hits.get(user, []) if now - t < self.window]
        if len(recent) >= self.limit:
            self.hits[user] = recent
            return False
        recent.append(now)
        self.hits[user] = recent
        return True