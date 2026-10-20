import json
import subprocess
from datetime import datetime,timedelta,timezone
from pathlib import Path

root=Path(__file__).resolve().parent
raw=subprocess.check_output(['bhosts','-w','hg_6148'],universal_newlines=True)
(root/'admission_snapshot.txt').write_text(raw)
hosts=[]
for line in raw.splitlines()[1:]:
    c=line.split()
    if len(c)>=6 and c[0].startswith('r13n') and c[1]=='ok' and c[3]=='40' and c[4]=='0' and c[0] not in ['r13n08','r13n45','r13n10','r13n22']:
        hosts.append(c[0])
assert len(hosts)>=2,('Need two free matching nodes',hosts)
for order in ['hotspots','threading']:
    source=root/('submission_'+order+'.json')
    spec=json.loads(source.read_text())
    spec['lsf_args']+=['-m',' '.join(hosts)]
    target=root/('admitted_'+order+'.json')
    target.write_text(json.dumps(spec,ensure_ascii=False,indent=2))
(root/'admission.json').write_text(json.dumps({'at_hkt':datetime.now(timezone(timedelta(hours=8))).isoformat(),'resource_group':'hg_6148','idle_candidates':hosts,'excluded_previous_nodes':['r13n08','r13n45','r13n10','r13n22'],'slots_each':40},indent=2))
print(json.dumps({'eligible_hosts':hosts,'count':len(hosts)}))
