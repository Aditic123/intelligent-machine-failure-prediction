
import sqlite3

conn = sqlite3.connect("../machine_history.db")

print("TOTAL PREDICTIONS:")
print(
    conn.execute(
        "SELECT COUNT(*) FROM predictions"
    ).fetchone()[0]
)

print("\nLATEST PREDICTION:")

result = conn.execute("""
    SELECT
        machine_id,
        timestamp,
        machine_type,
        prediction,
        failure_probability
    FROM predictions
    ORDER BY id DESC
    LIMIT 1
""").fetchone()

print(result)

conn.close()
