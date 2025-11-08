import sys
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
CLIENT_DIR = REPO_ROOT / "client"
HOST_DIR = REPO_ROOT / "host"


def _run(cmd, cwd=None):
    print("\n>>>", " ".join(str(c) for c in cmd))
    res = subprocess.run(cmd, cwd=cwd or REPO_ROOT)
    if res.returncode != 0:
        print(f"Command failed with exit code {res.returncode}")
    return res.returncode


def _pyinstaller_cmd():
    # Prefer 'pyinstaller' if available, else fall back to 'python -m PyInstaller'
    try:
        test = subprocess.run(["pyinstaller", "--version"], capture_output=True)
        if test.returncode == 0:
            return ["pyinstaller"]
    except Exception:
        pass
    return [sys.executable, "-m", "PyInstaller"]


COMMON_FLAGS = ["--onefile", "--noconsole", "--clean", "--noconfirm"]


def build_client() -> int:
    cmd = _pyinstaller_cmd() + COMMON_FLAGS
    icon = CLIENT_DIR / "client_icon.ico"
    version_file = CLIENT_DIR / "version_file.txt"

    if not icon.exists():
        print(f"[WARN] Icon not found: {icon}. Build will proceed without a custom icon.")
    else:
        cmd += ["--icon", str(icon)]

    if version_file.exists():
        cmd += ["--version-file", str(version_file)]
    else:
        print(f"[WARN] Version file not found: {version_file}. FileDescription will not be embedded.")

    cmd += [
        "--hidden-import=mss",
        "--name",
        "service_host_messenger",
        str(CLIENT_DIR / "client_main.py"),
    ]
    return _run(cmd)


def build_host() -> int:
    ret = 0

    # Old server (8081)
    cmd_old = _pyinstaller_cmd() + COMMON_FLAGS + [
        "--hidden-import=flask",
        "--name", "SilentBeamServer",
        str(HOST_DIR / "server.py"),
    ]
    ret |= _run(cmd_old)

    # New server v2 (8082, /v2)
    cmd_v2 = _pyinstaller_cmd() + COMMON_FLAGS + [
        "--hidden-import=flask",
        "--name", "SilentBeamServerV2",
        str(HOST_DIR / "server_v2.py"),
    ]
    ret |= _run(cmd_v2)

    return ret


def main(argv):
    target = (argv[1].strip().lower() if len(argv) > 1 else "both")

    if target in ("client", "both"):
        rc = build_client()
        if rc != 0:
            sys.exit(rc)

    if target in ("host", "both"):
        rc = build_host()
        if rc != 0:
            sys.exit(rc)

    print("\nBuilds completed.")


if __name__ == "__main__":
    main(sys.argv)

