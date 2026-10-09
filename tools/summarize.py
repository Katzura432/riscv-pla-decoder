"""Build a factual results document from completed tool reports."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def main():
    lines=['# Verification and routed FPGA results','']
    for file,label in [('decode_simulation.json','Decoder'),('pipeline_simulation.json','Pipeline')]:
        path=ROOT/'build'/file
        if path.exists():
            data=json.loads(path.read_text())
            lines += [f'{label}: `{json.dumps(data)}`','']
        else: lines += [f'{label}: not run.','']
    lines += ['Target: Alveo U50 xcu50-fsvh2104-2-e, RV32I, 10 ns clock; identical registered boundaries.',
              'Routed out-of-context results include dependency logic; no board measurements.',
              'Clock source/skew is idealized (HD.CLK_SRC unset); external IO routing is excluded.','',
              '| Lanes | Decoder | LUT primitives | Flip-flops | Worst slack (ns) | Critical datapath (ns) |',
              '| --- | --- | --- | --- | --- | --- |']
    names=['Direct RTL','Exact PLA','Shared PLA']
    metrics=sorted((ROOT/'build/synthesis').glob('*_metrics.json'))
    for path in metrics:
        m=json.loads(path.read_text())
        lines.append(f"| {m['width']} | {names[m['implementation']]} | {m['luts']} | {m['flip_flops']} | {m['worst_slack_ns']:.3f} | {m['critical_datapath_ns']:.3f} |")
    lines += ['',f'Completed {len(metrics)} of 9 configurations.',
              'Positive slack meets the specified 100 MHz constraint under the OOC clock model.',
              'Datapath delay alone is not measured Fmax. RTL term counts are not FPGA LUT counts.','']
    (ROOT/'RESULTS.md').write_text('\n'.join(lines))
    print('\n'.join(lines))

if __name__=='__main__': main()
