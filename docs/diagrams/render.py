"""Render source-traceable architecture figures; not a netlist schematic export."""
from pathlib import Path
import hashlib
import json
import math
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
COLORS={'implemented':'#e0edff','external':'#f1f5f9',
        'control':'#fff1d6','model':'#dcfce7','artifact':'#ede9fe'}

def boundary(node,other):
    x,y=node['x']+14,node['y']+6.5
    ox,oy=other['x']+14,other['y']+6.5
    dx,dy=ox-x,oy-y
    scale=min(14/abs(dx) if dx else math.inf,6.5/abs(dy) if dy else math.inf)
    return x+dx*scale,y+dy*scale

def render(diagram,out):
    fig,ax=plt.subplots(figsize=(16,9))
    ax.set(xlim=(0,100),ylim=(0,73));ax.axis('off')
    plt.rcParams['svg.fonttype']='none'
    fig.suptitle(diagram['title'],fontsize=22,fontweight='bold',y=.98)
    fig.text(.5,.935,diagram['subtitle'],ha='center',fontsize=12,color='#475569')
    nodes={n['id']:n for n in diagram['nodes']}
    for edge in diagram['edges']:
        a,b=nodes[edge['from']],nodes[edge['to']]
        points=edge.get('points',[boundary(a,b),boundary(b,a)])
        color='#2563eb' if edge.get('kind','data')=='data' else '#64748b'
        style='--' if edge.get('kind') in ['control','hierarchy','external'] else '-'
        for p,q in zip(points[:-2],points[1:-1]):
            ax.plot([p[0],q[0]],[p[1],q[1]],color=color,linewidth=1.8,linestyle=style,zorder=1)
        ax.add_patch(FancyArrowPatch(points[-2],points[-1],arrowstyle='-|>',mutation_scale=16,
            color=color,linewidth=1.8,linestyle=style,zorder=1))
        if edge.get('label'):
            lx,ly=edge.get('label_xy',[(points[0][0]+points[-1][0])/2,(points[0][1]+points[-1][1])/2+1.8])
            ax.text(lx,ly,edge['label'],ha='center',va='center',fontsize=9,color='#334155',
                    bbox={'facecolor':'white','edgecolor':'none','alpha':.95,'pad':2},zorder=4)
    for n in nodes.values():
        kind=n.get('kind','implemented')
        ax.add_patch(FancyBboxPatch((n['x'],n['y']),28,13,boxstyle='round,pad=.35',
             facecolor=COLORS[kind],edgecolor='#64748b',linewidth=1.4,
             linestyle='--' if kind=='external' else '-',zorder=2))
        ax.text(n['x']+14,n['y']+6.5,n['label'],ha='center',va='center',fontsize=11,
                linespacing=1.45,color='#172337',zorder=3)
    fig.text(.5,.055,diagram['scope'],ha='center',fontsize=10,color='#475569')
    fig.text(.5,.025,'Blue: signal/data flow   |   Dashed gray: control, hierarchy or external context   |   Dashed boxes: not implemented here',
             ha='center',fontsize=9,color='#64748b')
    fig.subplots_adjust(top=.88,bottom=.12,left=.025,right=.975)
    for suffix in ['png','svg']:
        fig.savefig(out/f"{diagram['id']}.{suffix}",dpi=150,facecolor='white')
    plt.close(fig)

def main():
    design=json.loads((HERE/'design.json').read_text(encoding='utf-8'))
    out=HERE/'figures';out.mkdir(exist_ok=True)
    hashes={}
    for source in design['sources']:
        path=ROOT/source['path']
        data=path.read_bytes();text=data.decode('utf-8',errors='replace')
        for marker in source.get('contains',[]):
            assert marker in text,(source['path'],marker)
        hashes[source['path']]=hashlib.sha256(data).hexdigest()
    for diagram in design['diagrams']:
        ids=[n['id'] for n in diagram['nodes']]
        assert len(ids)==len(set(ids))
        for edge in diagram['edges']: assert edge['from'] in ids and edge['to'] in ids
        render(diagram,out)
    (HERE/'provenance.json').write_text(json.dumps({'source_commit':design['source_commit'],
        'method':'Annotated source-derived block diagrams; not synthesized netlist or GUI screenshots',
        'source_sha256':hashes},indent=2)+'\n',encoding='utf-8')
    print(f"Rendered {len(design['diagrams'])} PNG/SVG diagram pairs for {design['project']}")

if __name__=='__main__':main()
