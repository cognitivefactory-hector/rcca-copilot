"""M0 smoke tests: the app serves and talks to the database.

The substantive tests (state machine, grounding) arrive in M1/M3 per PLAN.md.
"""
import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_home_serves(client):
    response = client.get(reverse("rcca:home"))
    assert response.status_code == 200
    assert b"RCCA Copilot" in response.content


@pytest.mark.django_db
def test_healthz_reports_db_connectivity(client):
    # DB connectivity moved to /healthz when the home page became the workspace
    # picker (M4). The live DB fixture means this should report ok.
    response = client.get(reverse("rcca:healthz"))
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "db": True}
