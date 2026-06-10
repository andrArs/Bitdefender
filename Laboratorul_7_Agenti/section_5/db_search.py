from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any, Iterable


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


DB_PATH = Path(__file__).resolve().parent / "team_sessions.db"


def connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def print_rows(rows: Iterable[sqlite3.Row]) -> None:
    rows = list(rows)
    if not rows:
        print("(no rows)")
        return

    headers = rows[0].keys()
    widths = {header: len(header) for header in headers}
    for row in rows:
        for header in headers:
            value = row[header]
            text = "" if value is None else str(value)
            widths[header] = max(widths[header], len(text))

    header_line = " | ".join(header.ljust(widths[header]) for header in headers)
    separator_line = "-+-".join("-" * widths[header] for header in headers)
    print(header_line)
    print(separator_line)
    for row in rows:
        print(" | ".join(("" if row[header] is None else str(row[header])).ljust(widths[header]) for header in headers))


def decode_jsonish(value: Any) -> Any:
    current = value
    for _ in range(2):
        if not isinstance(current, str):
            break
        try:
            current = json.loads(current)
        except Exception:
            break
    return current


def show_tables(conn: sqlite3.Connection) -> None:
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
    ).fetchall()
    print_rows(rows)


def show_schema(conn: sqlite3.Connection, table: str | None = None) -> None:
    if table:
        rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
        print_rows(rows)
        return

    tables = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
    ).fetchall()
    for row in tables:
        table_name = row["name"]
        print(f"\n### {table_name}")
        schema_rows = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
        print_rows(schema_rows)


def dump_rows(conn: sqlite3.Connection, table: str, limit: int = 10) -> None:
    rows = conn.execute(f"SELECT * FROM {table} LIMIT ?", (limit,)).fetchall()
    print_rows(rows)


def list_sessions(conn: sqlite3.Connection, limit: int = 20) -> None:
    rows = conn.execute(
        """
        SELECT session_id, session_type, agent_id, team_id, user_id, created_at, updated_at
        FROM agno_sessions
        ORDER BY updated_at DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    print_rows(rows)


def show_session(conn: sqlite3.Connection, session_id: str) -> None:
    row = conn.execute(
        "SELECT * FROM agno_sessions WHERE session_id = ?",
        (session_id,),
    ).fetchone()
    if row is None:
        print(f"No session found for '{session_id}'")
        return

    decoded = {key: decode_jsonish(row[key]) for key in row.keys()}
    print("### Session Row")
    print(json.dumps(decoded, indent=2, default=str))


def show_session_runs(conn: sqlite3.Connection, session_id: str) -> None:
    payload = load_session_runs(conn, session_id)
    if payload is None:
        return
    print(json.dumps(payload, indent=2, default=str))


def load_session_runs(conn: sqlite3.Connection, session_id: str) -> list[dict[str, Any]] | None:
    row = conn.execute(
        "SELECT * FROM agno_sessions WHERE session_id = ?",
        (session_id,),
    ).fetchone()
    if row is None:
        print(f"No session found for '{session_id}'")
        return None

    session_payload = row["runs"] if "runs" in row.keys() else None
    if session_payload is None:
        print("Session row found, but no runs column is available.")
        return None

    try:
        payload = decode_jsonish(session_payload)
    except Exception:
        print(session_payload)
        return None

    if not isinstance(payload, list):
        print("Runs payload is not a list.")
        return None

    return payload


def show_trace(conn: sqlite3.Connection, session_id: str) -> None:
    payload = load_session_runs(conn, session_id)
    if payload is None:
        return

    columns = [
        "run_index",
        "kind",
        "agent_name",
        "agent_id",
        "run_id",
        "parent_run_id",
        "status",
        "role",
        "name",
        "details",
        "message_index",
        "tool_index",
    ]
    trace_rows: list[dict[str, Any]] = []
    for run_index, run in enumerate(payload, start=1):
        trace_rows.append(
            {
                "run_index": run_index,
                "kind": "run",
                "agent_name": run.get("agent_name"),
                "agent_id": run.get("agent_id"),
                "run_id": run.get("run_id"),
                "parent_run_id": run.get("parent_run_id"),
                "status": run.get("status"),
                "role": "assistant",
                "name": "run_response",
                "details": run.get("content") or run.get("reasoning_content") or "",
                "message_index": None,
                "tool_index": None,
            }
        )
        for message_index, message in enumerate(run.get("messages", []) or [], start=1):
            trace_rows.append(
                {
                    "run_index": run_index,
                    "kind": "message",
                    "agent_name": run.get("agent_name"),
                    "agent_id": run.get("agent_id"),
                    "run_id": run.get("run_id"),
                    "parent_run_id": run.get("parent_run_id"),
                    "status": run.get("status"),
                    "role": message.get("role"),
                    "name": message.get("tool_name") or message.get("role"),
                    "details": message.get("content")
                    or message.get("reasoning_content")
                    or json.dumps(message.get("tool_calls", []), default=str),
                    "message_index": message_index,
                    "tool_index": None,
                }
            )
        for tool_index, tool in enumerate(run.get("tools", []) or [], start=1):
            trace_rows.append(
                {
                    "run_index": run_index,
                    "kind": "tool",
                    "agent_name": run.get("agent_name"),
                    "agent_id": run.get("agent_id"),
                    "run_id": run.get("run_id"),
                    "parent_run_id": run.get("parent_run_id"),
                    "status": run.get("status"),
                    "role": "tool",
                    "name": tool.get("tool_name"),
                    "details": json.dumps(
                        {
                            "tool_args": tool.get("tool_args"),
                            "result": tool.get("result"),
                            "tool_call_error": tool.get("tool_call_error"),
                            "tool_call_id": tool.get("tool_call_id"),
                        },
                        default=str,
                    ),
                    "message_index": None,
                    "tool_index": tool_index,
                }
            )

    print_rows([{column: row.get(column) for column in columns} for row in trace_rows])


def show_help_examples() -> None:
    print(
        f"""Examples:
  python section_5/db_search.py tables
  python section_5/db_search.py schema
  python section_5/db_search.py schema agno_sessions
  python section_5/db_search.py rows agno_sessions --limit 5
  python section_5/db_search.py sessions --limit 10
  python section_5/db_search.py session personal-assistant-team-demo
"""
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Inspect the team SQLite database.")
    parser.add_argument("--db", type=Path, default=DB_PATH, help="Path to the SQLite database file.")

    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("tables", help="List database tables.")

    schema_parser = subparsers.add_parser("schema", help="Show schema for one table or all tables.")
    schema_parser.add_argument("table", nargs="?", help="Optional table name.")

    rows_parser = subparsers.add_parser("rows", help="Dump rows from a table.")
    rows_parser.add_argument("table", help="Table name.")
    rows_parser.add_argument("--limit", type=int, default=10, help="Maximum number of rows to show.")

    sessions_parser = subparsers.add_parser("sessions", help="List team sessions.")
    sessions_parser.add_argument("--limit", type=int, default=20, help="Maximum number of sessions to show.")

    session_parser = subparsers.add_parser("session", help="Show one session row by id.")
    session_parser.add_argument("session_id", help="Session id to inspect.")

    runs_parser = subparsers.add_parser("runs", help="Show the JSON payload for one session.")
    runs_parser.add_argument("session_id", help="Session id to inspect.")

    trace_parser = subparsers.add_parser("trace", help="Show a flattened timeline of runs, messages, and tool calls.")
    trace_parser.add_argument("session_id", help="Session id to inspect.")

    subparsers.add_parser("help-examples", help="Print command examples.")

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "help-examples":
        show_help_examples()
        return

    if not args.db.exists():
        raise SystemExit(f"Database file not found: {args.db}")

    with connect(args.db) as conn:
        if args.command == "tables":
            show_tables(conn)
        elif args.command == "schema":
            show_schema(conn, getattr(args, "table", None))
        elif args.command == "rows":
            dump_rows(conn, args.table, args.limit)
        elif args.command == "sessions":
            list_sessions(conn, args.limit)
        elif args.command == "session":
            show_session(conn, args.session_id)
        elif args.command == "runs":
            show_session_runs(conn, args.session_id)
        elif args.command == "trace":
            show_trace(conn, args.session_id)
        else:
            parser.print_help()


if __name__ == "__main__":
    main()

# python section_5/db_search.py tables
# python section_5/db_search.py schema
# python section_5/db_search.py schema agno_sessions
# python section_5/db_search.py rows agno_sessions --limit 5
# python section_5/db_search.py sessions --limit 10
# python section_5/db_search.py session personal-assistant-team-demo
# python section_5/db_search.py runs personal-assistant-team-demo

# python section_5/db_search.py session personal-assistant-team-demo
# python section_5/db_search.py runs personal-assistant-team-demo