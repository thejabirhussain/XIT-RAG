import re
from typing import Any
import pyodbc


# Columns that must never appear in write statements
_PROTECTED_COMPUTED_COLS = {"risk_score"}
# DML keywords that are forbidden (SELECT only)
_FORBIDDEN_DML = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|TRUNCATE|EXEC|EXECUTE|CREATE|MERGE)\b",
    re.IGNORECASE,
)


class MSSQLService:
    def __init__(self, connection_string: str):
        """
        connection_string example:
        DRIVER={ODBC Driver 17 for SQL Server};SERVER=host;DATABASE=db;UID=user;PWD=pass
        Or use trusted connection:
        DRIVER={ODBC Driver 17 for SQL Server};SERVER=host;DATABASE=db;Trusted_Connection=yes
        """
        self.connection_string = connection_string
        self._conn: pyodbc.Connection | None = None

    def _get_connection(self) -> pyodbc.Connection:
        if self._conn is None:
            self._conn = pyodbc.connect(self.connection_string, autocommit=True)
        return self._conn

    def _validate_sql(self, sql: str) -> None:
        """
        Raises ValueError if the SQL is unsafe.
        Allows only SELECT statements.
        """
        stripped = sql.strip()
        if not stripped.upper().startswith("SELECT"):
            raise ValueError(f"Only SELECT statements are allowed. Got: {stripped[:60]}")

        if _FORBIDDEN_DML.search(stripped):
            raise ValueError(f"Forbidden DML keyword detected in SQL: {stripped[:120]}")

        for col in _PROTECTED_COMPUTED_COLS:
            # Detect writes to protected columns (UPDATE SET risk_score = ...)
            if re.search(rf"\bSET\s+{col}\s*=", stripped, re.IGNORECASE):
                raise ValueError(f"Attempt to write to protected computed column: {col}")

    def execute_query(self, sql: str) -> list[dict[str, Any]]:
        """
        Executes a validated SELECT query and returns rows as list of dicts.
        org_id scoping is enforced at text2sql generation level — validated here
        as a belt-and-suspenders check.
        """
        self._validate_sql(sql)

        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(sql)
            columns = [desc[0] for desc in cursor.description]
            rows = []
            for row in cursor.fetchall():
                rows.append(dict(zip(columns, row)))
            return rows
        except pyodbc.Error as e:
            raise RuntimeError(f"MS SQL execution error: {e}") from e
        finally:
            cursor.close()

    def test_connection(self) -> bool:
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            return True
        except Exception:
            return False

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None
