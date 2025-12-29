#!/usr/bin/env python3
"""
YangzLinuxVpnClient - Privileged Helper

Runs as root via pkexec/polkit.
Communicates strictly via JSON on stdin/stdout.

Supported actions:
- list_profiles
- install_profile
- connect
- disconnect
- status
"""

import json
import sys
import subprocess
from pathlib import Path

# ==================================================
# Constants & Security Guardrails
# ==================================================

OPENVPN_DIR = "/etc/openvpn"

ALLOWED_NAME_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-"

DISALLOWED_DIRECTIVES = (
    "auth-user-pass",
    "script-security",
    "up ",
    "down ",
    "plugin ",
    "management ",
)

# ==================================================
# Helpers
# ==================================================

def emit_error(code: str, message: str = None):
    print(json.dumps({
        "status": "error",
        "code": code,
        "message": message or code.replace("_", " ").title()
    }))
    sys.exit(1)


def emit_ok(payload=None):
    data = {"status": "ok"}
    if payload:
        data.update(payload)
    print(json.dumps(data))
    sys.exit(0)


def validate_profile_name(name: str):
    if not name:
        emit_error("INVALID_PROFILE_NAME")

    for ch in name:
        if ch not in ALLOWED_NAME_CHARS:
            emit_error("INVALID_PROFILE_NAME")


def profile_paths(name: str):
    base = Path(OPENVPN_DIR)
    conf = base / f"{name}.conf"
    auth = base / f"{name}.auth"

    # Prevent traversal / symlink abuse
    if not conf.resolve().parent.samefile(base):
        emit_error("INVALID_PATH")

    return conf, auth


def systemctl(args):
    subprocess.run(
        ["systemctl"] + args,
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )


def sanitize_ovpn(content: str) -> str:
    """Strip directives we explicitly control."""
    cleaned = []
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith(DISALLOWED_DIRECTIVES):
            continue
        cleaned.append(line)
    return "\n".join(cleaned) + "\n"


def write_auth_file(path: Path, username: str, password: str):
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"{username}\n{password}\n")
    path.chmod(0o600)


def write_conf_file(path: Path, content: str, auth_path: Path):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
        f.write(f"\nauth-user-pass {auth_path}\n")
    path.chmod(0o644)


def get_active_vpns():
    """Return list of active openvpn@*.service profile names."""
    result = subprocess.run(
        ["systemctl", "list-units", "--type=service", "--state=active"],
        capture_output=True,
        text=True,
        check=True
    )

    active = []
    for line in result.stdout.splitlines():
        if line.startswith("openvpn@") and ".service" in line:
            name = line.split("@", 1)[1].split(".service", 1)[0]
            active.append(name)
    return active


# ==================================================
# Action Handlers
# ==================================================

def handle_list_profiles():
    profiles = sorted(p.stem for p in Path(OPENVPN_DIR).glob("*.conf"))
    emit_ok({"profiles": profiles})


def handle_install_profile(data):
    name = data.get("profile_name")
    ovpn = data.get("ovpn_content")
    username = data.get("username")
    password = data.get("password")

    validate_profile_name(name)

    if not ovpn or not username or not password:
        emit_error("MISSING_FIELDS")

    conf_path, auth_path = profile_paths(name)

    # Fail-if-exists (locked design decision)
    if conf_path.exists() or auth_path.exists():
        emit_error("PROFILE_EXISTS", "VPN profile already exists")

    sanitized = sanitize_ovpn(ovpn)

    write_auth_file(auth_path, username, password)
    write_conf_file(conf_path, sanitized, auth_path)

    systemctl(["daemon-reload"])
    systemctl(["enable", f"openvpn@{name}"])

    emit_ok()


def handle_connect(data):
    name = data.get("profile_name")
    validate_profile_name(name)

    conf_path, _ = profile_paths(name)
    if not conf_path.exists():
        emit_error("PROFILE_NOT_FOUND")

    active = get_active_vpns()
    if active and name not in active:
        emit_error("ANOTHER_VPN_ACTIVE", "Another VPN is already active")

    systemctl(["start", f"openvpn@{name}"])
    emit_ok()


def handle_disconnect(data):
    name = data.get("profile_name")
    validate_profile_name(name)

    systemctl(["stop", f"openvpn@{name}"])
    emit_ok()


def handle_status(data):
    name = data.get("profile_name")
    validate_profile_name(name)

    result = subprocess.run(
        ["systemctl", "is-active", f"openvpn@{name}"],
        capture_output=True,
        text=True
    )

    state = result.stdout.strip()

    emit_ok({
        "active": state == "active",
        "state": state
    })


# ==================================================
# Dispatcher
# ==================================================

def main():
    try:
        data = json.load(sys.stdin)
        action = data.get("action")

        if action == "list_profiles":
            handle_list_profiles()
        elif action == "install_profile":
            handle_install_profile(data)
        elif action == "connect":
            handle_connect(data)
        elif action == "disconnect":
            handle_disconnect(data)
        elif action == "status":
            handle_status(data)
        else:
            emit_error("UNKNOWN_ACTION")

    except json.JSONDecodeError:
        emit_error("INVALID_JSON")

    except subprocess.CalledProcessError:
        emit_error("SYSTEMCTL_FAILED", "System service operation failed")

    except Exception as e:
        emit_error("INTERNAL_ERROR", str(e))


if __name__ == "__main__":
    main()
