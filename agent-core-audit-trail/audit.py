import json
import re
import uuid
from datetime import datetime, timezone

EMAIL_RE = re.compile(r"([A-Za-z0-9._%+-])[A-Za-z0-9._%+-]*@([A-Za-z0-9.-]+\.[A-Za-z]{2,})")


def mask_emails(text):
    return EMAIL_RE.sub(r"\1***@\2", text)


def count_tokens(*texts):
    # Simple estimate: 1 token per word (no LLM API needed)
    return sum(len(t.split()) for t in texts)


class AuditLog:
    def __init__(self, path="audit_log.jsonl"):
        self.path = path
        self.run_id = "run_" + uuid.uuid4().hex[:8]
        self.rows = []

    def log(self, step, thought, action, action_input, observation):
        row = {
            "run_id": self.run_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "step": step,
            "thought": mask_emails(thought),
            "action": action,
            "action_input": mask_emails(json.dumps(action_input)),
            "observation": mask_emails(observation),
            "tokens": count_tokens(thought, action, json.dumps(action_input), observation),
        }
        self.rows.append(row)
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(row) + "\n")
        return row