import os
import time
import subprocess
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DIST_DIR = BASE_DIR / "frontend" / "dist"
SCREENSHOTS_DIR = BASE_DIR / "screenshots"
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

ARTIFACT_DIR = Path(r"C:\Users\Valarmathi\.gemini\antigravity\brain\db86f052-29a7-4442-965e-7626e7ca5e25")
EDGE_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

class QuietHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DIST_DIR), **kwargs)
    def log_message(self, format, *args):
        pass

def run_server(httpd):
    httpd.serve_forever()

def main():
    port = 4173
    httpd = HTTPServer(("127.0.0.1", port), QuietHandler)
    server_thread = threading.Thread(target=run_server, args=(httpd,), daemon=True)
    server_thread.start()
    print(f"HTTP Server started on 127.0.0.1:{port}")
    time.sleep(1)

    views = [
        ("1_application_tracking_dashboard.png", f"http://127.0.0.1:{port}/#tracking"),
        ("2_institution_records_registry.png", f"http://127.0.0.1:{port}/#records"),
        ("3_predictive_sla_control_room.png", f"http://127.0.0.1:{port}/#sla-alerts"),
    ]

    for filename, url in views:
        out_path = SCREENSHOTS_DIR / filename
        cmd = [
            EDGE_PATH,
            "--headless=new",
            "--disable-gpu",
            "--window-size=1500,980",
            "--hide-scrollbars",
            f"--screenshot={out_path}",
            url
        ]
        print(f"Capturing {filename} from {url}...")
        subprocess.run(cmd, check=True)
        print(f"Saved to {out_path} ({out_path.stat().st_size} bytes)")

        # Copy to artifact dir as well
        if ARTIFACT_DIR.exists():
            art_path = ARTIFACT_DIR / filename
            with open(out_path, "rb") as f_src, open(art_path, "wb") as f_dst:
                f_dst.write(f_src.read())
            print(f"Copied to artifact dir: {art_path}")

    httpd.shutdown()
    print("All 3 screenshots captured successfully!")

if __name__ == "__main__":
    main()
