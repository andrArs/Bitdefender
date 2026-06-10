from pathlib import Path

from agno.db.sqlite import SqliteDb

GYM_SESSION_ID = "gym-buddy-demo"
GYM_SESSION_DB_PATH = Path(__file__).resolve().parent / "gym_sessions.db"


def create_gym_session_db() -> SqliteDb:
    GYM_SESSION_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return SqliteDb(db_file=str(GYM_SESSION_DB_PATH))
