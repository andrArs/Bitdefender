from pathlib import Path

from agno.db.sqlite import SqliteDb

TEAM_SESSION_ID = "personal-assistant-team-demo"
TEAM_SESSION_DB_PATH = Path(__file__).resolve().parent / "team_sessions.db"


def create_team_session_db() -> SqliteDb:
    TEAM_SESSION_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return SqliteDb(db_file=str(TEAM_SESSION_DB_PATH))
