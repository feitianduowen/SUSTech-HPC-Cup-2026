import json
import statistics
import sys
from pathlib import Path

out = Path(sys.argv[1])
check = json.loads((out / 'q4-correctness.json').read_text())
matrix = json.loads((out / 'library-correctness.json').read_text())
assert check['status'] == matrix['status'] == 'PASS'
assert check['bit_mismatches'] == matrix['bit_mismatches'] == 0
assert check['cases'] == 128128 and check['finite_half_patterns'] == 63488
raw = json.loads((out / 'q4-raw-samples.json').read_text())
assert len(raw) == 8
results = []
for item in raw:
    a, b = item['baseline'], item['candidate']
    assert len(a) == len(b) == 10 and min(a + b) > 0
    paired = [x / y - 1 for x, y in zip(a, b)]
    results.append({'variant': 'q4-maskshuffle', 'blocks': item['n'] // 256,
                    'n': item['n'], 'nc': item['nc'], 'mode': item['mode'] + ' nc=' + str(item['nc']),
                    'baseline': {'ns_median': statistics.median(a), 'all_ns': a},
                    'q4-maskshuffle': {'ns_median': statistics.median(b), 'all_ns': b},
                    'paired_median_speedup': statistics.median(paired), 'all_paired_speedups': paired,
                    'paired_wins': sum(x > y for x, y in zip(a, b)),
                    'weight_bytes': item['weight_bytes'], 'sets': item['sets'], 'calls_per_round': item['calls_per_round']})
advance = all(x['paired_median_speedup'] >= -0.05 for x in results) and any(
    x['mode'] == 'resident nc=64' and x['paired_median_speedup'] >= 0.03 and x['paired_wins'] >= 7 for x in results)
summary = {'checks': {'q4-maskshuffle': check, 'library-correctness.json': matrix}, 'kernel_times': results,
           'advance_to_model': advance, 'assembly_statistics': json.loads((out / 'q4-assembly-stats.json').read_text()),
           'proof_scope': 'Only shuffle+blend pairs replaced by AVX512VL masked dword shuffle with complementary masks0xAA/0x55. Every lane and all integer/FP arithmetic chains retained. Original AVX2 fallback preserved; target-node path tested.',
           'interpretation': 'Actual exported Q4_Kx8/Q8_K GEMV original and candidate functions verified by dladdr, both full Intel O3 libraries loaded by absolute path. nr1 direct check128128 cases, all finite FP16 patterns in d and dmin,3repetitions, exact bits; general matrix144cases exact. Eight resident/stream256MiB configurations with ten AB/BA rounds onCPU0/membind0, same inputs. Not full-model throughput. Gate:>=3% paired median at resident nc64 for n2560or6144 with>=7/10wins; no configuration below-5%. '+('Model gate eligible; fresh PPL/PP10/TG10 A/B/A pending.' if advance else 'Kernel screen did not pass; do not run model phase or claim PPL/model gain.')}
(out / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
print(json.dumps(summary))
