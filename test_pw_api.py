import requests, json

phone = '9871876926'

headers = {
    'Content-Type': 'application/json',
    'Client-Type': 'WEB',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

org_id = '5eb393ee95fab7468a79d189'

# Send OTP
print("Step 1: Sending OTP...")
r = requests.post('https://api.penpencil.co/v1/users/get-otp',
    json={'username': phone, 'countryCode': '+91', 'organizationId': org_id},
    headers=headers, timeout=15)
print(f"  Status: {r.status_code} | Success: {r.json().get('success')}")

if not r.json().get('success'):
    print("OTP send failed!")
    exit()

print("\nOTP SENT! Enter OTP: ", end="", flush=True)
otp = input().strip()

# Step 2: Verify OTP
print("\nStep 2: Verifying OTP...")
r2 = requests.post('https://api.penpencil.co/v1/users/verify-otp',
    json={'mobile': phone, 'otp': otp, 'organizationId': org_id},
    headers=headers, timeout=15)
verify_data = r2.json()
print(f"  Status: {r2.status_code} | Success: {verify_data.get('success')}")

if not verify_data.get('success'):
    print(f"  Error: {verify_data}")
    exit()

# Step 3: Try login endpoint with verified user info
user_id = verify_data.get('data', {}).get('_id', '')
profile_id = verify_data.get('data', {}).get('profileId', '')
print(f"  User ID: {user_id}")
print(f"  Profile ID: {profile_id}")

# Try various login/token endpoints
print("\nStep 3: Getting token...")

login_attempts = [
    # Try login with OTP
    ('POST', 'https://api.penpencil.co/v1/users/login',
     {'username': phone, 'otp': otp, 'organizationId': org_id}),
    
    # Try login with mobile + OTP
    ('POST', 'https://api.penpencil.co/v1/users/login',
     {'mobile': phone, 'otp': otp, 'organizationId': org_id}),

    # Try get-token
    ('POST', 'https://api.penpencil.co/v1/users/get-token',
     {'mobile': phone, 'otp': otp, 'organizationId': org_id}),
    
    # Try token generate
    ('POST', 'https://api.penpencil.co/v1/users/generate-token',
     {'mobile': phone, 'organizationId': org_id, 'userId': user_id}),

    # Try with userId
    ('POST', 'https://api.penpencil.co/v1/users/login',
     {'username': phone, 'password': otp, 'organizationId': org_id}),
    
    # Try auth token  
    ('POST', 'https://api.penpencil.co/v1/users/auth-token',
     {'mobile': phone, 'otp': otp, 'organizationId': org_id}),
     
    # Try refresh token
    ('POST', 'https://api.penpencil.co/v1/users/refresh-token',
     {'mobile': phone, 'organizationId': org_id}),
     
    # Try signin
    ('POST', 'https://api.penpencil.co/v1/users/signin', 
     {'mobile': phone, 'otp': otp, 'organizationId': org_id}),
]

for method, url, body in login_attempts:
    try:
        r = requests.post(url, json=body, headers=headers, timeout=8)
        data = r.json()
        
        # Check for token in response
        token = None
        if isinstance(data.get('data'), dict):
            token = data['data'].get('token') or data['data'].get('access_token') or data['data'].get('accessToken')
        if not token:
            token = data.get('token') or data.get('access_token')
        
        status = "TOKEN FOUND!" if token else f"{data.get('error', {}).get('message', data.get('message', 'no msg'))}"
        print(f"  {url.split('/v1/')[-1]} -> {r.status_code} | {status}")
        
        if token:
            with open('pw_token.txt', 'w') as f:
                f.write(token)
            print(f"\n  TOKEN: {token[:60]}...")
            print(f"  Saved to pw_token.txt!")
            
            # Save full response
            with open('pw_response.json', 'w') as f:
                f.write(json.dumps(data, indent=2))
            break
    except Exception as e:
        print(f"  {url.split('/v1/')[-1]} -> Error: {str(e)[:80]}")

print("\nDone!")
