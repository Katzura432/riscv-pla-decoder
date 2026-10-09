"""Independent opcode-oriented RV32I/M oracle; never reads the CSV or generator."""
NAMES = ('LUI AUIPC JAL JALR BEQ BNE BLT BGE BLTU BGEU LB LH LW LBU LHU SB SH SW '
         'ADDI SLTI SLTIU XORI ORI ANDI SLLI SRLI SRAI ADD SUB SLL SLT SLTU XOR SRL SRA OR AND '
         'FENCE ECALL EBREAK MUL MULH MULHSU MULHU DIV DIVU REM REMU').split()
IDS = {name:i+1 for i,name in enumerate(NAMES)}
ALU = {n:i for i,n in enumerate('PASS ADD SUB SLL LT LTU XOR SRL SRA OR AND EQ NE GE GEU MUL MULH MULHSU MULHU DIV DIVU REM REMU'.split())}

def sext(n, width):
    return (n - (1 << width) if n & (1 << (width-1)) else n) & 0xffffffff

def identify(insn, enable_m=False):
    op, f3, f7 = insn & 127, (insn>>12)&7, insn>>25
    if op == 0x37: return 'LUI'
    if op == 0x17: return 'AUIPC'
    if op == 0x6f: return 'JAL'
    if op == 0x67 and f3 == 0: return 'JALR'
    if op == 0x63: return {0:'BEQ',1:'BNE',4:'BLT',5:'BGE',6:'BLTU',7:'BGEU'}.get(f3)
    if op == 0x03: return {0:'LB',1:'LH',2:'LW',4:'LBU',5:'LHU'}.get(f3)
    if op == 0x23: return {0:'SB',1:'SH',2:'SW'}.get(f3)
    if op == 0x13:
        if f3 == 1: return 'SLLI' if f7 == 0 else None
        if f3 == 5: return {0:'SRLI',32:'SRAI'}.get(f7)
        return {0:'ADDI',2:'SLTI',3:'SLTIU',4:'XORI',6:'ORI',7:'ANDI'}.get(f3)
    if op == 0x33:
        if f7 == 0: return ['ADD','SLL','SLT','SLTU','XOR','SRL','OR','AND'][f3]
        if f7 == 32: return {0:'SUB',5:'SRA'}.get(f3)
        if f7 == 1 and enable_m: return ['MUL','MULH','MULHSU','MULHU','DIV','DIVU','REM','REMU'][f3]
    if op == 0x0f and f3 == 0: return 'FENCE'
    if insn == 0x00000073: return 'ECALL'
    if insn == 0x00100073: return 'EBREAK'
    return None

def decode(insn, valid=True, enable_m=False):
    if not valid: return 0
    name = identify(insn, enable_m)
    if name is None: return (1<<88) | (1<<87)
    rd,rs1,rs2 = (insn>>7)&31,(insn>>15)&31,(insn>>20)&31
    fmt,unit,alu,use1,use2,write,size,unsigned,trap,serial = 0,1,'PASS',0,0,1,0,0,0,0
    if name in ['LUI','AUIPC']: fmt,alu = 5,('PASS' if name=='LUI' else 'ADD')
    elif name in ['JAL','JALR']:
        fmt,unit,alu,use1 = (6 if name=='JAL' else 2),5,'ADD',int(name=='JALR')
    elif name in ['BEQ','BNE','BLT','BGE','BLTU','BGEU']:
        fmt,unit,use1,use2,write = 4,4,1,1,0
        alu = dict(BEQ='EQ',BNE='NE',BLT='LT',BGE='GE',BLTU='LTU',BGEU='GEU')[name]
    elif name in ['LB','LH','LW','LBU','LHU']:
        fmt,unit,alu,use1 = 2,2,'ADD',1
        size = {'LB':0,'LH':1,'LW':2,'LBU':0,'LHU':1}[name]
        unsigned = int(name in ['LBU','LHU'])
    elif name in ['SB','SH','SW']:
        fmt,unit,alu,use1,use2,write = 3,3,'ADD',1,1,0
        size = {'SB':0,'SH':1,'SW':2}[name]
    elif name in ['FENCE','ECALL','EBREAK']:
        unit,write,serial = (6 if name=='FENCE' else 7),0,1
        trap = {'FENCE':0,'ECALL':1,'EBREAK':2}[name]
    else:
        is_imm = name in ['ADDI','SLTI','SLTIU','XORI','ORI','ANDI','SLLI','SRLI','SRAI']
        fmt,use1,use2 = (7 if name in ['SLLI','SRLI','SRAI'] else 2) if is_imm else 1,1,int(not is_imm)
        alu = {'ADDI':'ADD','SLTI':'LT','SLTIU':'LTU','XORI':'XOR','ORI':'OR','ANDI':'AND',
               'SLLI':'SLL','SRLI':'SRL','SRAI':'SRA','SLT':'LT','SLTU':'LTU'}.get(name,name)
        if name in NAMES[40:]: unit=8
    write = int(bool(write and rd))
    ctrl = ((1<<27)|(IDS[name]<<21)|(fmt<<18)|(unit<<14)|(ALU[alu]<<9)|
            (use1<<8)|(use2<<7)|(write<<6)|(size<<4)|(unsigned<<3)|(trap<<1)|serial)
    imm=0
    if fmt==2: imm=sext(insn>>20,12)
    if fmt==3: imm=sext(((insn>>25)<<5)|((insn>>7)&31),12)
    if fmt==4: imm=sext(((insn>>31)<<12)|(((insn>>7)&1)<<11)|(((insn>>25)&63)<<5)|(((insn>>8)&15)<<1),13)
    if fmt==5: imm=insn&0xfffff000
    if fmt==6: imm=sext(((insn>>31)<<20)|(((insn>>12)&255)<<12)|(((insn>>20)&1)<<11)|(((insn>>21)&1023)<<1),21)
    if fmt==7: imm=(insn>>20)&31
    fence=(insn>>20) if name=='FENCE' else 0
    rd=rd if write else 0 # x0 was already zero; other nonwriters have no rd.
    rs1=rs1 if use1 else 0
    rs2=rs2 if use2 else 0
    return (1<<88)|(ctrl<<59)|(rd<<54)|(rs1<<49)|(rs2<<44)|(imm<<12)|fence
