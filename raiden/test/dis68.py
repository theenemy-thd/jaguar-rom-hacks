import capstone,sys
md=capstone.Cs(capstone.CS_ARCH_M68K,capstone.CS_MODE_BIG_ENDIAN|capstone.CS_MODE_M68K_000)
def dis(d,base,addr,n):
    out=[]
    for i in md.disasm(d[addr-base:addr-base+n],addr): out.append('%06X  %-24s %s %s'%(i.address,i.bytes.hex(),i.mnemonic,i.op_str))
    return '\n'.join(out)
if __name__=='__main__':
    f,base,addr,n=sys.argv[1],int(sys.argv[2],16),int(sys.argv[3],16),int(sys.argv[4],16)
    print(dis(open(f,'rb').read(),base,addr,n))
