import ctypes as C, os, sys, struct, zlib
CORE=os.environ.get('VJCORE','/home/claude/vj_test.so')
# retropad ids
U,D,L,R,A,B,Cc,PAUSE,OPTION=4,5,6,7,8,0,1,2,3  # B=0? see below
JP={'B':0,'Y':1,'SELECT':2,'START':3,'UP':4,'DOWN':5,'LEFT':6,'RIGHT':7,'A':8,'X':9,'L':10,'R':11}
# Jaguar: A->A(8), B->B(0), C->Y(1), PAUSE->SELECT(2), OPTION->START(3)
JAG={'A':8,'B':0,'C':1,'PAUSE':2,'OPTION':3,'U':4,'D':5,'L':6,'R':7}
class retro_game_info(C.Structure):
    _fields_=[('path',C.c_char_p),('data',C.c_void_p),('size',C.c_size_t),('meta',C.c_char_p)]
class retro_variable(C.Structure):
    _fields_=[('key',C.c_char_p),('value',C.c_char_p)]
ENVCB=C.CFUNCTYPE(C.c_bool,C.c_uint,C.c_void_p)
VIDCB=C.CFUNCTYPE(None,C.c_void_p,C.c_uint,C.c_uint,C.c_size_t)
AUDCB=C.CFUNCTYPE(None,C.c_int16,C.c_int16)
AUDBCB=C.CFUNCTYPE(C.c_size_t,C.c_void_p,C.c_size_t)
POLLCB=C.CFUNCTYPE(None)
INCB=C.CFUNCTYPE(C.c_int16,C.c_uint,C.c_uint,C.c_uint,C.c_uint)
SYSDIR=b'/home/claude/raiden/sys'
os.makedirs(SYSDIR,exist_ok=True)
class VJ:
    def __init__(s,rom,save=None):
        s.lib=C.CDLL(CORE)
        s.buttons=set(); s.frame=None; s.w=s.h=s.pitch=0
        s._sysdir=C.c_char_p(SYSDIR)
        def env(cmd,data):
            if cmd==9 or cmd==31:  # SYSTEM_DIRECTORY / SAVE_DIRECTORY
                C.cast(data,C.POINTER(C.c_char_p))[0]=s._sysdir.value; return True
            if cmd==10: return True  # pixel format
            if cmd==15:  # GET_VARIABLE
                v=C.cast(data,C.POINTER(retro_variable))[0]; return False
            if cmd==27: return False
            return False
        def vid(d,w,h,p):
            if d: s.w,s.h,s.pitch=w,h,p; s.frame=C.string_at(d,p*h)
        def poll(): pass
        def inp(port,dev,idx,id):
            if port!=0: return 0
            if id==256:
                m=0
                for b in s.buttons: m|=1<<JAG[b]
                return m
            return 1 if any(JAG[b]==id for b in s.buttons) else 0
        s._cbs=[ENVCB(env),VIDCB(vid),AUDCB(lambda a,b:None),AUDBCB(lambda d,n:n),POLLCB(poll),INCB(inp)]
        s.lib.retro_set_environment(s._cbs[0]); s.lib.retro_set_video_refresh(s._cbs[1])
        s.lib.retro_set_audio_sample(s._cbs[2]); s.lib.retro_set_audio_sample_batch(s._cbs[3])
        s.lib.retro_set_input_poll(s._cbs[4]); s.lib.retro_set_input_state(s._cbs[5])
        s.lib.retro_init()
        data=open(rom,'rb').read() if isinstance(rom,str) else rom
        s._rom=C.create_string_buffer(data,len(data))
        gi=retro_game_info(b'/home/claude/raiden/game.j64',C.cast(s._rom,C.c_void_p),len(data),None)
        assert s.lib.retro_load_game(C.byref(gi))
        s.lib.retro_get_memory_data.restype=C.c_void_p
        s.lib.retro_get_memory_size.restype=C.c_size_t
        s.ram_p=s.lib.retro_get_memory_data(2)
        s.sav_p=s.lib.retro_get_memory_data(0); s.sav_n=s.lib.retro_get_memory_size(0)
        if save is not None and s.sav_p: C.memmove(s.sav_p,save,min(len(save),s.sav_n))
        s.lib.m68k_get_reg.restype=C.c_uint; s.lib.m68k_get_reg.argtypes=[C.c_void_p,C.c_int]
        s.n=0
    def run(s,n=1,buttons=()):
        s.buttons=set(buttons)
        for _ in range(n): s.lib.retro_run(); s.n+=1
    def ram(s,a=0,n=0x200000): return C.string_at(s.ram_p+a,n)
    def poke(s,a,b): C.memmove(s.ram_p+a,bytes(b),len(b))
    def save(s): return C.string_at(s.sav_p,s.sav_n) if s.sav_p else b''
    def pc(s): return s.lib.m68k_get_reg(None,16)
    def r16(s,a): return struct.unpack('>H',s.ram(a,2))[0]
    def r32(s,a): return struct.unpack('>I',s.ram(a,4))[0]
    def shot(s,path):
        w,h,p=s.w,s.h,s.pitch; f=s.frame
        raw=b''.join(b'\0'+bytes(x for px in range(w) for x in (f[y*p+px*4+2],f[y*p+px*4+1],f[y*p+px*4])) for y in range(h))
        def ch(t,d): c=struct.pack('>I',len(d))+t+d; return c+struct.pack('>I',zlib.crc32(t+d))
        open(path,'wb').write(b'\x89PNG\r\n\x1a\n'+ch(b'IHDR',struct.pack('>IIBBBBB',w,h,8,2,0,0,0))+ch(b'IDAT',zlib.compress(raw))+ch(b'IEND',b''))
