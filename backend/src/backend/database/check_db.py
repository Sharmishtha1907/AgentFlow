from sqlalchemy import text
from backend.database.session import engine

try:
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))
        print("Database connected successfully!")
        print("Result:", result.scalar())

except Exception as e:
    print("Database connection failed:", e)

finally:
    engine.dispose()