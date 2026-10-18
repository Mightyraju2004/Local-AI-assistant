import sqlite3

conn = sqlite3.connect("tasks.db")
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()

print("Tables:", tables)

for table in tables:
    name = table[0]
    print(f"\nData in {name}:")
    cursor.execute(f'SELECT * FROM "{name}"')
    print(cursor.fetchall())

conn.close()