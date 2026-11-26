import sqlite3

DB = "hitl.db"


def conn():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c


def execute(sql, params=()):
    c = conn()
    try:
        cur = c.execute(sql, params)
        c.commit()
        return cur.lastrowid
    finally:
        c.close()


def query(sql, params=()):
    c = conn()
    try:
        return [dict(r) for r in c.execute(sql, params).fetchall()]
    finally:
        c.close()


def init():
    execute("""CREATE TABLE IF NOT EXISTS runs(
        run_id TEXT PRIMARY KEY, user TEXT, task TEXT, status TEXT,
        reply TEXT, events TEXT, created_at TEXT)""")
    execute("""CREATE TABLE IF NOT EXISTS pending_actions(
        id INTEGER PRIMARY KEY AUTOINCREMENT, run_id TEXT, tool TEXT,
        tool_input TEXT, status TEXT, created_at TEXT, decided_at TEXT)""")
    execute("""CREATE TABLE IF NOT EXISTS refunds(
        id INTEGER PRIMARY KEY AUTOINCREMENT, order_id INTEGER,
        amount REAL, run_id TEXT)""")