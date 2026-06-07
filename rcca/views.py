from django.db import OperationalError, connection
from django.http import JsonResponse
from django.shortcuts import render


def _db_ok() -> bool:
    """True if Postgres answers a trivial query — the M0 connectivity check."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        return True
    except OperationalError:
        return False


def home(request):
    return render(request, "rcca/home.html", {"db_ok": _db_ok()})


def healthz(request):
    ok = _db_ok()
    return JsonResponse({"status": "ok" if ok else "degraded", "db": ok}, status=200 if ok else 503)
