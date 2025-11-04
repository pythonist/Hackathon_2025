import requests
import json

test_phone = "+99999991000"

headers = {
    "x-rapidapi-key": "8d3dd95930mshd018383920dafbep1da792jsn445268c67ddc",
    "x-rapidapi-host": "network-as-code.nokia.rapidapi.com",
    "Content-Type": "application/json"
}

base_url = "https://network-as-code.p-eu.rapidapi.com"

print("=" * 60)
print("✅ FINAL NOKIA CAMARA API TEST (RapidAPI Verified Nov 2025)")
print("=" * 60)

# 1. SIM Swap (requires passthrough)
print("\n1️⃣ SIM Swap Check")
url = f"{base_url}/passthrough/camara/v1/sim-swap/sim-swap/v0/check"
payload = { "phoneNumber": test_phone, "maxAge": 240 }
r = requests.post(url, json=payload, headers=headers, timeout=10)
print(f"   Status: {r.status_code}")
print(f"   Response: {r.text[:200]}")

# 2. Location Retrieval (direct)
print("\n2️⃣ Location Retrieval")
url = f"{base_url}/location-retrieval/v0/retrieve"
payload = { "device": { "phoneNumber": test_phone }, "maxAge": 60 }
print(url)
r = requests.post(url, json=payload, headers=headers, timeout=10)
print(f"   Status: {r.status_code}")
print(f"   Response: {r.text[:200]}")

# 3. Device Roaming (direct)
print("\n3️⃣ Device Roaming Status")
url = f"{base_url}/device-status/v0/roaming"
payload = { "device": { "phoneNumber": test_phone } }
r = requests.post(url, json=payload, headers=headers, timeout=10)
print(f"   Status: {r.status_code}")
print(f"   Response: {r.text[:200]}")

# 4. Device Connectivity (direct)
print("\n4️⃣ Device Connectivity Status")
url = f"{base_url}/device-status/v0/connectivity"
payload = { "device": { "phoneNumber": test_phone } }
r = requests.post(url, json=payload, headers=headers, timeout=10)
print(f"   Status: {r.status_code}")
print(f"   Response: {r.text[:200]}")

print("\n" + "=" * 60)
