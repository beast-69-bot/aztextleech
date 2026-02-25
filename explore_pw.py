
import requests, json

token = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJleHAiOjE3NzIzNDU3NzkuMjY0LCJkYXRhIjp7Il9pZCI6IjY4M2Q0MjdkNWM3NGExZGM0NjMxZDRlMyIsInVzZXJuYW1lIjoiOTg3MTg3NjkyNiIsImZpcnN0TmFtZSI6IlJpc2hhYmgiLCJsYXN0TmFtZSI6IlBhbmRleSIsIm9yZ2FuaXphdGlvbiI6eyJfaWQiOiI1ZWIzOTNlZTk1ZmFiNzQ2OGE3OWQxODkiLCJ3ZWJzaXRlIjoicGh5c2ljc3dhbGxhaC5jb20iLCJuYW1lIjoiUGh5c2ljc3dhbGxhaCJ9LCJlbWFpbCI6InJpc2hhYmhwYW5kZXk5ODcxODdAZ21haWwuY29tIiwicm9sZXMiSlsiNWIyN2JkOTY1ODQyZjk1MGE3NzhjNmVmIl0sImNvdW50cnlHcm91cCI6IklOIiwib25lUm9sZXMiOltdLCJ0eXBlIjoiVVNFUiJ9LCJqdGkiOiJvMWR1S05id1E5MnRlbDV3Rk4xdXVnXzY4M2Q0MjdkNWM3NGExZGM0NjMxZDRlMyIsImlhdCI6MTc3MTc0MDk3OX0.3zvk7WuvBHZTIxbMKtFO1l85tABp79LpXgiHcK1CwUo'
bid = '6819787b3380aa01c4251997'
oid = '5eb393ee95fab7468a79d189'
headers = {
    'Authorization': f'Bearer {token}',
    'Client-Type': 'WEB'
}

# 1. Get Subjects
url = f'https://api.penpencil.co/v1/batches/{bid}/subjects?organizationId={oid}'
print(f'Fetching: {url}')
r = requests.get(url, headers=headers)
if r.status_code == 200:
    subjects = r.json().get('data', [])
    for s in subjects:
        sid = s.get('_id')
        sname = s.get('subjectId', {}).get('name', 'Unknown')
        print(f'Subject: {sname} ({sid})')
        
        chap_url = f'https://api.penpencil.co/v1/chapters?subjectId={sid}&organizationId={oid}'
        rc = requests.get(chap_url, headers=headers)
        if rc.status_code == 200:
            chapters = rc.json().get('data', [])
            for c in chapters[:2]:
                chid = c.get('_id')
                print(f'  Chapter: {c.get("name")} ({chid})')
                
                cont_url = f'https://api.penpencil.co/v1/contents?chapterId={chid}&organizationId={oid}&contentType=video'
                rct = requests.get(cont_url, headers=headers)
                if rct.status_code == 200:
                    contents = rct.json().get('data', [])
                    for cnt in contents[:2]:
                        print(f'    Video: {cnt.get("name")} ID: {cnt.get("_id")}')
else:
    print(f'Error {r.status_code}: {r.text}')
