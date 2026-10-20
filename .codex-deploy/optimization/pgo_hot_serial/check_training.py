import json
import sys
from pathlib import Path

root=Path(sys.argv[1])
records={}
for phase,shape in [('pp',(64,0,0)),('tg',(0,8,64))]:
    rows=json.loads((root/('training-'+phase+'.json')).read_text())
    assert isinstance(rows,list) and len(rows)==1
    row=rows[0]
    assert (row['n_prompt'],row['n_gen'],row['n_depth'])==shape
    assert (row['n_threads'],row['n_batch'],row['n_ubatch'],row['n_gpu_layers'],row['type_k'],row['type_v'])==(1,2048,512,0,'f16','f16')
    assert len(row['samples_ns'])==len(row['samples_ts'])==1
    records[phase]={'shape':shape,'complete':True,'unscored':True}
(root/'training-validation.json').write_text(json.dumps(records,indent=2))
print(json.dumps(records))
