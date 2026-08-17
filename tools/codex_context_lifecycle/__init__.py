"""Repository-owned context lifecycle control plane.

Canonical knowledge stays in owner-authored repository artifacts. This package
classifies sources, validates promotion authority, computes working sets, and
records promotion, rollover, and retention facts. SQLite remains a ledger, not
project memory.
"""
