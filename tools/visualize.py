"""Reproducible report screenshots and figures from actual Vivado/XSim output.

Requires matplotlib and a local Chromium browser. Never captures the desktop.
Screenshots render report excerpts in HTML, not an imitation of the Vivado GUI.
"""
import hashlib
import html
import json
import os
from pathlib import Path
import re
import subprocess
import time
from PIL import Image

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/figures'
EVIDENCE = ROOT / 'reports/evidence'
NAMES = ['Direct RTL', 'Exact PLA', 'Shared PLA']
COLORS = ['#2563eb', '#0d9488', '#d97706']
plt.rcParams.update({'font.family':'DejaVu Sans', 'font.size':11,
                     'axes.spines.top':False, 'axes.spines.right':False,
                     'svg.fonttype':'none'})

def read_metrics():
    rows = []
    for file in sorted((ROOT/'reports/synthesis').glob('*_metrics.json')):
        row = json.loads(file.read_text())
        report = file.with_name(file.name.replace('_metrics.json', '_utilization.rpt'))
        match = re.search(r'^\| CLB LUTs\s*\|\s*(\d+)', report.read_text(), re.M)
        if not match:
            raise ValueError(f'No physical CLB LUT count in {report}')
        row['clb_luts'] = int(match[1])
        rows.append(row)
    assert len(rows) == 9
    return rows

def save_figure(fig, name):
    fig.savefig(OUT/f'{name}.png', dpi=150, facecolor='white', bbox_inches='tight')
    fig.savefig(OUT/f'{name}.svg', facecolor='white', bbox_inches='tight')
    plt.close(fig)

def architecture():
    fig, ax = plt.subplots(figsize=(14, 7))
    ax.set(xlim=(0,100), ylim=(0,65)); ax.axis('off')
    fig.suptitle('Superscalar RISC-V decoder architecture', fontsize=20, fontweight='bold')
    def box(x,y,w,h,text,color='#eef2ff'):
        ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0.7',
                                   facecolor=color,edgecolor='#64748b',linewidth=1.3))
        ax.text(x+w/2,y+h/2,text,ha='center',va='center',fontsize=11)
    def arrow(points):
        for a,b in zip(points[:-2],points[1:-1]):
            ax.plot([a[0],b[0]],[a[1],b[1]],color='#475569',linewidth=1.6)
        ax.add_patch(FancyArrowPatch(points[-2],points[-1],arrowstyle='-|>',
                                    mutation_scale=15,color='#475569',linewidth=1.6))
    box(2,49,23,10,'Instruction specification\n40 RV32I + 8 optional M')
    box(35,49,23,10,'Python generator\nMasks, controls, cube merging')
    box(68,47,29,14,'Select one implementation\nDirect RTL / Exact PLA / Shared PLA')
    arrow([(25.8,54),(34.2,54)]); arrow([(58.8,54),(67.2,54)])
    box(2,27,23,11,'Fetch interface\n32-bit words + lane-valid bits','#f0fdfa')
    box(35,26,23,13,'1 / 2 / 4 parallel lanes\nLegality, controls, registers\nand immediate assembly')
    arrow([(25.8,32.5),(34.2,32.5)])
    arrow([(82.5,46.2),(82.5,42),(46.5,42),(46.5,39.8)])
    box(68,29,29,10,'In-bundle dependency checks\nRAW rs1 / RAW rs2 / WAW','#fef3c7')
    arrow([(58.8,33),(67.2,33)])
    box(35,5,23,13,'Elastic pipeline register\nReady / valid, stall, flush','#f0fdfa')
    arrow([(46.5,25.2),(46.5,18.8)])
    arrow([(82.5,28.2),(82.5,11.5),(58.8,11.5)])
    box(2,6,23,11,'Downstream CPU stages\nExecution / rename / scheduling','#f8fafc')
    arrow([(34.2,11.5),(25.8,11.5)])
    fig.text(.5,.015,'Decoder subsystem only; PC context and instruction execution are downstream responsibilities.',
             ha='center',fontsize=10,color='#475569')
    save_figure(fig,'architecture')

def comparisons(rows):
    fig, axes = plt.subplots(1,2,figsize=(14,5.9))
    positions = np.arange(3)
    for impl,(name,color) in enumerate(zip(NAMES,COLORS)):
        selected = sorted((r for r in rows if r['implementation']==impl),key=lambda r:r['width'])
        for ax,key in zip(axes,['clb_luts','critical_datapath_ns']):
            vals = [r[key] for r in selected]
            bars = ax.bar(positions+(impl-1)*.24,vals,.23,label=name,color=color)
            ax.bar_label(bars,labels=[str(v) if key=='clb_luts' else f'{v:.3f}' for v in vals],padding=4,fontsize=9)
            ax.set_xticks(positions,['1 lane','2 lanes','4 lanes'])
            ax.grid(axis='y',alpha=.2); ax.set_axisbelow(True)
    axes[0].set(ylabel='CLB LUTs (adjusted for LUT combining)',ylim=(0,max(r['clb_luts'] for r in rows)*1.23))
    axes[1].set(ylabel='Routed critical datapath delay (ns)',ylim=(0,4.1))
    axes[0].set_title('FPGA resource usage',fontsize=15)
    axes[1].set_title('Internal register-to-register datapath',fontsize=15)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles,labels,loc='upper center',ncol=3,bbox_to_anchor=(.5,.91),frameon=False)
    fig.suptitle('Area and timing across nine routed designs',fontsize=19,fontweight='bold',y=.99)
    fig.subplots_adjust(top=.78,bottom=.19,wspace=.25)
    fig.text(.5,.07,'Vivado 2026.1 | Alveo U50 | RV32I | 10 ns constraint | Same registered boundaries and dependency logic',ha='center',fontsize=10)
    fig.text(.5,.025,'OOC clock source/skew is idealized; external IO paths excluded. Datapath delay is not measured board Fmax.',ha='center',fontsize=9,color='#475569')
    save_figure(fig,'area_timing')

def waveform():
    path=EVIDENCE/'pipeline_waveform.vcd'
    text=path.read_text()
    assert re.search(r'\$timescale\s+1ps\s+\$end',text), 'Expected 1 ps VCD units'
    symbols={m.group(1):m.group(2) for m in re.finditer(r'\$var\s+\S+\s+1\s+(\S+)\s+(\S+)\s+\$end',text)}
    data={name:[] for name in symbols.values()}
    now=0
    for line in text.split('$enddefinitions $end',1)[1].splitlines():
        if line.startswith('#'):
            now=int(line[1:])/1000
            if now>300: break
        elif line and line[0] in '01xXzZ':
            name=symbols.get(line[1:])
            if name: data[name].append((now,int(line[0]) if line[0] in '01' else np.nan))
    names=['clk','reset','flush','in_valid','in_ready','out_valid','out_ready']
    fig,axes=plt.subplots(7,1,figsize=(14,6.5),sharex=True)
    for ax,name in zip(axes,names):
        events=data[name]
        assert events, name
        times=[t for t,v in events]+[300]
        vals=[v for t,v in events]+[events[-1][1]]
        ax.step(times,vals,where='post',color='#2563eb' if name=='clk' else '#0d9488',linewidth=1.5)
        ax.set(ylim=(-.25,1.25),yticks=[0,1]);ax.set_ylabel(name,rotation=0,ha='right',va='center',labelpad=14)
        ax.grid(axis='x',alpha=.18)
        ax.spines['left'].set_visible(False)
    axes[-1].set(xlim=(0,300),xlabel='Simulation time (ns)')
    fig.suptitle('Elastic decode pipeline: actual XSim waveform',fontsize=19,fontweight='bold')
    fig.subplots_adjust(left=.13,top=.9,bottom=.13,hspace=.18)
    fig.text(.5,.025,'First 300 ns from capture_waveform.tcl | Reset/flush block acceptance; outputs are held when stalled.',ha='center',fontsize=10)
    save_figure(fig,'pipeline_waveform')

def browser():
    candidates=[Path(os.environ.get('ProgramFiles','C:/Program Files'))/'Google/Chrome/Application/chrome.exe',
                Path(os.environ.get('ProgramFiles(x86)','C:/Program Files (x86)'))/'Microsoft/Edge/Application/msedge.exe']
    return next(p for p in candidates if p.exists())

def screenshot(name,title,subtitle,body,height=1100,width=1900):
    page='''<!doctype html><html><head><meta charset="utf-8"><style>
    *{box-sizing:border-box}body{margin:0;background:#eef2f6;color:#172337;font-family:Arial,sans-serif;padding:40px}
    h1{font-size:32px;margin:0 0 12px}p{font-size:17px;color:#475569;line-height:1.5}
    section{background:white;border:1px solid #cbd5e1;border-radius:12px;padding:22px;margin-top:22px}
    h2{font-size:20px;margin:0 0 14px}pre{font-family:Consolas,monospace;font-size:13px;line-height:1.5;white-space:pre;margin:0}
    table{border-collapse:collapse;width:100%;font-size:19px}td,th{text-align:left;padding:16px;border-bottom:1px solid #e2e8f0}
    th{background:#f1f5f9}.note{font-size:15px;margin-top:20px}footer{font-size:14px;margin-top:22px;color:#64748b}
    </style></head><body>'''+f'<h1>{html.escape(title)}</h1><p>{html.escape(subtitle)}</p>'+body+'''
    <footer>Report screenshot rendered from project evidence files. This is not a screenshot of the Vivado application UI.</footer></body></html>'''
    page_path=OUT/f'{name}.html'
    page_path.write_text(page,encoding='utf-8')
    target=OUT/f'{name}.png'
    profile=ROOT/f'build/visuals-browser/{name}'
    cmd=[str(browser()),'--headless','--disable-gpu','--no-first-run','--disable-background-networking',
         '--disable-extensions',f'--user-data-dir={profile}',
         '--hide-scrollbars','--force-device-scale-factor=1',f'--window-size={width},{height}',
         f'--screenshot={target}',page_path.as_uri()]
    started=time.time()
    try:
        result=subprocess.run(cmd,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,
                              timeout=30,creationflags=0x08000000)
        if result.returncode:
            raise RuntimeError(f'Browser returned {result.returncode}')
    except subprocess.TimeoutExpired:
        # Some Windows browser background services linger after saving the PNG.
        # The fresh, fully decoded artifact below determines capture success.
        pass
    if not target.exists() or target.stat().st_mtime < started:
        raise RuntimeError(f'Browser did not create a fresh screenshot: {name}')
    with Image.open(target) as im:
        assert im.size == (width,height), (name,im.size)
        im.verify()
    print(f'Captured {target.name}')

def evidence_screenshots(rows):
    logs=list((ROOT/'build/sim').glob('*.log'))
    logs.append(ROOT/'build/waveform_capture.log')
    logs.extend(EVIDENCE.glob('*_xsim.txt'))
    panels=[]
    for kind,needle in [('decoder','PASS: 244040'),('pipeline','PASS: pipeline 4000')]:
        candidates=[p for p in logs if p.exists() and needle in p.read_text(errors='replace')]
        source=max(candidates,key=lambda p:p.stat().st_mtime)
        original=source.read_text(errors='replace')
        start=original.find('source xsim.dir/')
        excerpt=original[start:] if start>=0 else original
        (EVIDENCE/f'{kind}_xsim.txt').write_text(excerpt,encoding='utf-8')
        panels.append(f'<section><h2>{kind.title()} regression — original XSim log excerpt</h2><pre>{html.escape(excerpt)}</pre></section>')
    screenshot('verification_results','XSim verification results',
               'Independent-model decoder regression and pipeline scoreboard. Original PASS lines are preserved.',
               ''.join(panels),height=1050)
    timing=(ROOT/'reports/synthesis/w4_impl2_timing.rpt').read_text()
    start=timing.index('| Design Timing Summary')
    end=timing.index('| Intra Clock Table',start)
    excerpt='\n'.join(timing.splitlines()[:12])+'\n\n'+timing[start:end]
    screenshot('timing_report','Four-lane shared PLA: routed timing',
               'Original Vivado report excerpt. Clock source/skew is idealized in this OOC comparison; external IO paths are excluded.',
               '<section><pre>'+html.escape(excerpt)+'</pre></section>',height=1050)
    utilization=(ROOT/'reports/synthesis/w4_impl2_utilization.rpt').read_text()
    start=re.search(r'^1\. CLB Logic\n-+\n',utilization,re.M).start()
    end=utilization.index('1.1 Summary of Registers',start)
    excerpt='\n'.join(utilization.splitlines()[:12])+'\n\n'+utilization[start:end]
    screenshot('utilization_report','Four-lane shared PLA: FPGA utilization',
               'Vivado reports 615 CLB LUTs after LUT combining and 498 flip-flops. The metrics JSON separately counts 723 LUT primitive cells.',
               '<section><pre>'+html.escape(excerpt)+'</pre></section>',height=1110)
    table='<section><table><thead><tr><th>Lanes</th><th>Architecture</th><th>CLB LUTs</th><th>LUT primitives</th><th>Flip-flops</th><th>Slack (ns)</th><th>Datapath (ns)</th></tr></thead><tbody>'
    for r in rows:
        table+=f"<tr><td>{r['width']}</td><td>{NAMES[r['implementation']]}</td><td>{r['clb_luts']}</td><td>{r['luts']}</td><td>{r['flip_flops']}</td><td>{r['worst_slack_ns']:.3f}</td><td>{r['critical_datapath_ns']:.3f}</td></tr>"
    table+='</tbody></table></section><p class="note">CLB LUT counts account for LUT combining; primitive cell counts do not. All nine runs met the 10 ns constraint under the documented OOC clock model. No physical-board measurements or maximum-frequency claims.</p>'
    screenshot('benchmark_results','Nine routed FPGA comparisons',
               'Vivado 2026.1 · Alveo U50 · RV32I · 100 MHz constraint · Identical registered boundaries',table,height=900)

def main():
    OUT.mkdir(parents=True,exist_ok=True); EVIDENCE.mkdir(parents=True,exist_ok=True)
    rows=read_metrics()
    architecture(); comparisons(rows); waveform(); evidence_screenshots(rows)
    manifest={'source':'Original reports and XSim VCD; no invented measurements',
              'screenshots':'Headless Chromium screenshots of report excerpts rendered in HTML, not Vivado GUI captures',
              'source_sha256':{str(p.relative_to(ROOT)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest()
                  for p in sorted((ROOT/'reports/synthesis').glob('*')) if p.is_file()},
              'waveform_sha256':hashlib.sha256((EVIDENCE/'pipeline_waveform.vcd').read_bytes()).hexdigest(),
              'measurement_rows':rows}
    (OUT/'provenance.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print('Created architecture, comparison, waveform, and four report screenshots.')

if __name__=='__main__': main()
