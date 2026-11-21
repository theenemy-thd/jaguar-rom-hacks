import zlib,struct
def rd(p):
    d=open(p,'rb').read();i=8;idat=b''
    while i<len(d):
        l=struct.unpack('>I',d[i:i+4])[0];t=d[i+4:i+8]
        if t==b'IHDR': w,h=struct.unpack('>II',d[i+8:i+16])
        if t==b'IDAT': idat+=d[i+8:i+8+l]
        i+=12+l
    raw=zlib.decompress(idat);return w,h,[raw[y*(w*3+1)+1:(y+1)*(w*3+1)] for y in range(h)]
def wr(out,W,H,rows):
    raw=b''.join(b'\0'+bytes(r) for r in rows)
    def ch(t,d): c=struct.pack('>I',len(d))+t+d; return c+struct.pack('>I',zlib.crc32(t+d))
    open(out,'wb').write(b'\x89PNG\r\n\x1a\n'+ch(b'IHDR',struct.pack('>IIBBBBB',W,H,8,2,0,0,0))+ch(b'IDAT',zlib.compress(raw))+ch(b'IEND',b''))
def montage(paths,out,cols=4):
    ims=[rd(p) for p in paths];w=max(i[0] for i in ims);h=max(i[1] for i in ims);rows=(len(ims)+cols-1)//cols
    W=w*cols;H=h*rows;canvas=[bytearray(W*3) for _ in range(H)]
    for k,(iw,ih,r) in enumerate(ims):
        ox=(k%cols)*w*3;oy=(k//cols)*h
        for y in range(ih): canvas[oy+y][ox:ox+iw*3]=r[y]
    wr(out,W,H,canvas)
if __name__=='__main__':
    import sys; montage(sys.argv[2:],sys.argv[1])
