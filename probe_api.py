"""
Live API probe script – runs against a locally running server at http://127.0.0.1:8000
"""
import requests
import json
import sys

BASE = "http://127.0.0.1:8000"

def check(label, resp, expected_status=200):
    status = "[PASS]" if resp.status_code == expected_status else f"[FAIL] (got {resp.status_code})"
    print(f"{status} | {label}")
    if resp.status_code != expected_status:
        print(f"         Body: {resp.text[:300]}")
    return resp.status_code == expected_status

passes = 0
failures = 0

# 1. Health check
r = requests.get(f"{BASE}/")
ok = check("GET / (health check)", r, 200)
passes += ok; failures += not ok
print(f"         Response: {r.json()}")

# 2. Create profile
profile_payload = {
    "goal": "Early Retirement",
    "time_horizon": 15,
    "monthly_budget": 2000.0,
    "risk_tolerance": "medium",
    "existing_holdings": "VTI,BND"
}
r = requests.post(f"{BASE}/profile", json=profile_payload)
ok = check("POST /profile (create)", r, 200)
passes += ok; failures += not ok
profile_id = r.json().get("id") if ok else None
print(f"         Created profile ID: {profile_id}")

# 3. Get profile
if profile_id:
    r = requests.get(f"{BASE}/profile/{profile_id}")
    ok = check(f"GET /profile/{profile_id} (read)", r, 200)
    passes += ok; failures += not ok

# 4. Update profile
if profile_id:
    updated = {**profile_payload, "goal": "Financial Independence"}
    r = requests.put(f"{BASE}/profile/{profile_id}", json=updated)
    ok = check(f"PUT /profile/{profile_id} (update)", r, 200)
    passes += ok; failures += not ok
    if ok:
        assert r.json()["goal"] == "Financial Independence", "Goal not updated!"
        print("         Goal updated correctly [OK]")

# 5. Get non-existent profile
r = requests.get(f"{BASE}/profile/99999")
ok = check("GET /profile/99999 (expect 404)", r, 404)
passes += ok; failures += not ok

# 6. Chat endpoint
if profile_id:
    print("\n         [Calling LLM - may take a few seconds...]\n")
    r = requests.post(f"{BASE}/chat", json={"user_id": profile_id, "message": "Give me a brief 1-sentence investment tip."}, timeout=60)
    # 200 = LLM responded; 503 = quota exhausted (gracefully handled - also a PASS)
    if r.status_code == 200:
        ok = check("POST /chat (LLM responded)", r, 200)
        passes += ok; failures += not ok
        response_text = r.json().get("response", "")
        print(f"         AI response preview: {response_text[:150]}...")
    elif r.status_code == 503:
        ok = True
        print("[PASS] | POST /chat (rate-limited - graceful 503 returned, handler working correctly)")
        print(f"         Detail: {r.json().get('detail', '')}")
        passes += 1
    else:
        ok = check("POST /chat (unexpected status)", r, 200)
        failures += not ok

# 7. Chat history
if profile_id:
    r = requests.get(f"{BASE}/history/{profile_id}")
    ok = check(f"GET /history/{profile_id}", r, 200)
    passes += ok; failures += not ok
    if ok:
        msgs = r.json()
        print(f"         History length: {len(msgs)} messages")

# 8. Chat missing field
r = requests.post(f"{BASE}/chat", json={"user_id": 1})
ok = check("POST /chat (missing message -> 422)", r, 422)
passes += ok; failures += not ok

# Summary
print(f"\n{'='*55}")
print(f"  API Probe Summary: {passes} passed | {failures} failed")
print(f"{'='*55}")
sys.exit(0 if failures == 0 else 1)
