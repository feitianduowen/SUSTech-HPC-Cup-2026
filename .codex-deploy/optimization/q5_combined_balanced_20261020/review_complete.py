import datetime
import json
import pathlib
import statistics

root = pathlib.Path('/work/apac2602/qwen38-cpu/optimization/20261020-q5-combined-balanced')
stamp = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat()
joint = {'reviewed_hong_kong': stamp, 'decision': 'model_gain_not_established_do_not_promote', 'jobs': {}}
for jid in ['4340898', '4340899']:
    out = root / 'results' / jid
    assert (out / 'job.status').read_text().startswith('COMPLETE')
    summary = json.loads((out / 'summary.json').read_text())
    for directory in [out / 'diagnostics/preparation'] + [out / c['directory'] for c in summary['cases']]:
        ppl = json.loads((directory / 'perplexity_result.json').read_text())
        assert ppl['status'] == 'PASS' and 2.63112 <= ppl['ppl'] <= 2.90808
        cfg = ppl['conditions']
        assert cfg['data_sha256'] == '173c87a53759e0201f33e0ccf978e510c2042d7f2cb78229d9a50d79b9e7dd08'
        assert tuple(cfg[k] for k in ['ppl_ctx', 'ppl_chunks', 'ppl_batch', 'ppl_ubatch', 'threads', 'kv_cache_k', 'kv_cache_v', 'numa', 'warmup', 'gpu_layers']) == (512, 2, 512, 256, 38, 'f16', 'f16', 'distribute', False, 0)
        for key, filename, dimensions in [('pp', 'pp2048.json', (2048, 0, 0)), ('tg', 'tg128_d2048.json', (0, 128, 2048))]:
            x = json.loads((directory / filename).read_text())[0]
            assert tuple(x[k] for k in ['n_prompt', 'n_gen', 'n_depth']) == dimensions
            assert tuple(x[k] for k in ['n_threads', 'n_batch', 'n_ubatch', 'n_gpu_layers', 'type_k', 'type_v', 'model_size']) == (38, 2048, 512, 0, 'f16', 'f16', 111323630080)
            assert len(x['samples_ns']) == len(x['samples_ts']) == 10
            assert min(x['samples_ns']) > 0 and min(x['samples_ts']) > 0
            if directory == out / 'diagnostics/preparation':
                summary['preparation'][key]['samples_ns'] = x['samples_ns']
    original = [c for c in summary['cases'] if c['letter'] == 'A']
    first, last = original
    joint['jobs'][jid] = dict(order=summary['order'], pass_means=summary['pass_means'], candidate_change=summary['candidate_change'],
        max_pp_cv=max(c['pp']['cv'] for c in summary['cases']), max_tg_cv=max(c['tg']['cv'] for c in summary['cases']),
        original_pass_change={key: last[key]['avg_ts'] / first[key]['avg_ts'] - 1 for key in ['pp', 'tg']},
        case_results=[{'case': c['directory'], 'ppl': c['ppl']['ppl'], 'pp': c['pp']['avg_ts'], 'tg': c['tg']['avg_ts']} for c in summary['cases']])
    (out / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
joint.update(evidence='Both jobs COMPLETE. Eight comparison cases:80 PP +80 TG raw samples. Two separate preparation cases:20 PP+20 TG samples. All ten fixed PPL=2.7767 PASS. Preparation excluded by predeclared plan; all comparison samples retained.',
    caveat='PP direction reverses:ABBA+23.346% vs BAAB-1.672%. ABBA original PP34.889999 then54.219316 despite separate full preparation. TG is lower for the candidate in both orders:-0.897%/-1.762%. No reproducible full-model speedup established; do not pool the two nodes or select favorable passes. The kernel microbenchmark remains valid within its narrower scope.',
    next_recommendation='Retain independent combined source and evidence. Do not repeat the same balanced model test solely to seek a favorable outcome; prioritize a different hotspot or diagnose runtime/I/O drift before further model-gain claims.')
(root / 'joint_review.json').write_text(json.dumps(joint, indent=2) + '\n')
for jid in ['4340898', '4340899']:
    out = root / 'results' / jid
    path = out / 'summary.json'
    summary = json.loads(path.read_text())
    summary.setdefault('initial_pass_summary', {k: summary[k] for k in ['interpretation', 'decision']})
    summary.update(joint_review=joint, decision=joint['decision'], interpretation='Completed Q5 combined '+summary['order']+'. '+joint['evidence']+' '+joint['caveat']+' Decision:do not promote.')
    path.write_text(json.dumps(summary, indent=2) + '\n')
next_path = root / 'next_actions.json'
value = json.loads(next_path.read_text())
value.update(updated_hong_kong=stamp, review=joint, next=[joint['next_recommendation'], 'Preserve all source, logs and raw samples; keep Excel and server mirror synchronized.'])
value.pop('interim_review', None)
for job in value['jobs']:
    job.update(last_known_status='DONE', latest_stage=(root / 'results' / job['job_id'] / 'job.status').read_text().strip(), complete_comparison_passes=4, comparison_ppl_passes=4)
next_path.write_text(json.dumps(value, indent=2) + '\n')
print(json.dumps(joint))
