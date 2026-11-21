import sys;sys.path.insert(0,'/home/claude/raiden/test');from menu import *
import boot
A4=0x45150
def lag(rom,opts,frames=6000):
    v=VJ(rom)
    if opts is None: boot.to_game(v)
    else: to_game(v,opts)
    v.run(300)
    prev=v.ram(A4+0x344b,1)[0]; logic=0; long=0; run=0
    for f in range(frames):
        v.run(1,['B'] if f%8<4 else [])
        c=v.ram(A4+0x344b,1)[0]
        run+=1
        if c<prev:
            logic+=1
            if run>2: long+=1
            run=0
        prev=c
    return logic,long
#print('clean          ',lag(sys.argv[1],None))
#print('trainer all off',lag(sys.argv[2],(0,0,0,0,0,0)))
#print('trainer AF only',lag(sys.argv[2],(0,0,0,0,0,1)))
#print('trainer all on ',lag(sys.argv[2],(1,1,1,1,0,1)))
def lag_poke(rom,opts,frames=6000):
    v=VJ(rom)
    if opts is None: boot.to_game(v)
    else: to_game(v,opts)
    v.run(300)
    prev=v.ram(A4+0x344b,1)[0]; logic=0; long=0; run=0
    for f in range(frames):
        v.poke(0x57b34+0x74c,[7])
        v.run(1,['B'] if f%8<4 else [])
        c=v.ram(A4+0x344b,1)[0]; run+=1
        if c<prev:
            logic+=1
            if run>2: long+=1
            run=0
        prev=c
    return logic,long
print('clean, power poked   ',lag_poke(sys.argv[1],None))
print('trainer, MAX POWER on',lag_poke(sys.argv[2],(0,0,0,1,0,0)))
