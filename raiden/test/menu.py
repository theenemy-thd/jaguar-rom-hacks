import sys;sys.path.insert(0,'/home/claude/raiden/test');from vj import *
VARS=0x2f00
def tap(v,b,hold=3,gap=4):
    v.run(hold,[b]); v.run(gap)
def menu(v,opts,shot=None):
    """opts: list of 6 values (lives,bombs,inv,power,stage0..7,autofire)"""
    while not (0x801000<=v.pc()<0x802000): v.run(10)
    v.run(30)
    cur=list(v.ram(VARS,6))
    for i,want in enumerate(opts):
        n=8 if i==4 else 2
        while cur[i]!=want:
            tap(v,'R'); cur=list(v.ram(VARS,6))
        tap(v,'D')
    if shot: v.shot(shot)
    tap(v,'PAUSE')
def to_game(v,opts=(0,0,0,0,0,1),shot=None):
    menu(v,opts,shot)
    v.run(1400)
    for k in range(6):
        v.run(5,['B']); v.run(60)
