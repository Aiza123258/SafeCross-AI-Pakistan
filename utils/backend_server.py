"""SafeCross AI - local FastAPI backend launcher for Streamlit deployments."""

import os
import socket
import subprocess
import sys
import time
from pathlib import Path


HOST = "127.0.0.1"
PORT = 8000


def _port_open(host: str = HOST, port: int = PORT) -> bool:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(0.25)
    try:
        return sock.connect_ex((host, port)) == 0
    finally:
        sock.close()


def ensure_backend_running() -> bool:
    """Start FastAPI once inside the same Streamlit machine if needed."""
    if _port_open():
        return True

    root = Path(__file__).resolve().parent.parent
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"

    log_path = root / "backend_error.log"

    try:
        log_file = open(log_path, "a")
        subprocess.Popen(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "backend.main:app",
                "--host",
                HOST,
                "--port",
                str(PORT),
            ],
            cwd=str(root),
            env=env,
            stdout=log_file,
            stderr=log_file,
            start_new_session=True,
        )
    except Exception:
        return False

    for _ in range(30):
        if _port_open():
            return True
        time.sleep(0.2)

    return False
