from pathlib import Path
from agno.db.sqlite import SqliteDb

SCAR_SESSION_ID  = "scar-analysis-session"
SCAR_DB_PATH     = Path(__file__).resolve().parent / "scar_sessions.db"


def create_scar_session_db() -> SqliteDb:
    SCAR_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return SqliteDb(db_file=str(SCAR_DB_PATH))
