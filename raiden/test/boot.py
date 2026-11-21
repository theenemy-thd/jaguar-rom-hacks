import sys;sys.path.insert(0,'/home/claude/raiden/test');from vj import *
def to_game(v,log=False):
    v.run(2100)
    for k in range(6):
        v.run(5,['B']); v.run(60)
        if log: v.shot('/home/claude/raiden/g%d.png'%k)
