#!/usr/bin/env python3
"""CivicLens Demo Reset Tool.

Resets system state and populates clean, deterministic synthetic demo data for
both Citizen and Admin console demonstration workflows.
"""
from __future__ import annotations

import os
import subprocess
import sys


def main() -> int:
    print("==========================================================")
    print("           CIVICLENS DEMO ENVIRONMENT RESET               ")
    print("==========================================================")

    here = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(here)
    backend_dir = os.path.join(repo_root, "backend")

    print("[STEP 1/3] Executing Database Alembic Migration (Head)...")
    r_mig = subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], cwd=backend_dir)
    if r_mig.returncode != 0:
        print("Alembic migration failed during demo reset.")
        return 1

    print("[STEP 2/3] Seeding Deterministic Demo Data...")
    r_seed = subprocess.run([sys.executable, "-m", "app.seeds.seed_all"], cwd=backend_dir)
    if r_seed.returncode != 0:
        print("Dev seeding failed during demo reset.")
        return 1

    print("[STEP 3/3] Demo Reset Complete & Ready for Presentation.")
    print("----------------------------------------------------------")
    print(" - Citizen Web App: http://localhost:3000")
    print(" - Admin Console:   http://localhost:3001")
    print(" - API Contract:    http://localhost:8000/docs")
    print("==========================================================\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
