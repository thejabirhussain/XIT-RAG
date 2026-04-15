import logging
import os
import time
import re
import sqlglot
import sqlglot.expressions as exp
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)
MAX_ROWS = 50
FORBIDDEN_KEYWORDS = [
    "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE",
    "TRUNCATE", "RENAME", "GRANT", "REVOKE", "USE",
    "EXEC", "EXECUTE", "CALL", "MERGE", "REPLACE",
    "LOAD", "HANDLER", "LOCK", "UNLOCK",
]

class DatabaseService:
    def __init__(self):
        # Use DATABASE_URL for Supabase PostgreSQL connection
        self.db_url = os.getenv("DATABASE_URL")
        
        if not self.db_url:
            raise ValueError("DATABASE_URL environment variable not set. Please configure Supabase connection.")
        
        # Connection pool configurations
        pool_size = int(os.getenv("DB_POOL_SIZE", "5"))
        max_overflow = int(os.getenv("DB_MAX_OVERFLOW", "10"))
        pool_timeout = int(os.getenv("DB_CONNECTION_TIMEOUT", "30"))

        # Initialize the persistent engine connection pool for PostgreSQL
        self.engine = create_engine(
            self.db_url,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_timeout=pool_timeout,
            pool_pre_ping=True,  # Verifies connections before using them
            pool_recycle=1800    # Recycle connections every hour
        )
        
        logger.info("DatabaseService initialized with Supabase PostgreSQL")

    def _validate_sql(self, query: str) -> str | None:
        stripped = query.strip().rstrip(";")
        
        if not stripped:
            return "Empty query."
    
        # Strip inline comments (-- ...) and block comments (/* ... */)
        cleaned = re.sub(r"--[^\n]*", " ", stripped)
        cleaned = re.sub(r"/\*.*?\*/", " ", cleaned, flags=re.DOTALL)
        normalized = " ".join(cleaned.split()).upper()
    
        # Must start with SELECT or WITH (CTEs)
        if not (normalized.startswith("SELECT") or normalized.startswith("WITH")):
            return f"Only SELECT is permitted."
    
        # Block forbidden keywords as whole words
        for kw in FORBIDDEN_KEYWORDS:
            if re.search(rf"\b{kw}\b", normalized):
                return f"Forbidden keyword in query: {kw}."

        # Block multiple statements
        if ";" in stripped:
            return "Only a single statement is allowed."

        # Block information_schema access
        if "INFORMATION_SCHEMA" in normalized:
            return "Access to information_schema is not permitted."

        return None

    def execute_query(self, query: str) -> dict:
        error = self._validate_sql(query)
        if error:
            logger.warning("Blocked SQL | Reason: %s | Query: %s", error, query[:200])
            return {"error": "I couldn't process this query safely. Could you please clarify or rephrase what you're looking for?"}

        safe_query = query.strip().rstrip(";")
        if "LIMIT" not in safe_query.upper():
            safe_query = f"{safe_query} LIMIT {MAX_ROWS}"

        try:
            t = time.perf_counter()
            with self.engine.connect() as connection:
                result = connection.execute(text(safe_query))
                rows = [dict(row) for row in result.mappings().fetchmany(MAX_ROWS)]
                
                elapsed = (time.perf_counter() - t) * 1000
                logger.info("db.execute | rows_returned=%d | %.1fms", len(rows), elapsed)
                return {"results": rows}
                
        except SQLAlchemyError as err:
            logger.error("SQL execution error: %s", err)
            return {"error": "I encountered an issue processing that request. Could you please clarify your query?"}
        except Exception as e:
            logger.error("DB error: %s", e)
            return {"error": "An unexpected issue occurred while retrieving data. Could you please clarify your query?"}
