import logging
import pymysql
import os
import sqlglot
import sqlglot.expressions as exp
import time

logger = logging.getLogger(__name__)
MAX_ROWS = 50

class DatabaseService:
    def __init__(self):
        self.host = os.getenv("MYSQL_HOST", "sql.freedb.tech")
        self.port = int(os.getenv("MYSQL_PORT", 3306))
        self.user = os.getenv("MYSQL_USER", "freedb_maryum")
        self.password = os.getenv("MYSQL_PASSWORD", "CWzM8d549E#6WhS")
        self.database = os.getenv("MYSQL_DB", "freedb_RAGPOC2")

    def get_connection(self):
        return pymysql.connect(
            host=self.host,
            user=self.user,
            password=self.password,
            database=self.database,
            port=self.port,
            cursorclass=pymysql.cursors.DictCursor,
            connect_timeout=10
        )

    def _validate_sql(self, query: str) -> str | None:
        stripped = query.strip().rstrip(";")
        if not stripped:
            return "Empty query."
        try:
            statements = sqlglot.parse(stripped, dialect="mysql")
        except sqlglot.errors.ParseError as e:
            return f"Invalid SQL syntax: {e}"

        if len(statements) != 1:
            return "Only a single statement is allowed."

        stmt = statements[0]

        if not isinstance(stmt, exp.Select):
            return f"Only SELECT is permitted. Got: {type(stmt).__name__}."

        _candidates = [
            "Insert", "Update", "Delete", "Drop", "Alter", "Create",
            "Rename", "RenameTable", "AlterTable",
            "TruncateTable", "Truncate",
            "Grant", "Revoke",
            "Command", "Use",
        ]
        FORBIDDEN_NODES = tuple(
            getattr(exp, name) for name in _candidates if hasattr(exp, name)
        )
        for node in stmt.walk():
            if isinstance(node, FORBIDDEN_NODES):
                return f"Forbidden operation in query: {type(node).__name__}."

        for table in stmt.find_all(exp.Table):
            if (table.db or "").lower() == "information_schema":
                return "Access to information_schema is not permitted."

        return None

    def execute_query(self, query: str) -> dict:
        error = self._validate_sql(query)
        if error:
            logger.warning("Blocked SQL | Reason: %s | Query: %s", error, query[:200])
            return {"error": error}

        safe_query = query.strip().rstrip(";")
        if "LIMIT" not in safe_query.upper():
            safe_query = f"{safe_query} LIMIT {MAX_ROWS}"

        try:
            with self.get_connection() as connection:
                with connection.cursor() as cursor:
                    t = time.perf_counter()
                    cursor.execute(safe_query)
                    rows = cursor.fetchmany(MAX_ROWS)
                    logger.info("db.execute | rows_returned=%d | %.1fms", len(rows), (time.perf_counter() - t) * 1000)
                    return {"results": rows}
        except pymysql.err.ProgrammingError as e:
            logger.error("SQL execution error: %s", e)
            return {"error": "Query execution failed."}
        except Exception as e:
            logger.error("DB error: %s", e)
            return {"error": "A database error occurred."}

