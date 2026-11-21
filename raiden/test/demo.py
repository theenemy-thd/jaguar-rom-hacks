import sys;sys.path.insert(0,'/home/claude/raiden/test');from menu import *
P=0x57b34;A4=0x45150
def demo_trace(rom,opts=None,frames=16000):
    v=VJ(rom)
    if opts is not None: menu(v,opts)
    tr=[];cur=None;demos=[]
    for f in range(frames):
        v.run(1)
        d=v.ram(A4+0x3486,1)[0]
        if d and cur is None: cur=[]
        if d: cur.append(v.ram(P+0xe,4).hex()+v.ram(P+0x742,2).hex()+v.ram(P+0x73c,4).hex())
        if not d and cur is not None: demos.append(cur); cur=None
    return demos
a=demo_trace(sys.argv[1],eval(sys.argv[3])); b=demo_trace(sys.argv[2],eval(sys.argv[4]))
print('demos',len(a),len(b))
for i,(x,y) in enumerate(zip(a,b)):
    print(i,'len',len(x),len(y),'identical',x==y,'final',x[-1],y[-1])
