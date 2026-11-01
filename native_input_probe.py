"""Dedicated native X11 input probe, not a browser takeover test."""
import sys,json,shlex,subprocess,time,uuid
from pathlib import Path
ROOT=Path(__file__).parent
sys.path.insert(0,str(ROOT.parent/'creator-studio-integration'))
from verify_live import ssh,vault_login,meta
from a0_client import A0Client
c=A0Client('http://100.108.186.69:50080',budget=12,timeout=25)
c.login(**vault_login())
contexts=meta(c.poll())
assert contexts and all(x['running'] is False for x in contexts),'BLOCK: context busy'
suffix=uuid.uuid4().hex[:12]
directory='/a0/usr/workdir/desktop-repair-test-'+suffix
title='Desktop repair input probe '+suffix
sentinel='native-desktop-keyboard-'+suffix
remote='''import os,sys,json,subprocess,time,pathlib,hashlib
from PIL import ImageGrab,ImageStat
D=pathlib.Path(DIRECTORY); title=TITLE; sentinel=SENTINEL
e=os.environ.copy();e['DISPLAY']=':120'
def run(args,timeout=15):
 r=subprocess.run(args,env=e,capture_output=True,text=True,timeout=timeout)
 if r.returncode:raise RuntimeError('Native probe command failed: '+args[0])
 return r.stdout.strip()
info=run(['xpra','info',':120'])
clients=[l for l in info.splitlines() if l.startswith('clients=')]
assert clients==['clients=0'],'BLOCK: connected Xpra client'
v=json.loads(pathlib.Path('/a0/usr/plugins/_desktop/sessions/agent-zero-desktop.json').read_text())
assert v['display']==120 and v['pids']=={'xvfb':1437,'xfce':1458,'xpra':2017},'BLOCK: runtime changed'
D.mkdir(mode=0o700)
app="""import gi,sys,pathlib
gi.require_version('Gtk','3.0')
from gi.repository import Gtk
w=Gtk.Window(title=sys.argv[1]);w.set_default_size(420,180);w.move(350,250)
f=Gtk.Fixed();w.add(f)
e=Gtk.Entry();e.set_size_request(380,35);f.put(e,20,20)
b=Gtk.Button(label='Save dedicated test artifact');b.set_size_request(380,40);f.put(b,20,90)
def save(button):pathlib.Path(sys.argv[2]).write_text(e.get_text()+chr(10))
b.connect('clicked',save);w.connect('destroy',Gtk.main_quit);w.show_all();e.grab_focus();Gtk.main()
"""
(D/'probe_app.py').write_text(app)
p=subprocess.Popen(['/usr/bin/python3',str(D/'probe_app.py'),title,str(D/'keyboard-pointer-verified.txt')],env=e,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,text=True)
try:
 time.sleep(2)
 if p.poll() is not None:raise RuntimeError('Probe GUI exited: '+p.stderr.read()[-1200:])
 wid=run(['xdotool','search','--onlyvisible','--name',title]).splitlines()
 assert len(wid)==1,'BLOCK: unique probe window not found'
 wid=wid[0]
 run(['xdotool','windowactivate','--sync',wid])
 run(['xdotool','type','--clearmodifiers','--delay','35',sentinel])
 image=ImageGrab.grab(xdisplay=':120');image.save(D/'native-render.png')
 render={'size':list(image.size),'channel_variance':ImageStat.Stat(image).var,'bytes':(D/'native-render.png').stat().st_size}
 # Click a known button inside our newly created window, never existing desktop content.
 run(['xdotool','mousemove','--sync','--window',wid,'210','110'])
 run(['xdotool','click','1'])
 time.sleep(1)
 artifact=D/'keyboard-pointer-verified.txt'
 content=artifact.read_bytes() if artifact.exists() else b''
 result={'clients_before':0,'input_transport':'native X11 xdotool (not browser/Xpra input)','artifact_path':str(artifact),'keyboard_and_pointer_verified':content==(sentinel+'\\n').encode(),'artifact_sha256':hashlib.sha256(content).hexdigest(),'render':render,'directory':str(D)}
 print(json.dumps(result))
finally:
 p.terminate();p.wait(timeout=10)
'''
remote='DIRECTORY='+repr(directory)+'\nTITLE='+repr(title)+'\nSENTINEL='+repr(sentinel)+'\n'+remote
out={'contexts_before':contexts}
try:
 r=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=10','root@100.108.186.69','docker exec agent-zero-1 /usr/bin/python3 -c '+shlex.quote(remote)],capture_output=True,text=True,timeout=35)
 if r.returncode:raise RuntimeError('Dedicated probe failed: '+r.stderr[-2000:])
 out['native_probe']=json.loads(r.stdout)
 out['contexts_after']=meta(c.poll())
 out['contexts_unchanged']=out['contexts_before']==out['contexts_after']
 out['state_after']=c.post('plugins/_desktop/desktop_session',{'action':'state','include_screenshot':False})
except Exception as e:out['error']=str(e) if isinstance(e,RuntimeError) else type(e).__name__
(ROOT/'native-input-evidence.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
