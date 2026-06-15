import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine("postgresql://user:password@localhost:5432/jobscout")
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()
res = db.execute("SELECT id, description, experience_required FROM jobs LIMIT 1").fetchone()
print(res)
