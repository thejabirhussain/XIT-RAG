import logging
import os
import time
import sqlglot
import sqlglot.expressions as exp
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from urllib.parse import quote_plus

logger = logging.getLogger(__name__)
MAX_ROWS = 50

class DatabaseService:
    def __init__(self):
        self.host = os.getenv("MYSQL_HOST", "sql.freedb.tech")
        self.port = int(os.getenv("MYSQL_PORT", 3306))
        self.user = os.getenv("MYSQL_USER", "freedb_maryum")
        self.password = os.getenv("MYSQL_PASSWORD", "CWzM8d549E#6WhS")
        self.database = os.getenv("MYSQL_DB", "freedb_RAGPOC2")
        
        # Connect to MySQL using PyMySQL driver via SQLAlchemy
        # Ensure password containing special characters is handled correctly by SQLAlchemy url encoding
        safe_password = quote_plus(str(self.password))
        
        self.db_url = f"mysql+pymysql://{self.user}:{safe_password}@{self.host}:{self.port}/{self.database}"
        
        # Connection pool configurations mapped securely
        pool_size = int(os.getenv("DB_POOL_SIZE", "5"))
        max_overflow = int(os.getenv("DB_MAX_OVERFLOW", "10"))
        pool_timeout = int(os.getenv("DB_CONNECTION_TIMEOUT", "30"))

        # Initialize the persistent engine connection pool
        self.engine = create_engine(
            self.db_url,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_timeout=pool_timeout,
            pool_pre_ping=True,  # Verifies connections before using them
            pool_recycle=3600    # Recycle connections every hour
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
            t = time.perf_counter()
            with self.engine.connect() as connection:
                # Use text() to mark safe
                result = connection.execute(text(safe_query))
                
                # Fetch only up to MAX_ROWS (SQLAlchemy allows fetchmany)
                rows_proxy = result.fetchmany(MAX_ROWS)
                # Parse Rows back to dictionaries (mimics pymysql.cursors.DictCursor)
                rows = [dict(row._mapping) for row in rows_proxy]
                
                logger.info("db.execute | rows_returned=%d | %.1fms", len(rows), (time.perf_counter() - t) * 1000)
                return {"results": rows}
                
        except SQLAlchemyError as err:
            logger.error("SQL execution error: %s", err)
            return {"error": "Query execution failed."}
        except Exception as e:
            logger.error("DB error: %s", e)
            return {"error": "A database error occurred."}

