#!/usr/bin/env python3
"""
Job Scout - Performance Benchmarking Tool
-----------------------------------------
This script validates the performance claims made in the project report.
It generates a mock dataset of 10,000 job embeddings and compares the 
query latency of sequential scans vs. HNSW-indexed vector searches.

Usage: 
    docker compose exec backend python scripts/benchmark_pgvector.py
"""

import time
import random
import os
from sqlalchemy import create_engine, text

# Fallback to localhost if not running inside docker
DB_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@db:5432/job_scout")
try:
    engine = create_engine(DB_URL)
    engine.connect()
except:
    # If running from host machine instead of inside the docker container
    DB_URL = "postgresql://postgres:postgres@localhost:5432/job_scout"
    engine = create_engine(DB_URL)

VECTOR_DIM = 384
NUM_ROWS = 10000
NUM_QUERIES = 50

def generate_random_vector():
    """Generates a random 384-dimensional vector to simulate all-MiniLM-L6-v2 embeddings."""
    return f"[{','.join(str(random.uniform(-1, 1)) for _ in range(VECTOR_DIM))}]"

def run_benchmark():
    with engine.connect() as conn:
        print("=" * 60)
        print(f"🚀 JOB SCOUT: PGVECTOR HNSW BENCHMARK")
        print("=" * 60)
        
        # 1. Setup Benchmark Table
        print(f"[*] Creating benchmark table with {NUM_ROWS} mock jobs...")
        conn.execute(text("DROP TABLE IF EXISTS benchmark_jobs;"))
        conn.execute(text("""
            CREATE TABLE benchmark_jobs (
                id SERIAL PRIMARY KEY,
                embedding vector(384)
            );
        """))
        conn.commit()

        # 2. Insert 10,000 Mock Embeddings
        print("[*] Generating and inserting random vector embeddings (this takes a moment)...")
        # Batch insert for speed
        batch_size = 1000
        for i in range(0, NUM_ROWS, batch_size):
            values = []
            for _ in range(batch_size):
                values.append(f"('{generate_random_vector()}')")
            
            insert_query = f"INSERT INTO benchmark_jobs (embedding) VALUES {','.join(values)};"
            conn.execute(text(insert_query))
        conn.commit()
        print(f"[+] Successfully inserted {NUM_ROWS} rows.")

        # 3. Test Sequential Scan (No Index)
        print("\n[*] Running baseline queries (Sequential Scan / No Index)...")
        seq_times = []
        for _ in range(NUM_QUERIES):
            target_vector = generate_random_vector()
            start_time = time.perf_counter()
            conn.execute(text(f"""
                SELECT id FROM benchmark_jobs 
                ORDER BY embedding <=> '{target_vector}' LIMIT 10;
            """))
            seq_times.append((time.perf_counter() - start_time) * 1000)
            
        avg_seq_time = sum(seq_times) / len(seq_times)
        print(f"[!] Baseline Average Latency: {avg_seq_time:.2f} ms")

        # 4. Create HNSW Index
        print("\n[*] Building HNSW (Hierarchical Navigable Small World) Index...")
        start_index_time = time.perf_counter()
        conn.execute(text("""
            CREATE INDEX idx_benchmark_hnsw ON benchmark_jobs 
            USING hnsw (embedding vector_cosine_ops);
        """))
        conn.commit()
        index_build_time = (time.perf_counter() - start_index_time)
        print(f"[+] Index built in {index_build_time:.2f} seconds.")

        # 5. Test Indexed Scan
        print("\n[*] Running optimized queries (HNSW Index Active)...")
        # Turn off sequential scans to force index usage for testing
        conn.execute(text("SET enable_seqscan = off;"))
        
        idx_times = []
        for _ in range(NUM_QUERIES):
            target_vector = generate_random_vector()
            start_time = time.perf_counter()
            conn.execute(text(f"""
                SELECT id FROM benchmark_jobs 
                ORDER BY embedding <=> '{target_vector}' LIMIT 10;
            """))
            idx_times.append((time.perf_counter() - start_time) * 1000)

        avg_idx_time = sum(idx_times) / len(idx_times)
        print(f"[!] HNSW Average Latency: {avg_idx_time:.2f} ms")
        
        conn.execute(text("SET enable_seqscan = on;")) # Reset

        # 6. Summary
        print("\n" + "=" * 60)
        print("📊 BENCHMARK RESULTS SUMMARY")
        print("=" * 60)
        print(f"Dataset Size       : {NUM_ROWS} job embeddings")
        print(f"Vector Dimensions  : {VECTOR_DIM} (all-MiniLM-L6-v2)")
        print(f"Sequential Latency : {avg_seq_time:.2f} ms")
        print(f"HNSW Latency       : {avg_idx_time:.2f} ms")
        print(f"Performance Gain   : {avg_seq_time / avg_idx_time:.1f}x faster")
        print("=" * 60)

        # Cleanup
        conn.execute(text("DROP TABLE benchmark_jobs;"))
        conn.commit()

if __name__ == "__main__":
    run_benchmark()
