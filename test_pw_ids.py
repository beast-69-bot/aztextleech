import requests, json

token = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJleHAiOjE3NzIzNDU3NzkuMjY0LCJkYXRhIjp7Il9pZCI6IjY4M2Q0MjdkNWM3NGExZGM0NjMxZDRlMyIsInVzZXJuYW1lIjoiOTg3MTg3NjkyNiIsImZpcnN0TmFtZSI6IlJpc2hhYmgiLCJsYXN0TmFtZSI6IlBhbmRleSIsIm9yZ2FuaXphdGlvbiI6eyJfaWQiOiI1ZWIzOTNlZTk1ZmFiNzQ2OGE3OWQxODkiLCJ3ZWJzaXRlIjoicGh5c2ljc3dhbGxhaC5jb20iLCJuYW1lIjoiUGh5c2ljc3dhbGxhaCJ9LCJlbWFpbCI6InJpc2hhYmhwYW5kZXk5ODcxODdAZ21haWwuY29tIiwicm9sZXMiOlsiNWIyN2JkOTY1ODQyZjk1MGE3NzhjNmVmIl0sImNvdW50cnlHcm91cCI6IklOIiwib25lUm9sZXMiOltdLCJ0eXBlIjoiVVNFUiJ9LCJqdGkiOiJvMWR1S05id1E5MnRlbDV3Rk4xdXVnXzY4M2Q0MjdkNWM3NGExZGM0NjMxZDRlMyIsImlhdCI6MTc3MTc0MDk3OX0.3zvk7WuvBHZTIxbMKtFO1l85tABp79LpXgiHcK1CwUo'

# Sample URL with parent/child info
full_url = 'https://d1d34p8vz63oiq.cloudfront.net/cda5e546-002d-4c4c-89a9-fb47e2544fb4/master.mpd&parentId=6819787b3380aa01c4251997&childId=6964eabd1971fce79e26840b'

# Try to extract parentId and childId
import re
parent_match = re.search(r'parentId=([^&]+)', full_url)
child_match = re.search(r'childId=([^&]+)', full_url)

if parent_match and child_match:
    parent_id = parent_match.group(1)
    child_id = child_match.group(1)
    print(f"Parent: {parent_id}, Child: {child_id}")
    
    # Try the v3 files API
    headers = {
        'Authorization': f'Bearer {token}',
        'Client-Type': 'WEB',
    }
    
    # This is the common endpoint for PW content
    api_url = f'https://api.penpencil.co/v3/files/{parent_id}/subject-content/{child_id}'
    print(f"Fetching from: {api_url}")
    
    try:
        r = requests.get(api_url, headers=headers)
        print(f"Status: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            # print(json.dumps(data, indent=2))
            if data.get('success'):
                video_details = data.get('data', {}).get('videoDetails', {})
                video_url = video_details.get('videoUrl')
                print(f"✅ FOUND VIDEO URL: {video_url}")
            else:
                print("Success False")
    except Exception as e:
        print(f"Error: {e}")
else:
    print("Could not find IDs")
