import requests, json

token = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJleHAiOjE3NzIzNDU3NzkuMjY0LCJkYXRhIjp7Il9pZCI6IjY4M2Q0MjdkNWM3NGExZGM0NjMxZDRlMyIsInVzZXJuYW1lIjoiOTg3MTg3NjkyNiIsImZpcnN0TmFtZSI6IlJpc2hhYmgiLCJsYXN0TmFtZSI6IlBhbmRleSIsIm9yZ2FuaXphdGlvbiI6eyJfaWQiOiI1ZWIzOTNlZTk1ZmFiNzQ2OGE3OWQxODkiLCJ3ZWJzaXRlIjoicGh5c2ljc3dhbGxhaC5jb20iLCJuYW1lIjoiUGh5c2ljc3dhbGxhaCJ9LCJlbWFpbCI6InJpc2hhYmhwYW5kZXk5ODcxODdAZ21haWwuY29tIiwicm9sZXMiOlsiNWIyN2JkOTY1ODQyZjk1MGE3NzhjNmVmIl0sImNvdW50cnlHcm91cCI6IklOIiwib25lUm9sZXMiOltdLCJ0eXBlIjoiVVNFUiJ9LCJqdGkiOiJvMWR1S05id1E5MnRlbDV3Rk4xdXVnXzY4M2Q0MjdkNWM3NGExZGM0NjMxZDRlMyIsImlhdCI6MTc3MTc0MDk3OX0.3zvk7WuvBHZTIxbMKtFO1l85tABp79LpXgiHcK1CwUo'
parent = '6819787b3380aa01c4251997'
child = '6964eabd1971fce79e26840b'

headers = {
    'Authorization': f'Bearer {token}',
    'Client-Type': 'WEB',
}

variations = [
    f'https://api.penpencil.co/v3/files/{parent}/subject-content/{child}',
    f'https://api.penpencil.co/v2/files/{parent}/subject-content/{child}',
    f'https://api.penpencil.co/v3/files/subject-content/{child}?parentId={parent}',
    f'https://api.penpencil.co/v3/subject-contents/{child}',
    f'https://api.penpencil.co/v3/contents/{child}',
]

for url in variations:
    try:
        r = requests.get(url, headers=headers)
        print(f"URL: {url} -> Status: {r.status_code}")
        if r.status_code == 200:
            print("FOUND!")
            # print(r.text[:500])
            break
    except:
        pass
