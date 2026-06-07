#!/usr/bin/env python3
"""Point rcca.hector-garza.com at the Render service via a Cloudflare CNAME.

Idempotent: creates or updates the CNAME record. Needs a scoped Cloudflare API
token (Zone.DNS:Edit on the hector-garza.com zone). Read from env or the
gitignored deploy/.secrets file:

    CLOUDFLARE_API_TOKEN=...
    RENDER_TARGET_HOST=rcca-copilot-xxxx.onrender.com   # from the Render service

Usage:  python deploy/cloudflare_dns.py
"""
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

API = "https://api.cloudflare.com/client/v4"
ZONE_NAME = "hector-garza.com"
RECORD_NAME = "rcca.hector-garza.com"


def load_secrets():
    f = Path(__file__).parent / ".secrets"
    if f.exists():
        for line in f.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


def req(method, path, token, body=None):
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(f"{API}{path}", data=data, method=method)
    r.add_header("Authorization", f"Bearer {token}")
    r.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(r) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        return json.loads(e.read().decode() or "null")


def main():
    load_secrets()
    token = os.environ.get("CLOUDFLARE_API_TOKEN")
    target = os.environ.get("RENDER_TARGET_HOST")
    if not token or not target:
        sys.exit("Set CLOUDFLARE_API_TOKEN and RENDER_TARGET_HOST (env or deploy/.secrets).")

    zones = req("GET", f"/zones?name={ZONE_NAME}", token)
    if not zones.get("success") or not zones["result"]:
        sys.exit(f"Zone {ZONE_NAME} not found: {zones}")
    zone_id = zones["result"][0]["id"]

    existing = req("GET", f"/zones/{zone_id}/dns_records?name={RECORD_NAME}", token)
    record = {"type": "CNAME", "name": RECORD_NAME, "content": target, "proxied": True, "ttl": 1}

    if existing.get("result"):
        rec_id = existing["result"][0]["id"]
        out = req("PUT", f"/zones/{zone_id}/dns_records/{rec_id}", token, record)
        action = "updated"
    else:
        out = req("POST", f"/zones/{zone_id}/dns_records", token, record)
        action = "created"

    if out.get("success"):
        print(f"CNAME {action}: {RECORD_NAME} → {target} (proxied)")
    else:
        sys.exit(f"DNS update failed: {out}")


if __name__ == "__main__":
    main()
