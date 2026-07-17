import os
import sys
sys.path.append(os.path.join(os.getcwd(), 'backend'))
from app.core.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
try:
    # Test the regex query
    query = text("SELECT 'Data Analyst' ~* '\\ydata\\s+analyst\\y'")
    result = db.execute(query).scalar()
    print("Regex test result:", result)
except Exception as e:
    print("Error:", e)
