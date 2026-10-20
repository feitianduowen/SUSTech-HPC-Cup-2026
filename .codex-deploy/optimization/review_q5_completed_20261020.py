import json
import pathlib
import statistics
import datetime

ROOT = pathlib.Path('/work/apac2602/qwen38-cpu/optimization')
now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat()
for jid, tag in [('4340602', 'unroll'), ('4340624', 'combined')]:
    root = ROOT / ('20261020-q5-' + tag) / 'results' / jid
    cases = []
    for directory in sorted(root.glob('[0-9][0-9]_*')):
        ppl = json.loads((directory / 'perplexity_result.json').read_text())
        assert 2.63112 <= ppl['ppl'] <= 2.90808
        cfg = ppl['conditions']
        for key, value in dict(ppl_ctx=512, ppl_chunks=2, ppl_batch=512, ppl_ubatch=256, threads=38,
                               kv_cache_k='f16', kv_cache_v='f16', numa='distribute', warmup=False, gpu_layers=0).items():
            assert cfg[key] == value, (jid, directory, key)
        assert cfg['data_sha256'] == '173c87a53759e0201f33e0ccf978e510c2042d7f2cb78229d9a50d79b9e7dd08'
        row = {'case': directory.name, 'ppl': ppl['ppl'], 'ppl_status': 'PASS'}
        for key, filename, shape in [('pp', 'pp2048.json', (2048, 0, 0)), ('tg', 'tg128_d2048.json', (0, 128, 2048))]:
            value = json.loads((directory / filename).read_text())[0]
            assert tuple(value[k] for k in ['n_prompt', 'n_gen', 'n_depth']) == shape
            for field, expected in dict(n_threads=38, n_batch=2048, n_ubatch=512, type_k='f16', type_v='f16', n_gpu_layers=0, model_size=111323630080).items():
                assert value[field] == expected, (jid, directory, field)
            assert len(value['samples_ts']) == len(value['samples_ns']) == 10
            assert all(x > 0 for x in value['samples_ts'] + value['samples_ns'])
            samples = value['samples_ts']
            row[key] = {'avg_ts': value['avg_ts'], 'raw_sample_count': len(samples),
                        'raw_cv_percent': 100 * statistics.stdev(samples) / statistics.mean(samples),
                        'samples_ts': samples, 'samples_ns': value['samples_ns']}
        cases.append(row)
    assert len(cases) == 3
    before, candidate, after = cases
    comparisons = {}
    for label, baseline in [('first_original', before), ('last_original', after)]:
        comparisons[label] = {k + '_change_percent': 100 * (candidate[k]['avg_ts'] / baseline[k]['avg_ts'] - 1) for k in ['pp', 'tg']}
    drift = {k + '_change_percent': 100 * (after[k]['avg_ts'] / before[k]['avg_ts'] - 1) for k in ['pp', 'tg']}
    summary_path = root / 'summary.json'
    summary = json.loads(summary_path.read_text())
    prior = summary.get('source_screening_review', {})
    summary.setdefault('pre_completion_review', prior)
    review = dict(prior)
    review.update(status='COMPLETE_MODEL_GAIN_NOT_ESTABLISHED', decision='do_not_promote_model_gain_not_established',
                  reviewed_hong_kong=now, phase=(root / 'job.status').read_text().strip(),
                  model_cases=cases, candidate_comparisons=comparisons, original_before_after_drift=drift,
                  validation='All six performance cases contain ten raw samples; all three fixed PPL cases PASS; fixed benchmark dimensions checked.',
                  limitation='Single original/candidate/original sequence, no counterbalanced replication. First original PP differs strongly from last original; last comparison alone does not establish a causal gain. Raw samples and reported statistics retained.')
    summary['source_screening_review'] = review
    summary['interpretation'] = ('Completed Intel Q5 ' + tag + ' A/B/A. All PPL=2.7767 and PP/TG each ten samples. '
        'Candidate vs last original PP {:+.4f}%, TG {:+.4f}%. First-to-last original PP drift {:+.4f}%. '
        'Kernel correctness and speed gains retained, but full-model gain not established; do not promote. '
        'Streaming diagnostic4340728 is separate synthetic evidence and does not establish model throughput.'.format(
            comparisons['last_original']['pp_change_percent'], comparisons['last_original']['tg_change_percent'], drift['pp_change_percent']))
    summary_path.write_text(json.dumps(summary, indent=2) + '\n')
    (root / 'completion-review.json').write_text(json.dumps(review, indent=2) + '\n')
    print(json.dumps({'job_id': jid, 'phase': review['phase'], 'comparisons': comparisons, 'original_drift': drift, 'decision': review['decision']}))
