def s16(v): return v-0x10000 if v & 0x8000 else v
def dis(i, pc=0):
    op=i>>26; D=(i>>21)&31; A=(i>>16)&31; B=(i>>11)&31; d=i&0xFFFF; xo=(i>>1)&0x3FF
    if i==0x60000000: return "nop"
    if i==0x4E800020: return "blr"
    if i==0x4E800021: return "blrl"
    if i==0x7C0802A6: return "mflr r0"
    if op==31 and xo==339 and ((i>>11)&0x3FF)==0x100: return "mflr r%d"%D
    if op==31 and xo==467 and ((i>>11)&0x3FF)==0x100: return "mtlr r%d"%D
    if op==14: return ("li r%d, %d"%(D,s16(d))) if A==0 else "addi r%d, r%d, %s0x%X"%(D,A,'-' if s16(d)<0 else '',abs(s16(d)))
    if op==15: return ("lis r%d, 0x%X"%(D,d)) if A==0 else "addis r%d, r%d, 0x%X"%(D,A,d)
    if op==24: return "nop" if i==0x60000000 else "ori r%d, r%d, 0x%X"%(A,D,d)
    if op==25: return "oris r%d, r%d, 0x%X"%(A,D,d)
    if op==32: return "lwz r%d, %s0x%X(r%d)"%(D,'-' if s16(d)<0 else '',abs(s16(d)),A)
    if op==33: return "lwzu r%d, %s0x%X(r%d)"%(D,'-' if s16(d)<0 else '',abs(s16(d)),A)
    if op==34: return "lbz r%d, %s0x%X(r%d)"%(D,'-' if s16(d)<0 else '',abs(s16(d)),A)
    if op==36: return "stw r%d, %s0x%X(r%d)"%(D,'-' if s16(d)<0 else '',abs(s16(d)),A)
    if op==37: return "stwu r%d, %s0x%X(r%d)"%(D,'-' if s16(d)<0 else '',abs(s16(d)),A)
    if op==38: return "stb r%d, %s0x%X(r%d)"%(D,'-' if s16(d)<0 else '',abs(s16(d)),A)
    if op==40: return "lhz r%d, %s0x%X(r%d)"%(D,'-' if s16(d)<0 else '',abs(s16(d)),A)
    if op==42: return "lha r%d, %s0x%X(r%d)"%(D,'-' if s16(d)<0 else '',abs(s16(d)),A)
    if op==44: return "sth r%d, %s0x%X(r%d)"%(D,'-' if s16(d)<0 else '',abs(s16(d)),A)
    if op==46: return "lmw r%d, %s0x%X(r%d)"%(D,'-' if s16(d)<0 else '',abs(s16(d)),A)
    if op==47: return "stmw r%d, %s0x%X(r%d)"%(D,'-' if s16(d)<0 else '',abs(s16(d)),A)
    if op==11: return "cmpwi r%d, %d"%(A,s16(d))
    if op==10: return "cmplwi r%d, 0x%X"%(A,d)
    if op==7:  return "mulli r%d, r%d, %d"%(D,A,s16(d))
    if op==21:
        MB=(i>>6)&31; ME=(i>>1)&31; SH=(i>>11)&31
        if MB==0 and ME==31: return "rotlwi r%d, r%d, %d"%(A,D,SH)
        return "rlwinm r%d, r%d, %d, %d, %d"%(A,D,SH,MB,ME)
    if op in (16,18):
        if op==18:
            li=i&0x03FFFFFC
            if li&0x02000000: li-=0x04000000
            t=(pc+li)&0xFFFFFFFF if not (i&2) else li
            return "%s 0x%08X"%("bl" if i&1 else "b", t)
        bd=i&0xFFFC
        if bd&0x8000: bd-=0x10000
        BO=(i>>21)&31; BI=(i>>16)&31
        nm={(12,2):"beq",(4,2):"bne",(12,0):"blt",(4,0):"bge",(12,1):"bgt",(4,1):"ble"}.get((BO,BI&3),"bc")
        return "%s 0x%08X"%(nm,(pc+bd)&0xFFFFFFFF)
    if op==31:
        if xo==444: return ("mr r%d, r%d"%(A,D)) if D==B else "or r%d, r%d, r%d"%(A,D,B)
        if xo==266: return "add r%d, r%d, r%d"%(D,A,B)
        if xo==40:  return "subf r%d, r%d, r%d"%(D,A,B)
        if xo==316: return "xor r%d, r%d, r%d"%(A,D,B)
        if xo==28:  return "and r%d, r%d, r%d"%(A,D,B)
        if xo==26:  return "cntlzw r%d, r%d"%(A,D)
        if xo==24:  return "slw r%d, r%d, r%d"%(A,D,B)
        if xo==536: return "srw r%d, r%d, r%d"%(A,D,B)
        if xo==23:  return "lwzx r%d, r%d, r%d"%(D,A,B)
        if xo==151: return "stwx r%d, r%d, r%d"%(D,A,B)
        if xo==279: return "lhzx r%d, r%d, r%d"%(D,A,B)
        if xo==407: return "sthx r%d, r%d, r%d"%(D,A,B)
        if xo==0:   return "cmpw r%d, r%d"%(A,B)
        if xo==32:  return "cmplw r%d, r%d"%(A,B)
    return ".long 0x%08X"%i
