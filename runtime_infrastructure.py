import os
import sqlite3
from functools import lru_cache
from typing import Any, Dict, Optional


DEFAULT_SQLITE_PATH = r'C:\backend\zwesta_trading.db'
KNOWN_VPS_SQLITE_PATH = r'C:\zwesta-trader\Zwesta Flutter App\zwesta_trading.db'


def _default_sqlite_candidates() -> list[str]:
    module_dir = os.path.dirname(os.path.abspath(__file__))
    return [
        KNOWN_VPS_SQLITE_PATH,
        os.path.join(module_dir, 'zwesta_trading.db'),
        DEFAULT_SQLITE_PATH,
    ]


def _load_local_dotenv() -> None:
    try:
        from dotenv import load_dotenv

        env_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
        if os.path.exists(env_file):
            load_dotenv(env_file)
    except ImportError:
        pass


_load_local_dotenv()


def get_database_backend() -> str:
    backend = os.getenv('DATABASE_BACKEND', 'sqlite').strip().lower()
    return backend if backend in {'sqlite', 'postgres'} else 'sqlite'


def get_database_path() -> str:
    configured_path = os.getenv('DATABASE_PATH', '').strip()
    if configured_path:
        return configured_path

    for candidate in _default_sqlite_candidates():
        if candidate and os.path.exists(candidate):
            return candidate

    return _default_sqlite_candidates()[0]


def get_database_url() -> str:
    return os.getenv('DATABASE_URL', '').strip()


def using_postgres() -> bool:
    backend = get_database_backend()
    database_url = get_database_url().lower()
    return backend == 'postgres' or database_url.startswith(('postgresql://', 'postgres://'))


def build_sqlite_connection(
    timeout: float = 30.0,
    *,
    database_path: Optional[str] = None,
    row_factory: bool = False,
    busy_timeout_ms: Optional[int] = None,
    wal: bool = True,
) -> sqlite3.Connection:
    conn = sqlite3.connect(database_path or get_database_path(), timeout=timeout, check_same_thread=False)
    if row_factory:
        conn.row_factory = sqlite3.Row
    if busy_timeout_ms is None:
        busy_timeout_ms = int(os.getenv('SQLITE_BUSY_TIMEOUT_MS', '60000'))
    if busy_timeout_ms is not None:
        conn.execute(f'PRAGMA busy_timeout = {int(busy_timeout_ms)}')
    if wal:
        conn.execute('PRAGMA journal_mode=WAL')
        conn.execute('PRAGMA synchronous=NORMAL')
    return conn


@lru_cache(maxsize=4)
def _get_sqlalchemy_engine(database_url: str):
    if not database_url:
        return None

    try:
        from sqlalchemy import create_engine

        return create_engine(database_url, future=True, pool_pre_ping=True)
    except Exception:
        return None


def get_sqlalchemy_engine(database_url: Optional[str] = None):
    return _get_sqlalchemy_engine((database_url or get_database_url()).strip())


@lru_cache(maxsize=1)
def get_redis_client():
    redis_url = os.getenv('REDIS_URL', '').strip()
    if not redis_url:
        return None

    try:
        import redis

        return redis.from_url(redis_url, decode_responses=True)
    except Exception:
        return None


def get_runtime_infrastructure_summary() -> Dict[str, Any]:
    return {
        'database_backend': get_database_backend(),
        'database_path': get_database_path(),
        'database_url_configured': bool(get_database_url()),
        'postgres_mode': using_postgres(),
        'sqlalchemy_ready': get_sqlalchemy_engine() is not None,
        'redis_url_configured': bool(os.getenv('REDIS_URL', '').strip()),
        'redis_ready': get_redis_client() is not None,
    }