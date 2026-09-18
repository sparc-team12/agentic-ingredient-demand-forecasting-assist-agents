"""Standalone CLI scripts, runnable as `python -m scripts.<module>`.

Responsibility: one-off/operational entry points that don't belong on the
ASGI request path (e.g. seeding). Reuse `db`/`services` for logic; scripts
themselves stay thin.
"""
