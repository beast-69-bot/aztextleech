import requests, json

token = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJleHAiOjE3NzIzNDU3NzkuMjY0LCJkYXRhIjp7Il9pZCI6IjY4M2Q0MjdkNWM3NGExZGM0NjMxZDRlMyIsInVzZXJuYW1lIjoiOTg3MTg3NjkyNiIsImZpcnN0TmFtZSI6IlJpc2hhYmgiLCJsYXN0TmFtZSI6IlBhbmRleSIsIm9yZ2FuaXphdGlvbiI6eyJfaWQiOiI1ZWIzOTNlZTk1ZmFiNzQ2OGE3OWQxODkiLCJ3ZWJzaXRlIjoicGh5c2ljc3dhbGxhaC5jb20iLCJuYW1lIjoiUGh5c2ljc3dhbGxhaCJ9LCJlbWFpbCI6InJpc2hhYmhwYW5kZXk5ODcxODdAZ21haWwuY29tIiwicm9sZXMiOlsiNWIyN2JkOTY1ODQyZjk1MGE3NzhjNmVmIl0sImNvdW50cnlHcm91cCI6IklOIiwib25lUm9sZXMiOltdLCJ0eXBlIjoiVVNFUiJ9LCJqdGkiOiJvMWR1S05id1E5MnRlbDV3Rk4xdXVnXzY4M2Q0MjdkNWM3NGExZGM0NjMxZDRlMyIsImlhdCI6MTc3MTc0MDk3OX0.3zvk7WuvBHZTIxbMKtFO1l85tABp79LpXgiHcK1CwUo'

url = 'https://api.penpencil.co/v1/users/self'
headers = { 'Authorization': f'Bearer {token}', 'Client-Type': 'WEB' }

try:
    r = requests.get(url, headers=headers)
    print(f'Status: {r.status_code}')
    if r.status_code == 200 and r.json().get('success'):
        print('✅ TOKEN IS VALID! (Self-info confirmed)')
        with open('pw_token.txt', 'w') as f:
            f.write(token)
    else:
        print(f'Response: {r.text}')
except Exception as e:
    print(f'Error: {e}')
