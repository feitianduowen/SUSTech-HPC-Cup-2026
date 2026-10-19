# GGML PGO V4

4337257 ended with EXIT 124 at 2026-10-19 15:59:54 Hong Kong time. Its actual
instrumented build and link passed; the PP64 training command hit its 1200-second
limit during model weight repacking, ending at blk.41. The last process sample
showed one active thread, growing resident memory (about 71.6 GiB), continuing CPU
consumption and no major page faults. This supports a slow initialization diagnosis.

training-pp.json is empty. TG training, profile merge, feedback compilation and the
PGO build's PPL did not execute. Three nonempty dyn files remain diagnostic evidence
only. They are not a completed profile and are not used by the next job. The PPL
2.7767 result belongs to the reused plain control, not a validated PGO product.

4337448 started on r13n24 at 2026-10-19 16:09 Hong Kong time. V4 changes only the
unscored PP64 and TG8@D64 training limits to 3600 seconds each, since both separate
processes must load/repack the model. It creates fresh gen/use builds and profile
directories; original sources, V3 outputs and incomplete counters remain intact.
The unchanged control from 4337216 is reused read-only after SHA256 and fixed PPL
condition validation. Intel Classic 2021.9, precise/no-ftz, 40 allocated slots and
38 inference threads are preserved.

The fixed PPL remains limited to 590 seconds. Formal PP2048/TG128@D2048 parameters
and ten repetitions remain unchanged. Training output never counts as performance.
Require normal training exit, valid output shapes, useful counters, successful merge
and feedback build, quantization tests and independent fixed PGO PPL before speed
tests. Do not submit duplicates while this job runs. Preserve all failed jobs.
