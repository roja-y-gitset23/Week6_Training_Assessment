import re

# Keywords per specialist agent (matched at the start of a word)
ROUTES = {
    "refund": ["refund", "money back", "reimburse", "return", "chargeback"],
    "order_status": ["where is", "track", "status", "shipped", "delivery", "package"],
    "general_info": ["hours", "opening", "contact", "support", "payment methods", "address"],
}
PRIORITY = ["refund", "order_status", "general_info"]   # tie-breaker order


def route(request):
    text = request.lower()
    scores = {
        name: sum(1 for kw in kws if re.search(r"\b" + re.escape(kw), text))
        for name, kws in ROUTES.items()
    }
    if all(s == 0 for s in scores.values()):
        return "general_info"                            # safe fallback
    return max(PRIORITY, key=lambda n: (scores[n], -PRIORITY.index(n)))