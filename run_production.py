import os
import sys
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

def check_frontend_bundle():
    """Verify built frontend production assets exist before launching server."""
    dist_dir = BASE_DIR / "frontend" / "dist"
    index_file = dist_dir / "index.html"
    if not index_file.exists():
        print("[PRODUCTION CHECK] frontend/dist not found. Running production build...")
        frontend_dir = BASE_DIR / "frontend"
        try:
            cmd = "npm run build" if os.name == "nt" else "npm run build"
            subprocess.run(cmd, cwd=str(frontend_dir), shell=True, check=True)
            print("[PRODUCTION CHECK] Frontend built successfully.")
        except Exception as e:
            print(f"[WARNING] Could not build frontend automatically ({e}). Starting API server without UI bundle.")
    else:
        print(f"[PRODUCTION CHECK] Production frontend bundle verified at {dist_dir}.")

def run():
    print("=" * 70)
    print("NIRIKSHA: The AICTE Approval Control Room (PS 26262)")
    print("Starting Enterprise Production Server...")
    print("=" * 70)

    # 1. Check frontend bundle
    check_frontend_bundle()

    # 2. Database validation
    try:
        from app.database import check_db_connection
        diag = check_db_connection()
        print(f"[DATABASE CHECK] Status: {diag.get('status')} | Dialect: {diag.get('dialect')} | Neon: {diag.get('is_neon')}")
    except Exception as e:
        print(f"[DATABASE WARNING] Connectivity test warning: {e}")

    # 3. Launch production server
    port = int(os.getenv("PORT", "8000"))
    host = os.getenv("HOST", "0.0.0.0")

    if os.name == "nt":
        # Windows environment: WinSock does not support socket sharing across spawned processes (WinError 10022).
        # Run single-process high-throughput async event loop on Windows.
        import uvicorn
        print(f"[LAUNCH] Starting Uvicorn on http://{host}:{port} (Windows Async Mode)...")
        uvicorn.run("app.main:app", host=host, port=port, log_level=os.getenv("LOG_LEVEL", "info").lower())
    else:
        # Linux / Container environment: Run Gunicorn with Uvicorn workers
        print(f"[LAUNCH] Starting Gunicorn ASGI server on http://{host}:{port} using gunicorn.conf.py...")
        cmd = [
            sys.executable, "-m", "gunicorn",
            "-c", "gunicorn.conf.py",
            "app.main:app"
        ]
        os.execvp(cmd[0], cmd)

if __name__ == "__main__":
    run()
