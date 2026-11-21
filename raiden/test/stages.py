import sys;sys.path.insert(0,'/home/claude/raiden/test');from menu import *
P=0x57b34;A4=0x45150
rom=sys.argv[1]
bad=[]
for st in range(8):
    v=VJ(rom); to_game(v,(0,0,1,1,st,1)); 
    ok=True; seen=set()
    for f in range(4000):
        v.run(1,['B'] if f%7<4 else [])
        if f%250==0:
            z=v.ram(0x2000,0xf00)+v.ram(0x2f20,0xe0)
            if any(z): ok=False
            seen.add(v.ram(A4+0x3442,1)[0])
    v.shot('/home/claude/raiden/st%d.png'%(st+1))
    print('start',st+1,'stages seen',sorted(seen),'lives',v.ram(P+0x742,1)[0],'ram2000 clean',ok,'hooks intact',v.ram(0x1fb12,2).hex(),flush=True)
