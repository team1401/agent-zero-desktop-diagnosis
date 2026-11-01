"""Read-only desktop diagnosis; never starts desktop or mutates contexts."""
import sys,json,subprocess,shlex,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent.parent/'creator-studio-integration'))
from verify_live import ssh,vault_login,meta
from a0_client import A0Client
root=Path(__file__).parent
c=A0Client('http://100.108.186.69:50080',budget=12,timeout=25)
c.login(**vault_login())
out={'time_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'contexts':meta(c.poll()),'state':c.post('plugins/_desktop/desktop_session',{'action':'state','include_screenshot':False,'context_id':'OzIMaV93'}),'links':[]}
from urllib.parse import urlsplit,urljoin
for path in ['/','/desktop/session/agent-zero-desktop/']:
 r=c.request('GET',path)
 entry={'path':path,'status':r.status_code}
 for _ in range(3):
  if r.status_code not in [301,302,303,307,308]:break
  target=urlsplit(urljoin(c.base+path,r.headers.get('Location','')))
  entry.setdefault('redirects',[]).append({'path':target.path,'query_present':bool(target.query)})
  if target.netloc!='100.108.186.69:50080':break
  # Inspect query names only; never print URL values or use an unknown auth parameter.
  from urllib.parse import parse_qsl
  pairs=parse_qsl(target.query)
  safe={'path','title','quality','speed','sharing','clipboard','clipboard_direction','clipboard_poll','clipboard_preferred_format','printing','file_transfer','sound','offscreen','floating_menu','xpramenu','encoding'}
  entry['query_names']=[k for k,v in pairs]
  if any(k not in safe for k,v in pairs):break
  path=target.path
  r=c.request('GET',path,params=pairs)
  entry['html_frame']=('text/html' in r.headers.get('Content-Type',''))
  entry['final_status']=r.status_code
 out['links'].append(entry)
script='''import pathlib,json,os,socket
p=pathlib.Path('/a0/usr/plugins/_desktop/sessions/agent-zero-desktop.json')
v=json.loads(p.read_text()) if p.exists() else {}
o={k:v.get(k) for k in ('display','xpra_port','pids','width','height','started_at','timezone')}
o['manifest_exists']=p.exists()
o['pid_status']={k:os.path.exists('/proc/'+str(i)) for k,i in v.get('pids',{}).items()}
s=socket.socket();s.settimeout(2);o['xpra_port_accepting']=s.connect_ex(('127.0.0.1',int(v.get('xpra_port') or 0)))==0;s.close()
o['x_sockets']=[x.name for x in pathlib.Path('/tmp/.X11-unix').glob('*')]
print(json.dumps(o))'''
out['runtime']=json.loads(ssh('docker exec agent-zero-1 python3 -c '+shlex.quote(script)))
raw=json.loads(ssh('docker inspect agent-zero-1 agent-zero-2'))
out['containers']=[{'name':x['Name'],'id':x['Id'],'started':x['State']['StartedAt'],'status':x['State']['Status']} for x in raw]
out['audit']=c.audit
(root/'readonly-evidence.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
