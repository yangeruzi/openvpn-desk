import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import json
import subprocess
from pathlib import Path
from typing import List, Dict, Any


HELPER_PATH = "/usr/lib/openvpn-desk/helper.py"
PROFILE_DIR = Path("/etc/openvpn-desk/profiles")
SERVICE_PREFIX = "openvpn-desk@"


class VpnBackendError(Exception):
    """Raised for all backend / helper related errors."""
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


class VpnBackend:
    """
    Unprivileged backend that communicates with the
    privileged helper via pkexec + JSON.
    """

    def _call_helper(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call the privileged helper and return parsed JSON.

        Raises VpnBackendError on failure.
        """
        try:
            proc = subprocess.run(
                ["pkexec", HELPER_PATH],
                input=json.dumps(payload),
                text=True,
                capture_output=True
            )
        except FileNotFoundError:
            raise VpnBackendError(
                "HELPER_NOT_FOUND",
                "VPN helper not installed"
            )

        if proc.returncode != 0:
            # Helper always returns JSON on stdout
            try:
                data = json.loads(proc.stdout)
                raise VpnBackendError(
                    data.get("code", "UNKNOWN_ERROR"),
                    data.get("message", "Unknown error")
                )
            except json.JSONDecodeError:
                raise VpnBackendError(
                    "HELPER_FAILED",
                    proc.stderr.strip() or "Helper execution failed"
                )

        try:
            return json.loads(proc.stdout)
        except json.JSONDecodeError:
            raise VpnBackendError(
                "INVALID_HELPER_RESPONSE",
                "Invalid response from VPN helper"
            )

    # -------------------------------------------------
    # Public API (used by GTK)
    # -------------------------------------------------

    def list_profiles(self) -> List[str]:
        if not PROFILE_DIR.exists():
            return []
        try:
            return sorted(path.stem for path in PROFILE_DIR.glob("*.conf"))
        except OSError:
            resp = self._call_helper({
                "action": "list_profiles"
            })
            return resp.get("profiles", [])

    def install_profile(
        self,
        profile_name: str,
        ovpn_content: str,
        username: str,
        password: str
    ) -> None:
        self._call_helper({
            "action": "install_profile",
            "profile_name": profile_name,
            "ovpn_content": ovpn_content,
            "username": username,
            "password": password
        })

    def connect(self, profile_name: str) -> None:
        self._call_helper({
            "action": "connect",
            "profile_name": profile_name
        })

    def disconnect(self, profile_name: str) -> None:
        self._call_helper({
            "action": "disconnect",
            "profile_name": profile_name
        })

    def get_status(self, profile_name: str) -> Dict[str, Any]:
        try:
            proc = subprocess.run(
                ["systemctl", "is-active", f"{SERVICE_PREFIX}{profile_name}"],
                text=True,
                capture_output=True
            )
        except FileNotFoundError:
            raise VpnBackendError(
                "SYSTEMCTL_NOT_FOUND",
                "systemctl is not available on this system"
            )

        state = (proc.stdout or proc.stderr).strip() or "unknown"
        return {
            "active": state == "active",
            "state": state
        }
