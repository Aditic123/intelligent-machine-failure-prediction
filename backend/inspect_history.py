import sqlite3

conn = sqlite3.connect("../machine_history.db")

records = conn.execute("""
    SELECT
        id,
        machine_id,
        timestamp,
        machine_type,
        prediction,
        failure_probability
    FROM predictions
    ORDER BY id DESC
    LIMIT 6
""").fetchall()

for record in records:
    print(record)

conn.close()