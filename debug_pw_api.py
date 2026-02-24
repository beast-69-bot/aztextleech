import requests, json, urllib.parse

token = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJleHAiOjE3NzIzNDU3NzkuMjY0LCJkYXRhIjp7Il9pZCI6IjY4M2Q0MjdkNWM3NGExZGM0NjMxZDRlMyIsInVzZXJuYW1lIjoiOTg3MTg3NjkyNiIsImZpcnN0TmFtZSI6IlJpc2hhYmgiLCJsYXN0TmFtZSI6IlBhbmRleSIsIm9yZ2FuaXphdGlvbiI6eyJfaWQiOiI1ZWIzOTNlZTk1ZmFiNzQ2OGE3OWQxODkiLCJ3ZWJzaXRlIjoicGh5c2ljc3dhbGxhaC5jb20iLCJuYW1lIjoiUGh5c2ljc3dhbGxhaCJ9LCJlbWFpbCI6InJpc2hhYmhwYW5kZXk5ODcxODdAZ21haWwuY29tIiwicm9sZXMiOlsiNWIyN2JkOTY1ODQyZjk1MGE3NzhjNmVmIl0sImNvdW50cnlHcm91cCI6IklOIiwib25lUm9sZXMiOltdLCJ0eXBlIjoiVVNFUiJ9LCJqdGkiOiJvMWR1S05id1E5MnRlbDV3Rk4xdXVnXzY4M2Q0MjdkNWM3NGExZGM0NjMxZDRlMyIsImlhdCI6MTc3MTc0MDk3OX0.3zvk7WuvBHZTIxbMKtFO1l85tABp79LpXgiHcK1CwUo'
clean_url = 'https://d1d34p8vz63oiq.cloudfront.net/cda5e546-002d-4c4c-89a9-fb47e2544fb4/master.mpd'

pw_headers = {
    'Authorization': f'Bearer {token}',
    'Client-Type': 'WEB',
    'Organization-Id': '5eb393ee95fab7468a79d189',
}

def test_api(url, label):
    print(f"\n--- Testing {label} ---")
    print(f"URL: {url}")
    try:
        r = requests.get(url, headers=pw_headers, timeout=10)
        print(f"Status: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            print(f"Success: {data.get('success')}")
            if 'data' in data:
                res = data['data'].get('url') or data['data'].get('videoUrl')
                print(f"Playable URL: {res}")
        else:
            print(f"Body: {r.text[:200]}")
    except Exception as e:
        print(f"Error: {e}")

# Test variants
test_api(f"https://api.penpencil.co/v1/videos/get-url?url={clean_url}", "v1 (No Encoding)")
test_api(f"https://api.penpencil.co/v1/videos/get-url?url={urllib.parse.quote(clean_url)}", "v1 (Encoded)")
test_api(f"https://api.penpencil.co/v3/files/get-video-details?url={urllib.parse.quote(clean_url)}", "v3 Details (Encoded)")
test_api(f"https://api.penpencil.co/v3/files/get-signed-url?url={urllib.parse.quote(clean_url)}", "v3 Signed (Encoded)")
