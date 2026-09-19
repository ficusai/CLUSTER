AI CLUSTER MODEL RECOMMENDATIONS
=================================

Measured RAM (live):
  Root (MBP 8GB)      : 2.3 GB available
  Android (7.2GB)     : 2.4 GB available
  MacBook Air (4GB)   : ~2.0 GB available (est, after OS)

Rule: workers need model_layers + overhead < available RAM.
Root uses same binary for local inference or splits layers via --rpc.

Live baseline:  llama-server with Qwen2.5 1.5B Q4_K_M uses ~1.3 GB RSS.

TINY — fits every node standalone (concurrent parallelism)
  Model                  Ollama               Size   Best For
  Qwen2.5 1.5B  instruct qwen2.5:1.5b        ~1GB  general chat, coding, lang
  Gemma3 1B             gemma3:1b            ~1GB  absolute minimum
  TinyLlama 1.1B        tinyllama:1.1B       ~0.5GB lightweight fallback
  Qwen2.5 Coder 1.5B    qwen2.5-coder:1.5b   ~1GB  code only

  Already on disk: qwen2.5-1.5b-instruct-q4_k_m.gguf

MID — fits root (8GB) alongside Hermes; split across cluster for quality
  Model                  Ollama               Size   Split-OK Notes
  Llama 3.2 3B          llama3.2:3b          ~2GB  yes       best chat at 3B
  Phi-4 Mini 3.8B       phi4:mini            ~2.5GB yes      fastest CPU reasoning
  Qwen3 4B              qwen3:4b             ~2.8GB yes      best small coder
  Gemma3 4B             gemma3:4b            ~3.3GB risky    128K ctx

HEAVY — split ONLY (clustered layers); otherwise root likely OOM
  Model                  Size      Root/Workers Notes
  Llama 3.1 8B           ~5-6GB   root ~2GB  split ~1.5GB/worker
  Mistral Nemo 12B       ~7.5GB   root ~2.5GB Air/Android risky
  Gemma3 12B             ~8.1GB   root ~2.7GB Android OOM
  Qwen3 14B (Q3)         ~7.3GB   root ~2.4GB Android tight

VERDICT
-------
Best immediate model: Qwen2.5 1.5B (already on disk, ~1.3 GB RSS).
Stronger mid upgrade:  Qwen3 4B or Llama 3.2 3B.
For "more brain, same speed": Phi-4 Mini 3.8B.
Cluster split test:     Llama 3.1 8B (only if root RAM frees to >=5GB).

NOTE: root currently has ~2.3 GB free.  8B models need ~5GB RSS for llama-server.
Use swap (23 GB available) or close Hermes browsers to free RAM for heavier splits.

SOURCES
-------
 Ollama Library      : https://ollama.com/search
 GGUF (HuggingFace)  : bartowski, unsloth, MaziyarPanahi
 Quantization        : Q4_K_M (quality/size sweet spot for CPU)

RENAME FILE
-----------
Place GGUF as /models/<name>-q4_k_m.gguf.
Edit config.yaml -> ai.model to point to it.
Restart root: close & re-run the AI Cluster desktop action.
