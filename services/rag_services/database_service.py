import pymysql
import os

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

    def execute_query(self, query: str) -> dict:
        """
        Executes a SELECT query safely. Returns a dict containing either 'results' (rows) or 'error'.
        """
        if not query.strip():
            return {"error": "Empty query provided"}
            
        try:
            with self.get_connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(query)
                    rows = cursor.fetchall()
                    return {"results": rows}
        except Exception as e:
            return {"error": str(e)}
