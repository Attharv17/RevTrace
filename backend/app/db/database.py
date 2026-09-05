"""
RevTrace — Database utilities.
ping_db() runs a lightweight SELECT 1 to verify connectivity.
"""
import socket
from sqlalchemy import text
from app.db.session import engine


async def ping_db() -> bool:
    """Check database connection using a lightweight query."""
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
