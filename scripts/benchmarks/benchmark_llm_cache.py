#!/usr/bin/env python3
"""
LLM Cache Latency Benchmark (Dual Mode)
Measures Cold generation time vs AIGenerationCache response time
across 5 repetitions on CPU for both Demo Mode and Full Local Llama-3.2-3B.
"""

import os
import sys

# Ensure benchmark scripts directory is on python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from benchmark_llm_cache_dual import run_cache_benchmarks

if __name__ == "__main__":
    run_cache_benchmarks()
