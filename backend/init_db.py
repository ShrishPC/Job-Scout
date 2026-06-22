from app.core.database import engine
from app.models.models import Base
from sqlalchemy import text

def init_db():
    print("Initializing database...")
    try:
        # Create pgvector extension if it doesn't exist
        with engine.connect() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            conn.commit()
        
        # Create tables
        Base.metadata.create_all(bind=engine)
        
        # Check and dynamically add workplace_type column if it's missing (auto-migration)
        with engine.connect() as conn:
            check_col_query = text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='jobs' AND column_name='workplace_type';
            """)
            col_exists = conn.execute(check_col_query).fetchone()
            if not col_exists:
                print("Adding 'workplace_type' column to 'jobs' table...")
                conn.execute(text("ALTER TABLE jobs ADD COLUMN workplace_type VARCHAR DEFAULT 'unspecified';"))
                conn.commit()
                print("Column 'workplace_type' added successfully.")
        
        # Create HNSW index for vector cosine distance optimization
        with engine.connect() as conn:
            print("Checking/Creating HNSW index on jobs.embedding column...")
            conn.execute(text("CREATE INDEX IF NOT EXISTS jobs_embedding_hnsw_idx ON jobs USING hnsw (embedding vector_cosine_ops);"))
            conn.commit()
            print("HNSW index initialized successfully.")
                
        print("Database initialized successfully.")
    except Exception as e:
        print(f"Error initializing database: {e}")
        print("Make sure PostgreSQL with pgvector is running.")


if __name__ == "__main__":
    init_db()
