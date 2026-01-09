import sqlite3
import json
import re
from datetime import datetime

DB_PATH = "/Users/mantosh/Desktop/Consumer durable 2/consumer_durable.db"

def format_uuid(uuid_str):
    """Convert 32-char hex to UUID format with hyphens"""
    if uuid_str and len(uuid_str) == 32:
        return f"{uuid_str[:8]}-{uuid_str[8:12]}-{uuid_str[12:16]}-{uuid_str[16:20]}-{uuid_str[20:]}"
    return uuid_str

def escape_string(s):
    """Escape string for SQL"""
    if s is None:
        return "NULL"
    return "'" + str(s).replace("'", "''") + "'"

def format_value(val, col_type=None):
    """Format value for PostgreSQL"""
    if val is None:
        return "NULL"
    if isinstance(val, bool) or val in (0, 1) and col_type == 'bool':
        return "TRUE" if val else "FALSE"
    if isinstance(val, (int, float)):
        return str(val)
    # Check if it looks like a UUID
    val_str = str(val)
    if len(val_str) == 32 and re.match(r'^[a-f0-9]+$', val_str.lower()):
        return f"'{format_uuid(val_str)}'"
    return escape_string(val_str)

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

output = []

# Define tables to migrate with their boolean columns
tables_config = {
    'modules': {'bool_cols': ['is_active']},
    'permissions': {'bool_cols': ['is_active']},
    'roles': {'bool_cols': ['is_system', 'is_active']},
    'regions': {'bool_cols': ['is_active']},
    'users': {'bool_cols': ['is_active', 'is_verified']},
    'user_roles': {'bool_cols': []},
    'role_permissions': {'bool_cols': []},
    'products': {'bool_cols': ['is_active', 'is_serialized', 'requires_installation', 'has_warranty']},
    'categories': {'bool_cols': ['is_active']},
    'brands': {'bool_cols': ['is_active']},
    'warehouses': {'bool_cols': ['is_active']},
    'dealers': {'bool_cols': ['is_active', 'is_verified']},
}

for table, config in tables_config.items():
    try:
        cursor.execute(f"SELECT * FROM {table}")
        rows = cursor.fetchall()
        if rows:
            cols = [desc[0] for desc in cursor.description]
            output.append(f"\n-- {table.upper()} ({len(rows)} rows)")
            output.append(f"DELETE FROM {table};")
            
            for row in rows:
                values = []
                for i, col in enumerate(cols):
                    val = row[i]
                    is_bool = col in config['bool_cols']
                    if is_bool and val in (0, 1):
                        values.append("TRUE" if val else "FALSE")
                    else:
                        values.append(format_value(val))
                output.append(f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({', '.join(values)});")
    except Exception as e:
        output.append(f"-- Skipping {table}: {e}")

conn.close()

# Write to file
with open("/Users/mantosh/Desktop/Consumer durable 2/supabase_migration.sql", "w") as f:
    f.write("-- Migration from SQLite to Supabase PostgreSQL\n")
    f.write("-- Generated: " + datetime.now().isoformat() + "\n")
    f.write("\n".join(output))

print("Migration SQL generated: supabase_migration.sql")
print(f"Total statements: {len([l for l in output if l.startswith('INSERT')])}")
