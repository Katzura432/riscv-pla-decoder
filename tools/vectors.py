"""Independent oracle vectors: structural sweep, mutations, operands, random."""
import json
import random
from pathlib import Path
from reference import decode, identify, NAMES
ROOT=Path(__file__).resolve().parents[1]

def main():
    rng=random.Random(0x504c41)
    dest=ROOT/'build'
    dest.mkdir(exist_ok=True)
    count=0
    coverage={name:0 for name in NAMES}
    invalid=0
    with (dest/'vectors.txt').open('w') as out:
        def emit(insn, valid=1):
            nonlocal count,invalid
            name=identify(insn,True)
            if valid:
                if name: coverage[name]+=1
                else: invalid+=1
            out.write(f'{valid:x} {insn:08x} {decode(insn,valid,False):023x} {decode(insn,valid,True):023x}\n')
            count+=1
        # Every opcode/funct3/funct7 combination with representative operands.
        for op in range(128):
            for f3 in range(8):
                for f7 in range(128):
                    emit((f7<<25)|(9<<20)|(7<<15)|(f3<<12)|(5<<7)|op)
        # Exact SYSTEM encodings and all single-bit mutations.
        for word in [0x73,0x100073,0,0xffffffff,0x0000100f,0x30200073]:
            emit(word)
            for bit in range(32): emit(word^(1<<bit))
        # Complete I and S immediate spaces, x0 destinations, all shift encodings.
        for imm in range(4096):
            emit((imm<<20)|(3<<15)|(4<<7)|0x13)
            emit((imm<<20)|(3<<15)|(2<<12)|0x03)
            emit(((imm>>5)<<25)|(6<<20)|(3<<15)|(2<<12)|((imm&31)<<7)|0x23)
            emit((imm<<20)|0x0f)
        for f7 in range(128):
            for shamt in range(32):
                for f3 in [1,5]: emit((f7<<25)|(shamt<<20)|(3<<15)|(f3<<12)|(2<<7)|0x13)
        # Legal-biased randomized operands, x0 and lane bubbles.
        seeds=[0x37,0x17,0x6f,0x67,0x63,0x03,0x23,0x13,0x33,0x0f]
        for _ in range(40000):
            word=(rng.getrandbits(25)<<7)|rng.choice(seeds)
            emit(word, int(rng.random()>0.12))
        for _ in range(40000): emit(rng.getrandbits(32),int(rng.random()>0.12))
        # Dense legal register dependencies and M-extension operands.
        for f3 in range(8):
            for rd in range(32):
                for rs in range(32):
                    emit((1<<25)|(rs<<20)|(rs<<15)|(f3<<12)|(rd<<7)|0x33)
        while count%4: emit(0,0)
    assert all(coverage.values()),coverage
    report={'vectors':count,'valid_illegal_vectors':invalid,'instruction_coverage':coverage,
            'seed':'0x504c41','oracle':'tools/reference.py; independent of CSV and RTL generator'}
    (dest/'vector_coverage.json').write_text(json.dumps(report,indent=2)+'\n')
    print(f'Generated {count} vectors; all {len(coverage)} operations covered.')

if __name__=='__main__': main()
