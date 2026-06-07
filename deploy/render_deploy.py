#!/usr/bin/env python3
"""Provision RCCA Copilot on Render via the REST API.

The Render CLI can only *list* services — creating them needs the REST API, which
needs an API key. This script is idempotent: it finds-or-creates the Postgres and
the web service, sets env vars (incl. ANTHROPIC_API_KEY), triggers a deploy, and
polls until live. It is the API-driven alternative to the dashboard Blueprint in
DEPLOY.md.

Secrets are read from the environment or a gitignored deploy/.secrets file
(KEY=value lines) — NEVER pass them on the command line or commit them:

    RENDER_API_KEY=rnd_...        # Render → Account Settings → API Keys
    ANTHROPIC_API_KEY=sk-ant-...  # the agent's key

Usage:  python deploy/render_deploy.py
"""
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

API = "https://api.render.com/v1"
REPO = "https://github.com/cognitivefactory-hector/rcca-copilot"
BRANCH = "main"
SERVICE_NAME = "rcca-copilot"
DB_NAME = "rcca-db"
REGION = "oregon"


def load_secrets():
    secrets_file = Path(__file__).parent / ".secrets"
    if secrets_file.exists():
        for line in secrets_file.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


def req(method, path, token, body=None):
    url = path if path.startswith("http") else f"{API}{path}"
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(url, data=data, method=method)
    r.add_header("Authorization", f"Bearer {token}")
    r.add_header("Content-Type", "application/json")
    r.add_header("Accept", "application/json")
    try:
        with urllib.request.urlopen(r) as resp:
            raw = resp.read().decode()
            return resp.status, (json.loads(raw) if raw else None)
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode() or "null")


def owner_id(token):
    status, data = req("GET", "/owners", token)
    if status != 200 or not data:
        sys.exit(f"Could not list owners ({status}): {data}")
    return data[0]["owner"]["id"]


def find_postgres(token, owner):
    _, data = req("GET", f"/postgres?name={DB_NAME}&ownerId={owner}", token)
    for item in data or []:
        pg = item.get("postgres", item)
        if pg.get("name") == DB_NAME:
            return pg
    return None


def ensure_postgres(token, owner):
    pg = find_postgres(token, owner)
    if pg:
        print(f"• Postgres '{DB_NAME}' exists ({pg['id']})")
        return pg["id"]
    print(f"• Creating Postgres '{DB_NAME}' …")
    status, data = req(
        "POST", "/postgres", token,
        {"name": DB_NAME, "ownerId": owner, "plan": "free", "region": REGION,
         "databaseName": "rcca", "databaseUser": "rcca"},
    )
    if status not in (200, 201):
        sys.exit(f"  Postgres create failed ({status}): {data}")
    return data["id"]


def pg_connection(token, pg_id):
    # poll until connection info is available (db must finish provisioning)
    for _ in range(60):
        status, data = req("GET", f"/postgres/{pg_id}/connection-info", token)
        if status == 200 and data:
            return data
        time.sleep(5)
    sys.exit("  Timed out waiting for Postgres connection info")


def env_vars(conn):
    # conn exposes host/port/database/user/password (internal connection)
    return [
        {"key": "ANTHROPIC_API_KEY", "value": os.environ["ANTHROPIC_API_KEY"]},
        {"key": "RCCA_MODEL", "value": "claude-opus-4-8"},
        {"key": "DJANGO_DEBUG", "value": "False"},
        {"key": "DJANGO_SECRET_KEY", "generateValue": True},
        {"key": "DJANGO_ALLOWED_HOSTS", "value": ".onrender.com,rcca.hector-garza.com"},
        {"key": "DJANGO_CSRF_TRUSTED_ORIGINS",
         "value": "https://*.onrender.com,https://rcca.hector-garza.com"},
        {"key": "POSTGRES_HOST", "value": conn["internalConnectionInfo"]["host"]},
        {"key": "POSTGRES_PORT", "value": str(conn["internalConnectionInfo"]["port"])},
        {"key": "POSTGRES_DB", "value": conn["internalConnectionInfo"]["databaseName"]},
        {"key": "POSTGRES_USER", "value": conn["internalConnectionInfo"]["user"]},
        {"key": "POSTGRES_PASSWORD", "value": conn["internalConnectionInfo"]["password"]},
    ]


def find_service(token, owner):
    _, data = req("GET", f"/services?name={SERVICE_NAME}&ownerId={owner}", token)
    for item in data or []:
        svc = item.get("service", item)
        if svc.get("name") == SERVICE_NAME:
            return svc
    return None


def ensure_service(token, owner, conn):
    svc = find_service(token, owner)
    if svc:
        print(f"• Web service '{SERVICE_NAME}' exists ({svc['id']})")
        return svc["id"]
    print(f"• Creating web service '{SERVICE_NAME}' …")
    body = {
        "type": "web_service",
        "name": SERVICE_NAME,
        "ownerId": owner,
        "repo": REPO,
        "branch": BRANCH,
        "autoDeploy": "yes",
        "serviceDetails": {
            "env": "docker",
            "plan": "free",
            "region": REGION,
            "healthCheckPath": "/healthz",
            "envSpecificDetails": {"dockerfilePath": "./Dockerfile"},
        },
        "envVars": env_vars(conn),
    }
    status, data = req("POST", "/services", token, body)
    if status not in (200, 201):
        sys.exit(f"  Service create failed ({status}): {data}")
    return (data.get("service") or data)["id"]


def poll_deploy(token, svc_id):
    print("• Waiting for deploy …")
    for _ in range(120):
        _, data = req("GET", f"/services/{svc_id}/deploys?limit=1", token)
        if data:
            dep = data[0].get("deploy", data[0])
            status = dep.get("status")
            print(f"  deploy status: {status}")
            if status in ("live", "deactivated", "build_failed", "update_failed", "canceled"):
                return status
        time.sleep(10)
    return "timeout"


def main():
    load_secrets()
    token = os.environ.get("RENDER_API_KEY")
    if not token or not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("Set RENDER_API_KEY and ANTHROPIC_API_KEY (env or deploy/.secrets).")

    owner = owner_id(token)
    print(f"Owner: {owner}")
    pg_id = ensure_postgres(token, owner)
    conn = pg_connection(token, pg_id)
    svc_id = ensure_service(token, owner, conn)
    status = poll_deploy(token, svc_id)
    print(f"\nDeploy finished: {status}")
    print(f"Service: https://dashboard.render.com (id {svc_id})")
    if status != "live":
        sys.exit("Deploy did not reach 'live' — check logs: render logs " + svc_id)


if __name__ == "__main__":
    main()
