import sys;sys.path.insert(0,'/home/claude/raiden/test');from menu import *
P=0x57b34
def hs_run(rom,opts,save=None,tag='x'):
    v=VJ(rom,save=save); to_game(v,opts); v.run(800)
    v.poke(P+0x742,[1]); v.poke(P+0x767,[0]); v.poke(P+0x73c,[0x00,0x50,0x00,0x00])
    e0=v.save()
    shots=[]
    for f in range(9000):
        # stay idle until something; press B every 40 frames for name entry
        v.run(1,['B'] if f%40<3 else [])
        if f%1500==0: v.shot('/home/claude/raiden/hs_%s_%d.png'%(tag,f)); 
    tbl=v.ram(0x24850,90)
    return v,e0,v.save(),tbl
if __name__=='__main__':
    rom=sys.argv[1]
    for tag,o in [('clean',(0,0,0,0,0,1)),('cheat',(0,0,0,1,0,1))]:
        v,e0,e1,tbl=hs_run(rom,o,tag=tag)
        print(tag,'eeprom changed',e0!=e1,'table',[tbl[i*9:i*9+3]+b':'+tbl[i*9+3:i*9+7].hex().encode() for i in range(10)][:3],flush=True)
        open('/home/claude/raiden/eep_%s.bin'%tag,'wb').write(e1)
