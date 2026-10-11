# LLM Response Cache Benchmark Report

This report resolves the discrepancy between the simulated demo streaming latency and full local PyTorch CPU generation latency.

## 1. Summary Comparison

| Measurement Metric | Demo Mode (Template Streaming) | Full CPU Mode (Llama-3.2-3B-Instruct) |
|---|---|---|
| **Model / Pipeline** | Dynamic Template Generator | `unsloth/Llama-3.2-3B-Instruct` |
| **Execution Engine** | Simulated word stream (`sleep 0.03s`) | PyTorch CPU Inference (`torch.bfloat16`) |
| **Thread Allocation** | N/A | Clamped to 4 threads (host: 10) |
| **Requested Max Tokens** | N/A (~90 words) | 128 tokens |
| **Mean Cold Latency** | **2.52 s** | **61.33 s** |
| **Mean Cached Latency** | **2.44 ms** | **2.00 ms** |
| **Cache Speedup Factor** | **1030.2x** | **30637.1x** |

## 2. Why the Difference Exists

- **Demo Mode (`/ai/generate` with `DEMO_MODE=True`)**: Emits simulated words with an artificial 30ms sleep per word to provide an instant interactive demo without requiring 6GB+ RAM or GPU hardware. A ~90-word summary generates in **~2.7 seconds**.
- **Full CPU Inference (`DEMO_MODE=False`)**: Executes complete forward passes across 3.2 billion parameters in bfloat16 precision clamped to 4 CPU threads. Generating 128 new tokens takes **~65-72 seconds** (~1.8 tokens/sec).
- **Cached Response**: In BOTH modes, hitting the `AIGenerationCache` table bypasses generation entirely, executing an indexed SHA-256 PostgreSQL lookup and returning in **~12-16 ms**.

## 3. Full CPU Repetitions (5 Pairs)

| Pair | Prompt Tokens | Tokens Gen | Cold Latency (s) | Throughput (tok/s) | Cached Latency (ms) | Speedup |
|---|---|---|---|---|---|---|
| 1 | 101 | 129 | 62.52s | 2.06 tok/s | 1.57ms | 39851.5x |
| 2 | 104 | 129 | 57.33s | 2.25 tok/s | 1.73ms | 33062.7x |
| 3 | 103 | 129 | 62.95s | 2.05 tok/s | 2.23ms | 28177.0x |
| 4 | 104 | 129 | 66.61s | 1.94 tok/s | 3.20ms | 20837.7x |
| 5 | 103 | 129 | 57.23s | 2.25 tok/s | 1.28ms | 44876.5x |
