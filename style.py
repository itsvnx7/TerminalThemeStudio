"""Window chrome and reversible shell appearance settings."""
import copy, getpass, json, os, re, shutil, subprocess, sys, codecs
from pathlib import Path

WINDOW_NAME = 'Terminal Theme Studio Glass'
GLOBAL = ('theme','useAcrylicInTabRow','showTabsInTitlebar','tabWidthMode','compatibility.enableUnfocusedAcrylic')
PROFILE = ('tabColor','font','padding','cursorShape','scrollbarState')
CMD_GUID = '{0caa0dad-35be-5f56-a8ff-afceeeaa6101}'
MARK = '# >>> Terminal Theme Studio >>>'
END = '# <<< Terminal Theme Studio <<<'
COLORS = {'purple':('#7C3AED','#C026D3','#4338CA','#0E7490'), 'blue':('#0369A1','#2563EB','#164E63','#0E7490'), 'white':('#52525B','#71717A','#334155','#0E7490'), 'black':('#3F3F46','#52525B','#27272A','#475569')}

def cfg_extra(c):
    for k,default in {'glass_titlebar':True,'custom_prompt':True,'startup_panel':True,'powerline':True}.items():
        c.setdefault(k,default)
        if type(c[k]) is not bool: raise ValueError(k+' must be true or false')
    c.setdefault('font_face','Cascadia Code PL')
    if not isinstance(c['font_face'],str) or not c['font_face'].strip(): raise ValueError('font_face must be a nonempty string')
    return c

def restore_keys(a,b,keys):
    for k in keys:
        if k in b: a[k]=copy.deepcopy(b[k])
        else: a.pop(k,None)

def chrome(doc,c,default,items,s,state_dir):
    bg=s['background']; glass=c['glass_titlebar']
    # Acrylic tab row has native 50% opacity; transparent theme layer lets it show.
    row='#00000000' if glass else bg+'FF'
    obj={'name':WINDOW_NAME,'window':{'applicationTheme':'light' if c['theme']=='white' else 'dark','useMica':False},'tab':{'background':'terminalBackground','unfocusedBackground':'#00000000','showCloseButton':'hover'},'tabRow':{'background':row,'unfocusedBackground':row}}
    themes=doc.setdefault('themes',[])
    if not isinstance(themes,list): raise ValueError('Unexpected themes structure')
    doc['themes']=[x for x in themes if not isinstance(x,dict) or x.get('name')!=WINDOW_NAME]+[obj]
    doc.update(theme=WINDOW_NAME,useAcrylicInTabRow=glass,showTabsInTitlebar=True,tabWidthMode='titleLength')
    doc['compatibility.enableUnfocusedAcrylic']=True
    for p in [default,*items]:
        p.pop('tabColor',None)
        font=p.get('font',{})
        p['font']={**(font if isinstance(font,dict) else {}),'face':c['font_face']}
        p.update(padding='12, 10, 12, 10',cursorShape='bar',scrollbarState='hidden')
    # A dedicated CMD profile startup command, not a global CMD AutoRun hook.
    cmd=next((p for p in items if str(p.get('guid','')).lower()==CMD_GUID),None)
    if cmd is not None:
        command=cmd.get('commandline','')
        generated=cmd_command(state_dir)
        standard=not command or re.fullmatch(r'(?i)"?(?:(?:%SystemRoot%|%windir%|[A-Z]:\\Windows)\\System32\\)?cmd(?:\.exe)?"?',command.strip())
        if c['startup_panel'] and (standard or command==generated): cmd['commandline']=generated
        elif command==generated: cmd.pop('commandline',None)
        elif c['startup_panel']: print('Notice: custom CMD launch command preserved; startup panel skipped for that profile.')
    elif c['startup_panel']:
        items.append({'guid':CMD_GUID,'commandline':cmd_command(state_dir)})
    return doc

def cmd_command(state_dir):
    return '%SystemRoot%\\System32\\cmd.exe /k call "'+str(state_dir/'startup.cmd')+'"'

def restore_chrome(doc,original,default,items,old_default,old_items,profile_id,state_dir):
    restore_keys(doc,original,GLOBAL)
    if 'themes' in doc:
        doc['themes']=[x for x in doc['themes'] if not isinstance(x,dict) or x.get('name')!=WINDOW_NAME]
        doc['themes'].extend(copy.deepcopy(x) for x in original.get('themes',[]) if isinstance(x,dict) and x.get('name')==WINDOW_NAME)
        if not doc['themes'] and 'themes' not in original: doc.pop('themes')
    restore_keys(default,old_default,PROFILE)
    lookup={profile_id(p):p for p in old_items}
    for p in items[:]:
        old=lookup.get(profile_id(p),{})
        restore_keys(p,old,PROFILE)
        if str(p.get('guid','')).lower()==CMD_GUID and p.get('commandline')==cmd_command(state_dir):
            restore_keys(p,old,('commandline',))
            if not old and set(p)=={'guid'}: items.remove(p)
    return doc

def rgb(h): return ';'.join(str(int(h[i:i+2],16)) for i in (1,3,5))

def prompt_cmd(c):
    a,b,d,t=map(rgb,COLORS[c['theme']]); arrow='\ue0b0' if c['powerline'] else '|'
    # CMD expands $E to ESC, $P to live path, $T to live time, and $_ to newline.
    user=getpass.getuser().replace('$','$$')
    user=''.join(ch for ch in user if ord(ch)>=32 and ord(ch)!=127)
    return f'$E[38;2;255;255;255;48;2;{a}m {user} $E[38;2;{a};48;2;{b}m{arrow}$E[38;2;255;255;255m $P $E[38;2;{b};48;2;{t}m{arrow}$E[38;2;255;255;255m CMD $T $E[0m$E[38;2;{t}m{arrow}$E[0m$_$E[38;2;{a}m$G$E[0m '

def reg_get():
    import winreg as w
    try:
        with w.OpenKey(w.HKEY_CURRENT_USER,'Environment') as k:
            v,t=w.QueryValueEx(k,'PROMPT'); return [v,t]
    except FileNotFoundError: return None

def reg_prompt(value):
    import winreg as w
    with w.CreateKeyEx(w.HKEY_CURRENT_USER,'Environment',0,w.KEY_SET_VALUE) as k:
        if value is None:
            try: w.DeleteValue(k,'PROMPT')
            except FileNotFoundError: pass
        else: w.SetValueEx(k,'PROMPT',0,value[1],value[0])
    import ctypes
    # Notify Explorer of the user environment update. Existing shells retain their environment.
    result=ctypes.c_size_t()
    send=ctypes.windll.user32.SendMessageTimeoutW
    send.argtypes=[ctypes.c_void_p,ctypes.c_uint,ctypes.c_size_t,ctypes.c_wchar_p,ctypes.c_uint,ctypes.c_uint,ctypes.POINTER(ctypes.c_size_t)]
    send.restype=ctypes.c_ssize_t
    send(0xffff,0x1a,0,'Environment',2,1000,ctypes.byref(result))

def ps_profiles():
    # Resolve actual console profile paths, including redirected Documents folders.
    result=[]
    for name in ('powershell.exe','pwsh.exe'):
        exe=shutil.which(name)
        if not exe: continue
        try:
            p=subprocess.run([exe,'-NoLogo','-NoProfile','-NonInteractive','-Command','[Console]::OutputEncoding = [System.Text.Encoding]::UTF8; $PROFILE.CurrentUserCurrentHost'],capture_output=True,timeout=8,check=True)
            s=p.stdout.decode('utf-8-sig').strip()
            if s and Path(s).is_absolute() and Path(s).suffix.lower()=='.ps1': result.append(Path(s))
        except (OSError,subprocess.SubprocessError,UnicodeError) as e: print('Notice: could not find profile for',name,e)
    return list(dict.fromkeys(result))

def decode_profile(raw):
    if raw.startswith(codecs.BOM_UTF16_LE): return raw.decode('utf-16'),'utf-16'
    if raw.startswith(codecs.BOM_UTF16_BE): return raw.decode('utf-16-be').lstrip('\ufeff'),'utf-16-be-bom'
    if raw.startswith(codecs.BOM_UTF8): return raw.decode('utf-8-sig'),'utf-8-sig'
    try: return raw.decode('utf-8'),'utf-8'
    except UnicodeError: return raw.decode('mbcs'),'mbcs'

def encode_profile(text,enc):
    return codecs.BOM_UTF16_BE+text.encode('utf-16-be') if enc=='utf-16-be-bom' else text.encode(enc)

def ps_block_removed(text):
    return re.sub(r'(?m)^'+re.escape(MARK)+r'\r?\n[\s\S]*?^'+re.escape(END)+r'(?:\r?\n|$)','',text)

def ps_quote(s): return "'"+str(s).replace("'","''")+"'"

def ps_source(c,root):
    a,b,d,t=map(rgb,COLORS[c['theme']]); arrow='[char]0xe0b0' if c['powerline'] else "'|'"
    prompt=r'''
function global:prompt {
    $lastOk = $?
    $e = [char]27
    $a = '__A__'; $b = '__B__'; $t = '__T__'; $arrow = __ARROW__
    $where = $ExecutionContext.SessionState.Path.CurrentLocation.Path
    $clock = Get-Date -Format 'HH:mm:ss'
    $user = $env:USERNAME
    $h = Get-History -Count 1
    $elapsed = if ($h) { ('{0:0.00}s' -f ($h.EndExecutionTime - $h.StartExecutionTime).TotalSeconds) } else { '0.00s' }
    $reset = "$e[0m"
    $s = "$e[38;2;255;255;255;48;2;${a}m $user $e[38;2;${a};48;2;${b}m$arrow$e[38;2;255;255;255m $where $e[38;2;${b};48;2;${t}m$arrow$e[38;2;255;255;255m PS $elapsed | $clock $reset$e[38;2;${t}m$arrow$reset"
    $sign = if ($lastOk) { "$e[38;2;${a}m>" } else { "$e[91m>" }
    return "$s`n$sign$reset "
}
'''.replace('__A__',a).replace('__B__',b).replace('__T__',t).replace('__ARROW__',arrow)
    # No execution-policy changes; profile respects Windows policy.
    s="if ($Host.Name -eq 'ConsoleHost' -and $env:WT_SESSION -and -not [Console]::IsOutputRedirected) {\n"
    if c['custom_prompt']: s+=prompt
    if c['startup_panel']:
        s+=f"    if (-not [Console]::IsInputRedirected -and [Environment]::GetCommandLineArgs() -notmatch '^-(?:NonInteractive|Command|File|EncodedCommand|c|f)$') {{\n        try {{ & {ps_quote(sys.executable)} {ps_quote(root/'panel.py')} PowerShell }} catch {{ }}\n    }}\n".replace("[Environment]::GetCommandLineArgs() -notmatch '^-(?:NonInteractive|Command|File|EncodedCommand|c|f)$'","-not ([Environment]::GetCommandLineArgs() -match '^-(?:NonInteractive|Command|File|EncodedCommand|c|f)$')")
    return s+'}\n'

def shell_apply(c,state,root,write_json,state_file,atomic):
    import winreg as w
    sh=state.setdefault('shell',{'prompt_saved':False,'profiles':{}})
    if c['custom_prompt']:
        if not sh['prompt_saved']:
            sh['prompt_original']=reg_get(); sh['prompt_saved']=True
        value=[prompt_cmd(c),w.REG_SZ]; sh['prompt_applied']=value
        write_json(state_file,state); reg_prompt(value)
    else: restore_prompt(sh)
    # Copy helper to stable per-user location so extracted folder can be moved.
    atomic(root/'panel.py',(Path(__file__).parent/'panel.py').read_bytes())
    write_json(root/'panel-config.json',{'theme':c['theme'],'startup_panel':c['startup_panel']})
    # /k starts an interactive CMD, so a panel never runs from CMD /c automation.
    exe=str(Path(sys.executable)); helper=str(root/'panel.py')
    if any(x in exe+helper for x in '%\r\n"'): raise ValueError('Unsupported character in Python or helper path')
    bat='@echo off\r\n'+('"'+exe+'" "'+helper+'" CMD\r\n' if c['startup_panel'] else '')
    atomic(root/'startup.cmd',bat.encode('utf-8'))
    atomic(root/'shell.ps1',ps_source(c,root).encode('utf-8-sig'))
    if not (c['startup_panel'] or c['custom_prompt']): restore_profiles(sh,atomic); write_json(state_file,state); return
    for p in ps_profiles():
        raw=p.read_bytes() if p.exists() else b''
        txt,enc=decode_profile(raw)
        if '# SIG # Begin signature block' in txt:
            print('Notice: signed PowerShell profile left unchanged:',p); continue
        if str(p) not in sh['profiles']:
            import hashlib
            b=root/('profile-'+hashlib.sha256(str(p).encode()).hexdigest()[:16]+'.bak')
            atomic(b,raw); sh['profiles'][str(p)]={'backup':str(b),'existed':p.exists()}; write_json(state_file,state)
        txt=ps_block_removed(txt)
        if txt and not txt.endswith('\n'): txt+='\n'
        block=MARK+'\nif ($env:WT_SESSION -and (Test-Path -LiteralPath '+ps_quote(root/'shell.ps1')+')) { . '+ps_quote(root/'shell.ps1')+' }\n'+END+'\n'
        atomic(p,encode_profile(txt+block,enc))
    write_json(state_file,state)

def restore_prompt(sh):
    if sh.get('prompt_saved'):
        if reg_get()==sh.get('prompt_applied'): reg_prompt(sh.get('prompt_original'))
        else: print('Notice: PROMPT changed outside Studio; preserving it.')
        sh['prompt_saved']=False

def restore_profiles(sh,atomic):
    for filename,entry in list(sh.get('profiles',{}).items()):
        p=Path(filename)
        if not p.exists(): continue
        raw=p.read_bytes(); txt,enc=decode_profile(raw); clean=ps_block_removed(txt)
        if clean==txt: continue
        original=Path(entry['backup']).read_bytes()
        orig,_=decode_profile(original)
        if clean.rstrip('\r\n')==orig.rstrip('\r\n'):
            if entry['existed']: atomic(p,original)
            else: p.unlink()
        else: atomic(p,encode_profile(clean,enc))
    sh['profiles']={}

def shell_restore(state,atomic):
    sh=state.get('shell',{})
    restore_prompt(sh); restore_profiles(sh,atomic)
