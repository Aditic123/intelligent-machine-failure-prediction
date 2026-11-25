import sqlite3

conn = sqlite3.connect("../machine_history.db")

print("TABLES:")
print(conn.execute(
    "SELECT name FROM sqlite_master WHERE type='table'"
).fetchall())

print("\nPREDICTIONS COLUMNS:")
print(conn.execute(
    "PRAGMA table_info(predictions)"
).fetchall())

print("\nTOTAL RECORDS:")
print(conn.execute(
    "SELECT COUNT(*) FROM predictions"
).fetchone()[0])

conn.close()