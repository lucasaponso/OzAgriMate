"""OzAgriMate platform entry point. Starts every implemented service container, each as its own process.

Usage:  python main.py          (Ctrl+C stops all services)

Each container keeps its own entry point (services/<name>/main.py) so it can also run and deploy
alone, e.g.  uvicorn services.telemetry_service.main:app --port 8002
"""

import signal
import subprocess
import sys
import time

SERVICES = [
    ("farm_management_service", 8001),     # APIs 1-4
    ("telemetry_service", 8002),           # APIs 5-6
    ("irrigation_control_service", 8003),  # APIs 7-8
]


def main() -> None:
    procs = []
    for name, port in SERVICES:
        cmd = [sys.executable, "-m", "uvicorn", f"services.{name}.main:app", "--port", str(port), "--log-level", "info"]
        procs.append(subprocess.Popen(cmd))
        print(f"  {name:<30} http://localhost:{port}/docs")

    def stop(*_):
        for p in procs:
            p.terminate()
        for p in procs:
            p.wait()
        sys.exit(0)

    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)
    while True:
        if any(p.poll() is not None for p in procs):
            print("A service exited unexpectedly; stopping all.")
            stop()
        time.sleep(1)


if __name__ == "__main__":
    main()
