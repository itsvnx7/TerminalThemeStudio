#!/usr/bin/env python3
"""Persistent Windows Terminal themes. Python 3.9+, no third-party modules."""
import argparse
import copy
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import style

ROOT = Path(__file__).resolve().parent
CONFIG = ROOT / 'config.json'
NAME = 'Terminal Theme Studio'
KEYS = ('colorScheme', 'background', 'foreground', 'cursorColor', 'selectionBackground', 'opacity', 'useAcrylic', 'acrylicOpacity')
REG_PATH = r'Console\%%Startup'
REG_VALUES = {
    'stable': {'DelegationTerminal': '{E12CFF52-A866-4C77-9A90-F570A7AA2C6B}', 'DelegationConsole': '{2EACA947-7F5F-4CFA-BA87-8F7FBEEFBE69}'},
    'preview': {'DelegationTerminal': '{86633F1F-6454-40EC-89CE-DA4EBA977EE2}', 'DelegationConsole': '{06EC847C-C0A5-46B8-92CB-7C92F6E35CD5}'},
}
PALETTES = {
    'purple': ('#10051C','#E9D5FF','#C084FC','#581C87'),
    'blue': ('#06152D','#BFDBFE','#60A5FA','#1E40AF'),
    'white': ('#F5F5F5','#18181B','#444444','#D4D4D8'),
    'black': ('#080808','#F2F2F2','#FFFFFF','#454545'),
}
ANSI_DARK = ['#15121A','#F87171','#86EFAC','#FDE68A','#93C5FD','#C084FC','#67E8F9','#E5E7EB','#77717F','#FCA5A5','#BBF7D0','#FEF3C7','#BFDBFE','#E9D5FF','#A5F3FC','#FFFFFF']
ANSI_LIGHT = ['#18181B','#B91C1C','#166534','#854D0E','#1D4ED8','#7E22CE','#0E7490','#52525B','#71717A','#DC2626','#15803D','#A16207','#2563EB','#9333EA','#0891B2','#71717A']
ANSI_KEYS = ('black','red','green','yellow','blue','purple','cyan','white','brightBlack','brightRed','brightGreen','brightYellow','brightBlue','brightPurple','brightCyan','brightWhite')

def atomic(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix='.theme-', suffix='.tmp')
    try:
        with os.fdopen(fd, 'wb') as f:
            f.write(data)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)

def write_json(path, obj):
    atomic(path, (json.dumps(obj, indent=4, ensure_ascii=False)+'\n').encode('utf-8'))

def read_jsonc(raw):
    # Preserve quoted strings while removing JSONC comments and trailing commas.
    s = raw.decode('utf-8-sig')
    token = re.compile(r'"(?:\\.|[^"\\])*"|//[^\r\n]*|/\*[\s\S]*?\*/')
    s = token.sub(lambda m: m.group() if m.group().startswith('"') else ' ', s)
    s = re.sub(r'"(?:\\.|[^"\\])*"|,(?=\s*[}\]])', lambda m: m.group() if m.group().startswith('"') else '', s)
    return json.loads(s)

def config_load():
    cfg = json.loads(CONFIG.read_text(encoding='utf-8-sig'))
    theme = cfg.get('theme', 'purple')
    if not isinstance(theme,str) or theme.lower() not in (*PALETTES, 'off'):
        raise ValueError('theme must be purple, blue, white, black, or off')
    cfg['theme'] = theme.lower()
    n = cfg.get('opacity', 50)
    if type(n) is not int or not 0 <= n <= 100: raise ValueError('opacity must be an integer 0-100')
    cfg['opacity'] = n
    for k in ('acrylic','set_default_terminal'):
        cfg.setdefault(k, True)
        if type(cfg[k]) is not bool: raise ValueError(k+' must be true or false')
    overrides = cfg.setdefault('custom_colors', {})
    if not isinstance(overrides,dict): raise ValueError('custom_colors must be an object')
    for k,v in overrides.items():
        if k not in ('background','foreground','cursorColor','selectionBackground') or not isinstance(v,str) or not re.fullmatch(r'#[0-9a-fA-F]{6}',v):
            raise ValueError('Invalid custom color: '+str(k))
    return style.cfg_extra(cfg)

def paths(local):
    base = local / 'Packages'
    return [(kind, p) for kind,p in [
        ('stable', base/'Microsoft.WindowsTerminal_8wekyb3d8bbwe'/'LocalState'/'settings.json'),
        ('preview', base/'Microsoft.WindowsTerminalPreview_8wekyb3d8bbwe'/'LocalState'/'settings.json'),
        ('stable', local/'Microsoft'/'Windows Terminal'/'settings.json'),
        ('preview', local/'Microsoft'/'Windows Terminal Preview'/'settings.json'),
    ] if p.is_file()]

def profiles(doc):
    p = doc.setdefault('profiles', {})
    if isinstance(p,list):
        p = doc['profiles'] = {'defaults':{},'list':p}
    if not isinstance(p,dict): raise ValueError('Unexpected profiles structure')
    default = p.setdefault('defaults',{})
    items = p.setdefault('list',[])
    if not isinstance(default,dict) or not isinstance(items,list) or any(not isinstance(x,dict) for x in items):
        raise ValueError('Unexpected profile structure')
    return default, items

def profile_id(p):
    return ('guid', str(p['guid']).lower()) if 'guid' in p else ('name',p.get('name'),p.get('source'))

def scheme(cfg):
    theme = cfg['theme']
    c = dict(zip(('background','foreground','cursorColor','selectionBackground'), PALETTES[theme]))
    c.update(cfg['custom_colors'])
    return {'name':NAME, **dict(zip(ANSI_KEYS, ANSI_LIGHT if theme=='white' else ANSI_DARK)), **c}

def apply_doc(doc,cfg,state_dir=None):
    default, items = profiles(doc)
    s = scheme(cfg)
    schemes = doc.setdefault('schemes',[])
    if not isinstance(schemes,list): raise ValueError('Unexpected schemes structure')
    doc['schemes'] = [x for x in schemes if not isinstance(x,dict) or x.get('name')!=NAME] + [s]
    values = {k:s[k] for k in ('background','foreground','cursorColor','selectionBackground')}
    values.update(colorScheme=NAME, opacity=cfg['opacity'],useAcrylic=cfg['acrylic'])
    for p in [default,*items]:
        p.pop('acrylicOpacity',None)
        p.update(values)
        # Explicit unfocused overrides would otherwise change the theme on blur.
        if isinstance(p.get('unfocusedAppearance'),dict):
            for k in KEYS: p['unfocusedAppearance'].pop(k,None)
    if state_dir is not None: style.chrome(doc,cfg,default,items,s,state_dir)
    return doc

def restore_fields(target,original):
    for k in KEYS:
        if k in original: target[k]=copy.deepcopy(original[k])
        else: target.pop(k,None)
    if isinstance(target.get('unfocusedAppearance'),dict):
        old = original.get('unfocusedAppearance',{})
        if not isinstance(old,dict): old={}
        for k in KEYS:
            if k in old: target['unfocusedAppearance'][k]=copy.deepcopy(old[k])
            else: target['unfocusedAppearance'].pop(k,None)

def restore_doc(doc, original, state_dir=None):
    default,items = profiles(doc)
    old_default,old_items = profiles(copy.deepcopy(original))
    restore_fields(default,old_default)
    lookup = {profile_id(p):p for p in old_items}
    for p in items:
        old = lookup.get(profile_id(p))
        if old is not None: restore_fields(p,old)
        elif p.get('colorScheme')==NAME: restore_fields(p,{})
    doc['schemes'] = [x for x in doc.get('schemes',[]) if not isinstance(x,dict) or x.get('name')!=NAME]
    doc['schemes'].extend(copy.deepcopy(x) for x in original.get('schemes',[]) if isinstance(x,dict) and x.get('name')==NAME)
    if state_dir is not None: style.restore_chrome(doc,original,default,items,old_default,old_items,profile_id,state_dir)
    return doc

def reg_snapshot():
    import winreg as w
    result={}
    try:
        with w.OpenKey(w.HKEY_CURRENT_USER, REG_PATH) as key:
            for n in REG_VALUES['stable']:
                try:
                    v,t=w.QueryValueEx(key,n); result[n]=[v,t]
                except FileNotFoundError: result[n]=None
    except FileNotFoundError: result={n:None for n in REG_VALUES['stable']}
    return result

def reg_set(kind):
    import winreg as w
    with w.CreateKeyEx(w.HKEY_CURRENT_USER,REG_PATH,0,w.KEY_SET_VALUE) as key:
        for n,v in REG_VALUES[kind].items(): w.SetValueEx(key,n,0,w.REG_SZ,v)

def reg_restore(snapshot):
    import winreg as w
    with w.CreateKeyEx(w.HKEY_CURRENT_USER,REG_PATH,0,w.KEY_SET_VALUE) as key:
        for n,entry in snapshot.items():
            if entry is None:
                try: w.DeleteValue(key,n)
                except FileNotFoundError: pass
            else: w.SetValueEx(key,n,0,entry[1],entry[0])

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--theme',choices=[*PALETTES,'off'],help='Save and apply a theme')
    parser.add_argument('--opacity',type=int,help='Save and apply opacity, 0-100')
    parser.add_argument('--restore',action='store_true',help='Restore original appearance (same as off)')
    parser.add_argument('--dry-run',action='store_true',help='Validate and show targets without writing anything')
    args=parser.parse_args()
    if os.name!='nt': raise RuntimeError('This script is for Windows only.')
    cfg=config_load()
    if args.theme: cfg['theme']=args.theme
    if args.restore: cfg['theme']='off'
    if args.opacity is not None:
        if not 0<=args.opacity<=100: raise ValueError('opacity must be 0-100')
        cfg['opacity']=args.opacity
    local=Path(os.environ['LOCALAPPDATA'])
    state_dir=local/'TerminalThemeStudio'
    state_file=state_dir/'state.json'
    state=json.loads(state_file.read_text(encoding='utf-8')) if state_file.exists() else {'files':{},'registry':None}
    targets=paths(local)
    off=cfg['theme']=='off'
    if not off and not targets:
        raise RuntimeError('No Windows Terminal settings found. Install Windows Terminal, open it once, then run this script again.')
    operations=[]
    if off:
        for filename,backup in state['files'].items():
            p=Path(filename); b=Path(backup)
            if not p.exists():
                print('Skipped missing settings:',p); continue
            raw=p.read_bytes(); original=read_jsonc(b.read_bytes())
            operations.append((p,raw,restore_doc(read_jsonc(raw),original,state_dir)))
    else:
        for kind,p in targets:
            raw=p.read_bytes(); operations.append((p,raw,apply_doc(read_jsonc(raw),cfg,state_dir)))
    print(f"Theme: {cfg['theme']} | Opacity: {cfg['opacity']}% | Acrylic: {cfg['acrylic']}")
    for p,_,_ in operations: print('  ',p)
    if args.dry_run:
        print('Dry run: nothing changed.'); return
    # Save originals once per theme cycle, before modifying any settings.
    if not off:
        for i,(p,raw,_) in enumerate(operations):
            if str(p) not in state['files']:
                import hashlib
                b=state_dir/('original-'+hashlib.sha256(str(p).encode()).hexdigest()[:16]+'.jsonc')
                atomic(b,raw); state['files'][str(p)]=str(b)
        if cfg['set_default_terminal'] and state['registry'] is None:
            state['registry']=reg_snapshot()
        write_json(state_file,state)
    if not off: style.shell_apply(cfg,state,state_dir,write_json,state_file,atomic)
    for p,raw,doc in operations:
        if p.read_bytes()!=raw: raise RuntimeError('Settings changed while running. Run the script again: '+str(p))
        write_json(p,doc)
    if off:
        style.shell_restore(state,atomic)
        if state['registry'] is not None: reg_restore(state['registry'])
        # Keep backup files available, but start a fresh baseline next time.
        write_json(state_file,{'files':{},'registry':None})
    elif cfg['set_default_terminal']:
        kind='stable' if any(k=='stable' for k,_ in targets) else 'preview'
        reg_set(kind)
    elif state['registry'] is not None:
        reg_restore(state['registry']); state['registry']=None; write_json(state_file,state)
    if args.theme or args.restore or args.opacity is not None: write_json(CONFIG,cfg)
    print('Done. Close all Windows Terminal windows and open a new one. Sign out/in if CMD still uses the previous prompt.')
    if not off and cfg['opacity']<15: print('Warning: very low opacity may be difficult to read.')

if __name__=='__main__':
    try: main()
    except (OSError,ValueError,RuntimeError,KeyError,TypeError) as exc:
        print('Error:',exc,file=sys.stderr); sys.exit(1)
