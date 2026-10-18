import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

root = Path(__file__).parent / 'results_4335666'
fig, axes = plt.subplots(1, 2, figsize=(10, 3.6), layout='constrained')
for ax, name, title in zip(axes, ['pp2048', 'tg128_d2048'], ['PP2048', 'TG128 @ depth 2048']):
    b = json.loads((root / name / 'bench.json').read_text())[0]
    x, y = list(range(1, 11)), b['samples_ts']
    ax.plot(x, y, 'o-', color='#2261a6', lw=2, ms=5)
    ax.axhline(b['avg_ts'], color='#ca6632', ls='--', label='Mean: %.2f t/s' % b['avg_ts'])
    ax.set(title=title, xlabel='Repetition', ylabel='Tokens / second', xticks=x)
    ax.grid(axis='y', alpha=.2)
    ax.legend(frameon=False)
fig.suptitle('Intel build under VTune sampling — diagnostic measurements', fontsize=12)
fig.savefig(Path('D:/compete/Qwen38_CPU_Profiling.png'), dpi=180)
