import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

work=Path('D:/compete')
rows=json.loads((work/'.codex-deploy/optimization/evidence/experiment_summary.json').read_text())
data={r['name']:r for r in rows}
groups=[('4335857','r13n09: baseline -> native -> concat',['baseline','native','concat']),('4335870','r13n10: baseline -> q8-u2',['baseline','q8-u2']),('4335903','r13n04: native -> baseline',['native','baseline']),('4335930','combined -> native',['native-concat-u2','native'])]
colors={'baseline':'#7B8794','native':'#2878B5','q8-u2':'#6D59A6','concat':'#2A9D8F','native-concat-u2':'#D98E32'}
plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'axes.titleweight':'bold','figure.facecolor':'white'})
fig,axes=plt.subplots(len(groups),2,figsize=(11.5,12),layout='constrained')
for i,(job,title,variants) in enumerate(groups):
    for j,key in enumerate(['pp','tg']):
        ax=axes[i,j]
        for x,variant in enumerate(variants):
            row=data.get('confirm-'+variant+'_'+job)
            if row and row[key]:
                avg=row[key];std=row[key+'_std'];samples=row[key+'_samples']
                ax.bar(x,avg,color=colors[variant],alpha=.72,width=.6,zorder=2)
                ax.errorbar(x,avg,yerr=std,color='#25313B',capsize=5,linewidth=1.2,zorder=4)
                ax.scatter(x+np.linspace(-.18,.18,len(samples)),samples,s=15,color='#25313B',alpha=.75,zorder=3)
                ax.annotate(f'{avg:.3f}',(x,avg+std),xytext=(0,6),textcoords='offset points',ha='center',fontsize=10)
            else:
                ax.text(x,.12,'pending',ha='center',transform=ax.get_xaxis_transform(),color='#777777')
        ax.set_xticks(range(len(variants)),[v.replace('native-concat-u2','native + concat + u2') for v in variants])
        ax.set_ylim(bottom=0)
        ax.margins(y=.22)
        ax.set_ylabel('tokens/s')
        ax.set_title(f'{job} | '+('PP2048' if key=='pp' else 'TG128 @ depth 2048'),loc='left',fontsize=11)
        ax.text(.02,.97,title,ha='left',va='top',transform=ax.transAxes,fontsize=9,color='#555555')
        ax.grid(axis='y',color='#E4E8ED',zorder=0)
fig.suptitle('Qwen3.8 CPU: sequential comparisons on the same node',fontsize=15,fontweight='bold')
fig.supxlabel('38 inference threads | fixed workload | all 10 samples shown | whiskers = sample SD\nRun order and memory placement can affect results; these are development measurements.',fontsize=10)
target=work/'Qwen38_CPU_优化对照.png'
fig.savefig(target,dpi=170)
plt.close(fig)
print(target)
