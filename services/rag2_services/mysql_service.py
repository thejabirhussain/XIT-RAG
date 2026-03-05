import re
import logging
from typing import Any

import mysql.connector
from mysql.connector import Error as MySQLError

logger = logging.getLogger(__name__)

_FORBIDDEN_DML = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|TRUNCATE|EXEC|EXECUTE|CREATE|MERGE)\b",
    re.IGNORECASE,
)
_PROTECTED_COMPUTED_COLS = {"risk_score"}


class MySQLService:  # keeping class name so no other imports break
    def __init__(
        self,
        host: str,
        port: int,
        user: str,
        password: str,
        database: str,
    ):
        self.host     = host
        self.port     = port
        self.user     = user
        self.password = password
        self.database = database
        self._conn: mysql.connector.MySQLConnection | None = None

    def _get_connection(self):
        if self._conn is None or not self._conn.is_connected():
            self._conn = mysql.connector.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database,
                connection_timeout=10,
            )
            logger.info(f"[MySQLService] Connected to {self.host}:{self.port}/{self.database}")
        return self._conn

    def _validate_sql(self, sql: str) -> None:
        stripped = sql.strip()
        if not stripped.upper().startswith("SELECT"):
            raise ValueError(f"Only SELECT statements allowed. Got: {stripped[:60]}")
        if _FORBIDDEN_DML.search(stripped):
            raise ValueError(f"Forbidden DML keyword in SQL: {stripped[:120]}")
        for col in _PROTECTED_COMPUTED_COLS:
            if re.search(rf"\bSET\s+{col}\s*=", stripped, re.IGNORECASE):
                raise ValueError(f"Attempt to write to computed column: {col}")

    def execute_query(self, sql: str) -> list[dict[str, Any]]:
        self._validate_sql(sql)
        conn = self._get_connection()
        cursor = conn.cursor(dictionary=True)  # dictionary=True → returns list of dicts directly
        try:
            cursor.execute(sql)
            rows = cursor.fetchall()
            return rows
        except MySQLError as e:
            raise RuntimeError(f"MySQL execution error: {e}") from e
        finally:
            cursor.close()

    def test_connection(self) -> bool:
        try:
            conn = self._get_connection()
            return conn.is_connected()
        except Exception:
            return False

    def close(self):
        if self._conn and self._conn.is_connected():
            self._conn.close()
            self._conn = None
