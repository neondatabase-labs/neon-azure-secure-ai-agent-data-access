import psycopg2
from psycopg2.extras import execute_values
import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Load your Neon Postgres connection string from an environment variable
# Example format: postgres://username:password@host/dbname
DATABASE_URL = os.getenv("NEON_DB_CONNECTION_STRING")

# Connect to Neon PostgreSQL
conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()

# Drop the finance table if it exists
cursor.execute("DROP TABLE IF EXISTS finance")

# Create the finance table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS finance (
        id SERIAL PRIMARY KEY,
        company TEXT,
        revenue REAL,
        profit REAL,
        stock_price REAL,
        user_role TEXT
    )
''')

# Insert 10 sample records
financial_data = [
    ('IBM', 75000, 5000, 145.32, 'restricted'),
    ('Apple', 394000, 99900, 179.95, 'restricted'),
    ('Microsoft', 211000, 72000, 314.10, 'restricted'),
    ('Google', 280000, 76000, 2801.12, 'restricted'),
    ('Amazon', 502000, 33000, 142.92, 'restricted'),
    ('Meta', 117000, 39000, 302.56, 'restricted'),
    ('Tesla', 123000, 15500, 199.35, 'public'),
    ('Netflix', 35000, 5400, 412.75, 'public'),
    ('Nvidia', 26000, 9600, 450.99, 'public'),
    ('Samsung', 244000, 41000, 70.10, 'public')
]

# Insert records using `execute_values` for efficiency
execute_values(
    cursor,
    "INSERT INTO finance (company, revenue, profit, stock_price, user_role) VALUES %s",
    financial_data
)

conn.commit()

# Read and print all records
cursor.execute("SELECT * FROM finance")
rows = cursor.fetchall()

for row in rows:
    print(row)

cursor.close()
conn.close()

print("✅ Neon Postgres database is set up with 10 records!")
