"""
Add minutes column to games table
"""
import sqlite3

# Connect to database
conn = sqlite3.connect('statscout.db')
cursor = conn.cursor()

# Check if column already exists
cursor.execute("PRAGMA table_info(games)")
columns = [col[1] for col in cursor.fetchall()]

if 'minutes' not in columns:
    print("Adding 'minutes' column to games table...")
    cursor.execute("ALTER TABLE games ADD COLUMN minutes REAL")
    conn.commit()
    print("Column added successfully!")
else:
    print("'minutes' column already exists in games table")

conn.close()
print("\nMigration complete!")
