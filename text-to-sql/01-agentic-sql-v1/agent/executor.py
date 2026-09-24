"""
Day 15 — Step 4: Execution

Enforces, in addition to Step 3's query-shape validation:
  - a genuinely READ-ONLY connection (SQLite URI mode=ro — the OS/DB
    layer refuses writes even if a mutating query somehow got past
    validation; defense in depth, not a replacement for the validator)
  - a query timeout (SQLite has no native statement timeout like
    Postgres's statement_timeout, so this uses a watcher thread that
    calls connection.interrupt() if the query runs too long)
  - audit logging of every execution attempt, success or failure

On real PostgreSQL: open the connection as a role with SELECT-only
GRANTs (a real read-only DB user, not just a URI flag), and use
`SET statement_timeout = '5s'` for a genuine server-enforced timeout
instead of the client-side interrupt() used here.
"""

import json
import os
import sqlite3
import threading
import time
import uuid

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "company.db")
LOGS_DIR = os.path.join(os.path.dirname(__file__), "..", "logs")
QUERY_TIMEOUT_SECONDS = 5


def _get_readonly_connection(db_path: str = DB_PATH) -> sqlite3.Connection:
    uri = f"file:{db_path}?mode=ro"
    return sqlite3.connect(uri, uri=True)


def execute_query(sql: str, question: str = "", attempt: int = 1) -> dict:
    """
    Returns {"success": bool, "rows": list, "columns": list, "error": str | None, "latency_ms": int}.
    Every call is logged to logs/audit_log.jsonl regardless of outcome.
    """
    request_id = str(uuid.uuid4())[:8]
    start = time.time()
    result = {"success": False, "rows": [], "columns": [], "error": None}

    try:
        conn = _get_readonly_connection()
        cursor = conn.cursor()

        timed_out = {"flag": False}

        def _watchdog():
            time.sleep(QUERY_TIMEOUT_SECONDS)
            timed_out["flag"] = True
            conn.interrupt()

        watchdog = threading.Thread(target=_watchdog, daemon=True)
        watchdog.start()

        cursor.execute(sql)
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        rows = cursor.fetchall()

        conn.close()

        result["success"] = True
        result["rows"] = rows
        result["columns"] = columns

    except sqlite3.OperationalError as e:
        if "interrupted" in str(e).lower():
            result["error"] = f"Query timed out after {QUERY_TIMEOUT_SECONDS}s"
        else:
            result["error"] = str(e)
    except Exception as e:
        result["error"] = str(e)

    latency_ms = round((time.time() - start) * 1000)
    result["latency_ms"] = latency_ms

    _audit_log({
        "request_id": request_id,
        "attempt": attempt,
        "question": question,
        "sql": sql,
        "success": result["success"],
        "error": result["error"],
        "row_count": len(result["rows"]),
        "latency_ms": latency_ms,
        "timestamp": time.time(),
    })

    return result


def _audit_log(entry: dict) -> None:
    os.makedirs(LOGS_DIR, exist_ok=True)
    path = os.path.join(LOGS_DIR, "audit_log.jsonl")
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, default=str) + "\n")


if __name__ == "__main__":
    result = execute_query("SELECT COUNT(*) FROM customers", question="How many customers?")
    print(result)
