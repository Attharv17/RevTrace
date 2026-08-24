"""
Database module — Phase 1 stub.

Full async SQLAlchemy engine is configured here but disabled until
a PostgreSQL C driver is available (asyncpg or psycopg2-binary).

To enable:
  1. Install PostgreSQL locally (ships pg_config)
  2. pip install asyncpg  OR  pip install psycopg2-binary
  3. Uncomment the engine block below
  4. Set DATABASE_URL in backend/.env
"""
import socket


def ping_db_tcp(host: str = "localhost", port: int = 5432, timeout: float = 2.0) -> bool:
    """
    Lightweight TCP connectivity check for PostgreSQL.
    Works without any C extension driver — just checks if the port is open.
    Phase 2 will replace this with a proper SQL-level ping.
    """
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (OSError, ConnectionRefusedError):
        return False


async def ping_db() -> bool:
    """Async-compatible wrapper around the TCP ping."""
    from app.core.config import get_settings
    settings = get_settings()

    # Parse host/port from DATABASE_URL
    # e.g. postgresql+asyncpg://ledger:ledger@localhost:5432/ledgerpilot
    try:
        url = settings.database_url
        after_at = url.split("@")[-1]   # localhost:5432/ledgerpilot
        host_port = after_at.split("/")[0]
        if ":" in host_port:
            host, port_str = host_port.split(":")
            port = int(port_str)
        else:
            host, port = host_port, 5432
        return ping_db_tcp(host, port)
    except Exception:
        return False
