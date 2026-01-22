#!/usr/bin/env python3
import urllib.request
import json

job_id = "94d8c3e1-154e-4355-aaf7-90779e435283"
base_url = "http://localhost:8000"

# 대기 중인 항목 가져오기
req = urllib.request.Request(f"{base_url}/api/v1/review/pending/{job_id}")
with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read().decode())

pending_items = data.get("pending_items", [])
print(f"총 {len(pending_items)}개 항목 승인 중...")

# 각 항목 승인
for i, item in enumerate(pending_items):
    decision = {
        "job_id": job_id,
        "review_item_id": item["id"],
        "decision": "approve"
    }
    req = urllib.request.Request(
        f"{base_url}/api/v1/review/decision",
        data=json.dumps(decision).encode(),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req) as resp:
            pass
    except Exception as e:
        print(f"Error: {e}")

    if (i + 1) % 20 == 0:
        print(f"  {i + 1}/{len(pending_items)} 완료...")

print(f"모든 {len(pending_items)}개 항목 승인 완료!")
