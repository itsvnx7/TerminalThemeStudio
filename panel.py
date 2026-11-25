"""Local system-information startup panel. No network calls or third-party packages."""
import ctypes, getpass, json, os, platform, shutil, socket, sys
from pathlib import Path

PALETTE={'purple':'38;2;192;132;252','blue':'38;2;96;165;250','white':'38;2;82;82;91','black':'38;2;180;180;190'}

def memory():
    class Memory(ctypes.Structure):
        _fields_=[('length',ctypes.c_ulong),('load',ctypes.c_ulong)]+[(x,ctypes.c_ulonglong) for x in ('total','available','page_total','page_avail','virtual_total','virtual_avail','ext')]
    m=Memory(); m.length=ctypes.sizeof(m)
    if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m)): return 'Unavailable'
    return f'{(m.total-m.available)/2**30:.1f} / {m.total/2**30:.1f} GB ({m.load}%)'

def hardware():
    import winreg as w
    cpu=platform.processor() or platform.machine(); gpus=[]
    try:
        with w.OpenKey(w.HKEY_LOCAL_MACHINE,r'HARDWARE\DESCRIPTION\System\CentralProcessor\0') as k: cpu=w.QueryValueEx(k,'ProcessorNameString')[0].strip()
    except OSError: pass
    try:
        with w.OpenKey(w.HKEY_LOCAL_MACHINE,r'HARDWARE\DEVICEMAP\VIDEO') as k:
            i=0
            while True:
                try: _,v,_=w.EnumValue(k,i); i+=1
                except OSError: break
                if not isinstance(v,str) or not v.lower().startswith('\\registry\\machine\\'): continue
                try:
                    with w.OpenKey(w.HKEY_LOCAL_MACHINE,v[len('\\registry\\machine\\'):]) as a:
                        s=w.QueryValueEx(a,'HardwareInformation.AdapterString')[0]
                        if isinstance(s,bytes): s=s.decode('utf-16-le',errors='ignore').rstrip('\0')
                        if isinstance(s,str) and s.strip() and s not in gpus: gpus.append(s)
                except OSError: pass
    except OSError: pass
    return cpu, ', '.join(gpus) or 'Unavailable'

def show():
    if os.name!='nt' or not sys.stdout.isatty(): return
    c=json.loads((Path(__file__).parent/'panel-config.json').read_text(encoding='utf-8'))
    if not c['startup_panel']: return
    color='\x1b['+PALETTE[c['theme']]+'m'; reset='\x1b[0m'; e='\x1b[1m'
    if hasattr(sys.stdout,'reconfigure'): sys.stdout.reconfigure(encoding='utf-8',errors='replace')
    cpu,gpu=hardware(); disk=shutil.disk_usage(Path.home()); seconds=ctypes.windll.kernel32.GetTickCount64
    seconds.restype=ctypes.c_ulonglong; up=seconds()//1000
    rows=[('CPU',cpu),('GPU',gpu),('Threads',str(os.cpu_count() or '?')),('RAM',memory()),('Disk',f'{disk.used/2**30:.1f} / {disk.total/2**30:.1f} GB'),('OS',f'Windows {platform.version()}'),('Shell',sys.argv[1] if len(sys.argv)>1 else 'Terminal'),('User',getpass.getuser()+'@'+socket.gethostname()),('Uptime',f'{up//3600}h {up%3600//60}m')]
    width=min(75,max(30,shutil.get_terminal_size((80,24)).columns-2)); inner=width-2
    def line(s): print(color+'│'+reset+' '+s[:inner-2].ljust(inner-2)+' '+color+'│'+reset)
    print(); print(color+'╭'+'─'*inner+'╮'+reset); line('TERMINAL  /  SYSTEM INFORMATION'); print(color+'├'+'─'*inner+'┤'+reset)
    for k,v in rows: line(f'{k:<9} {v}')
    print(color+'╰'+'─'*inner+'╯'+reset); print()

if __name__=='__main__':
    try: show()
    except Exception: pass  # A cosmetic panel must never prevent opening a shell.
