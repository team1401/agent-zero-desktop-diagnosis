"""Authorized one-shot native desktop activation; secrets remain in memory."""
import sys,json,shlex,time
from pathlib import Path
from urllib.parse import urlsplit,urljoin
ROOT=Path(__file__).parent
sys.path.insert(0,str(ROOT.parent/'creator-studio-integration'))
from verify_live import ssh,vault_login,meta
from a0_client import A0Client

def runtime():
 script='''import pathlib,json,os,socket,subprocess
p=pathlib.Path('/a0/usr/plugins/_desktop/sessions/agent-zero-desktop.json')
v=json.loads(p.read_text()) if p.exists() else {}
o={k:v.get(k) for k in ('display','xpra_port','pids','width','height','started_at','timezone','profile_dir')}
o['manifest_mtime']=p.stat().st_mtime if p.exists() else None
o['pid_status']={k:os.path.exists('/proc/'+str(i)) for k,i in v.get('pids',{}).items()}
o['pid_commands']={k:pathlib.Path('/proc/'+str(i)+'/comm').read_text().strip() for k,i in v.get('pids',{}).items() if os.path.exists('/proc/'+str(i))}
s=socket.socket();s.settimeout(2);o['port_accepting']=s.connect_ex(('127.0.0.1',int(v.get('xpra_port') or 0)))==0;s.close()
r=subprocess.run(['xdpyinfo','-display',':'+str(v.get('display',120))],capture_output=True,text=True);o['display_valid']=r.returncode==0
print(json.dumps(o))'''
 return json.loads(ssh('docker exec agent-zero-1 python3 -c '+shlex.quote(script)))
def containers():
 raw=json.loads(ssh('docker inspect agent-zero-1 agent-zero-2'))
 return [{'name':x['Name'],'id':x['Id'],'started':x['State']['StartedAt']} for x in raw]
def save():
 (ROOT/'repair-evidence.json').write_text(json.dumps(out,indent=2)+'\n')

out={'time_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())}
c=A0Client('http://<agent-zero-host>:50080',budget=25,timeout=85)
try:
 c.login(**vault_login())
 out['containers_before']=containers();out['runtime_before']=runtime()
 out['contexts_before']=meta(c.poll())
 if not out['contexts_before'] or any(x.get('running') is not False for x in out['contexts_before']):raise RuntimeError('BLOCK: contexts not all confirmed idle')
 if out['runtime_before']['port_accepting'] or any(out['runtime_before']['pid_status'].values()):raise RuntimeError('BLOCK: runtime now live; avoid disturbing possible human session')
 save()
 r=c.post('plugins/_desktop/desktop_session',{'action':'desktop'})
 out['activation']={'ok':r.get('ok'),'session_id':r.get('session_id'),'error':r.get('error')}
 out['runtime_after']=runtime()
 state=c.post('plugins/_desktop/desktop_session',{'action':'state','include_screenshot':False})
 out['state_after']=state
 path='/desktop/session/agent-zero-desktop/'
 links=[]
 for _ in range(4):
  response=c.request('GET',path)
  links.append({'path':urlsplit(path).path,'status':response.status_code,'html':'text/html' in response.headers.get('Content-Type','')})
  if response.status_code not in (301,302,303,307,308):break
  target=urlsplit(urljoin(c.base+path,response.headers['Location']))
  if target.netloc!='<agent-zero-host>:50080':raise RuntimeError('Unexpected redirect origin')
  path=target.path+('?' + target.query if target.query else '')
 out['route']=links
 out['contexts_after']=meta(c.poll());out['containers_after']=containers()
 out['contexts_unchanged']=out['contexts_before']==out['contexts_after']
 out['containers_unchanged']=out['containers_before']==out['containers_after']
except Exception as e:
 out['error']=str(e) if isinstance(e,RuntimeError) else type(e).__name__
finally:
 out['audit']=c.audit;save();print(json.dumps(out,indent=2))
