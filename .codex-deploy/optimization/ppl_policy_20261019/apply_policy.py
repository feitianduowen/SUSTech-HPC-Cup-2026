import argparse
import hashlib
import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path


POLICY_ID = '20261019-ppl-tolerance-5pct'
OLD_CHECK = 'status = "PASS" if abs(diff_pct) <= tolerance else "FAIL"'
NEW_CHECK = '''if base_ppl != 2.7696 or tolerance != 5.0:
        sys.exit("PPL INVALID: amended policy requires baseline 2.7696 and tolerance 5%")
    result["accepted_ppl_interval"] = [2.63112, 2.90808]
    result["policy_id"] = "20261019-ppl-tolerance-5pct"
    status = "PASS" if 2.63112 <= ppl <= 2.90808 else "FAIL"'''


def amend(text):
    text = re.sub(r'^PPL_MAX_REL_DIFF_PERCENT=0\.5[^\n]*',
                  'PPL_MAX_REL_DIFF_PERCENT=5.0  # Official amendment: inclusive [2.63112, 2.90808]',
                  text, flags=re.M)
    text = text.replace(OLD_CHECK, NEW_CHECK)
    text = text.replace('2.755752', '2.63112').replace('2.783448', '2.90808')
    text = text.replace('允许±0.5%', '允许±5%')
    return text


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', required=True)
    parser.add_argument('--audit', required=True)
    parser.add_argument('--local', action='store_true')
    args = parser.parse_args()
    root, audit = Path(args.root), Path(args.audit)
    if args.local:
        directories = [root/'package', root/'optimization/orchestrator',
                       root/'optimization/compiler_pgo', root/'optimization/source_v2',
                       root/'optimization/q8_avx2_v2']
    else:
        directories = [root/'scripts', root/'optimization/20261018-v1/scripts',
                       root/'optimization/20261019-compiler-pgo',
                       root/'optimization/20261019-q8-avx2-v2',
                       root/'optimization/20261019-q8-avx2-v2/scripts',
                       root/'optimization/20261019-source-v2',
                       root/'optimization/20261019-source-v2/scripts',
                       root/'optimization/20261019-q8-avx512',
                       root/'optimization/20261019-q8-avx512/scripts',
                       root/'optimization/20261019-memory/scripts']
    stamp = datetime.now(timezone(timedelta(hours=8))).isoformat()
    audit.mkdir(parents=True, exist_ok=True)
    changes = []
    for directory in directories:
        if not directory.is_dir():
            continue
        for path in sorted(directory.iterdir()):
            if not path.is_file() or path.suffix not in ['.lsf', '.py', '.sh']:
                continue
            # Reference asset validation checks the immutable original JSON,
            # whose recorded 0.5% remains historical evidence.
            if path.name == 'check_assets.py':
                continue
            before = path.read_bytes()
            after = amend(before.decode('utf-8')).encode('utf-8')
            if after == before:
                continue
            relative = path.relative_to(root)
            backup = audit/'backups'/relative
            backup.parent.mkdir(parents=True, exist_ok=True)
            if not backup.exists():
                backup.write_bytes(before)
            temporary = path.with_name(path.name+'.policy5-writing')
            temporary.write_bytes(after)
            temporary.chmod(path.stat().st_mode)
            temporary.replace(path)
            changes.append({'path':str(path), 'backup':str(backup),
                            'before_sha256':hashlib.sha256(before).hexdigest(),
                            'after_sha256':hashlib.sha256(after).hexdigest()})
    record = {'policy_id':POLICY_ID, 'applied_at_hkt':stamp,
              'baseline_ppl':2.7696, 'tolerance_percent':5.0,
              'accepted_interval_inclusive':[2.63112,2.90808],
              'source':'User provided official rule amendment in this conversation',
              'unchanged':'Model/data, all PPL conditions and 590s timeout, PP/TG parameters, compiler requirement, score formula',
              'historical_evidence':'Original reference/rules, result JSON, logs, completed-job snapshots remain unchanged',
              'changes':changes}
    destination = audit/('application-'+datetime.now().strftime('%H%M%S%f')+'.json')
    destination.write_text(json.dumps(record,ensure_ascii=False,indent=2), encoding='utf-8')
    print(json.dumps({'changed_files':len(changes),'audit':str(destination)}))


if __name__ == '__main__':
    main()
