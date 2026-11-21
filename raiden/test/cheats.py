import sys;sys.path.insert(0,'/home/claude/raiden/test');from menu import *
P=0x57b34; A4=0x45150
def run(opts,frames=3000,bomb=False,tag=''):
    v=VJ('/home/claude/raiden/t.j64'); to_game(v,opts)
    deaths=0;prev=0;lives=[];bombs=[]
    for f in range(frames):
        btn=['B']
        if bomb and f%200==0: btn.append('C')
        v.run(1,btn)
        st=v.ram(P+0x759,1)[0]
        if st and not prev: deaths+=1
        prev=st
        if f%500==0: lives.append(v.ram(P+0x742,1)[0]); bombs.append(v.ram(P+0x743,1)[0])
    v.shot('/home/claude/raiden/c_%s.png'%tag)
    return dict(deaths=deaths,lives=lives,bombs=bombs,power=v.ram(P+0x74c,1)[0],stage=v.ram(A4+0x3442,1)[0],gameover_lives=v.ram(P+0x742,1)[0])
if __name__=='__main__':
    for tag,o,b in [('inv',(0,0,1,0,0,1),False),('none',(0,0,0,0,0,1),False)]:
        print(tag,run(o,bomb=b,tag=tag),flush=True)
