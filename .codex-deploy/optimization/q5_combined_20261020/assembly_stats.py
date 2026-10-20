import json
import re
import sys
from pathlib import Path

r=Path(sys.argv[1]);stats={}
for name in ['baseline','mask','unroll','candidate']:
    s=(r/('dot-'+name+'-assembly.txt')).read_text()
    assert '<ggml_vec_dot_q5_1_q8_1>:' in s
    stats[name]={
      'vector_fma_static':len(re.findall(r'\bvfmadd\w*ps\b',s)),
      'scalar_fma_static':len(re.findall(r'\bvfmadd\w*ss\b',s)),
      'half_conversion_static':len(re.findall(r'\bvcvtph2ps\b',s)),
      'conditional_jumps_static':len(re.findall(r'\bj(?:e|ne|l|le|g|ge|a|ae|b|be|z|nz)\s',s)),
    }
stats['scope']='Static counts from actual exported function, including remainder paths; not a dynamic instruction count or a speedup claim.'
(r/'dot-assembly-stats.json').write_text(json.dumps(stats,indent=2));print(json.dumps(stats))
