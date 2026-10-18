# Agent usage

OpenAI Codex configured an account-local deployment using the official shared source, model, dataset, and baseline. It adapted the supplied LSF scripts, built the required targets, checked fixed-parameter PPL, and tested real server completion and chat requests.

A GCC reference build passed PPL=2.7696. Intel LLVM presets produced PPL=2.8403, 2.8274, and 2.7931; their failed results are retained under the corresponding job result directories. They were not used for performance scoring.

The final Intel Classic build passed PPL=2.7767 (+0.2563547083%) in job 4335636. Server health, ordinary completion, and chat completion also passed. The final manifest records compiler paths, flags, model assets, and binary/library SHA-256 values.

No llama.cpp or ggml computation source was changed. No model weights, dataset content, official baseline JSON, benchmark statistics, or correctness thresholds were modified. Full PP/TG performance benchmarks were not run.
