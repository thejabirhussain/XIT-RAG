"""
Export entire FreeDB database to a SQL script
This creates a complete SQL dump that can be imported into Supabase or any other database
"""

import os
import mysql.connector
from urllib.parse import quote_plus
from datetime import datetime

# Database connection from .env
host = os.getenv("MYSQL_HOST", "sql.freedb.tech")
port = int(os.getenv("MYSQL_PORT", 3306))
user = os.getenv("MYSQL_USER", "freedb_maryum")
password = os.getenv("MYSQL_PASSWORD", "CWzM8d549E#6WhS")
database = os.getenv("MYSQL_DB", "freedb_RAGPOC2")

def get_connection():
    return mysql.connector.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        database=database
    )

def export_database():
    """Export entire database to SQL script"""
    conn = get_connection()
    cursor = conn.cursor()
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"database_export_{timestamp}.sql"
    
    print(f"Exporting database to {output_file}...")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        # Header
        f.write("-- Database Export\n")
        f.write(f"-- Exported: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"-- Database: {database}\n")
        f.write("-- ================================================\n\n")
        
        # Get all tables
        cursor.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = %s", (database,))
        tables = cursor.fetchall()
        
        if not tables:
            print("No tables found in database!")
            return
        
        print(f"Found {len(tables)} tables")
        
        for (table_name,) in tables:
            print(f"  Exporting table: {table_name}...")
            
            # Get CREATE TABLE statement
            cursor.execute(f"SHOW CREATE TABLE {table_name}")
            create_table = cursor.fetchone()[1]
            f.write(f"\n-- ================================================\n")
            f.write(f"-- Table: {table_name}\n")
            f.write(f"-- ================================================\n")
            f.write(f"DROP TABLE IF EXISTS {table_name};\n")
            f.write(f"{create_table};\n\n")
            
            # Get all data
            cursor.execute(f"SELECT * FROM {table_name}")
            rows = cursor.fetchall()
            
            if rows:
                # Get column names
                cursor.execute(f"DESCRIBE {table_name}")
                columns = [col[0] for col in cursor.fetchall()]
                col_names = ", ".join([f"`{col}`" for col in columns])
                
                # Insert statements
                f.write(f"-- Data for table {table_name}\n")
                for row in rows:
                    values = []
                    for val in row:
                        if val is None:
                            values.append("NULL")
                        elif isinstance(val, str):
                            # Escape single quotes
                            escaped = val.replace("'", "''")
                            values.append(f"'{escaped}'")
                        elif isinstance(val, (int, float)):
                            values.append(str(val))
                        elif isinstance(val, bytes):
                            values.append(f"0x{val.hex()}")
                        else:
                            values.append(f"'{str(val)}'")
                    
                    values_str = ", ".join(values)
                    f.write(f"INSERT INTO {table_name} ({col_names}) VALUES ({values_str});\n")
                
                f.write("\n")
            else:
                f.write(f"-- Table {table_name} is empty\n\n")
        
        f.write("-- ================================================\n")
        f.write("-- Export Complete\n")
        f.write("-- ================================================\n")
    
    cursor.close()
    conn.close()
    
    print(f"\n✓ Database exported successfully to {output_file}")
    print(f"File size: {os.path.getsize(output_file) / 1024:.2f} KB")
    print(f"\nYou can now:")
    print(f"1. Import this into Supabase via the SQL editor")
    print(f"2. Or use: psql -h <supabase-host> -U postgres -d postgres -f {output_file}")

if __name__ == "__main__":
    try:
        export_database()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
