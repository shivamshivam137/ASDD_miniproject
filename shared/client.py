import json, urllib.request, time
BASE='http://127.0.0.1:8090'

def get(path, timeout=2.5, retries=3):
    last={'ok':False,'offline':True}
    for attempt in range(retries):
        try:
            req=urllib.request.Request(BASE+path,headers={'Accept':'application/json'},method='GET')
            with urllib.request.urlopen(req,timeout=timeout) as r:
                return json.loads(r.read().decode())
        except Exception as e:
            last={'ok':False,'offline':True,'error':str(e)}
            if attempt < retries-1: time.sleep(0.35)
    return last

def post(path,payload,timeout=2.5,retries=3):
    last={'ok':False,'offline':True}
    for attempt in range(retries):
        try:
            req=urllib.request.Request(BASE+path,data=json.dumps(payload).encode(),headers={'Content-Type':'application/json'},method='POST')
            with urllib.request.urlopen(req,timeout=timeout) as r:
                return json.loads(r.read().decode())
        except Exception as e:
            last={'ok':False,'offline':True,'error':str(e)}
            if attempt < retries-1: time.sleep(0.35)
    return last
