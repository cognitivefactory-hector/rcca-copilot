"""M0 smoke tests: the app serves and talks to the database.

The substantive tests (state machine, grounding) arrive in M1/M3 per PLAN.md.
"""
import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_home_serves_and_reports_db_connected(client):
    response = client.get(reverse("rcca:home"))
    assert response.status_code == 200
    assert b"RCCA Copilot" in response.content
    # The DB fixture is live, so the connectivity check should pass.
    assert b"connected" in response.content


@pytest.mark.django_db
def test_healthz_ok(client):
    response = client.get(reverse("rcca:healthz"))
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "db": True}
