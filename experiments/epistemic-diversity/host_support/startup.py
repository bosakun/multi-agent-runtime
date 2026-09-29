"""Fail-closed startup checks. Never terminate a process or attach to an existing server."""

import json
import platform
import socket
from collections.abc import Callable
from typing import Any

from host_support.commands import POWERSHELL_PREFIX, PROCESS_SCRIPT, Commands


def port_available() -> bool:
    """Check both loopback families, closing sockets before Ollama starts.

    This is a preflight, not a reservation: Ollama must still handle bind races.
    """
    families = [(socket.AF_INET, "127.0.0.1")]
    if socket.has_ipv6:
        families.append((socket.AF_INET6, "::1"))
    for family, address in families:
        try:
            with socket.socket(family, socket.SOCK_STREAM) as listener:
                if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
                    listener.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
                if family == socket.AF_INET6:
                    listener.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 1)
                listener.bind((address, 11434))
        except OSError:
            return False
    return True


def startup_check(
    commands: Commands, *, port_probe: Callable[[], bool] = port_available
) -> dict[str, Any]:
    if platform.system() != "Windows":
        return {"allowed": False, "reason": "Native Windows required"}
    if not commands.which("ollama"):
        return {"allowed": False, "reason": "Ollama CLI unavailable"}
    result = commands.run([*POWERSHELL_PREFIX, PROCESS_SCRIPT])
    try:
        if result.output is None:
            raise ValueError("Process query failed")
        processes = json.loads(result.output) if result.output else []
        if isinstance(processes, dict):
            processes = [processes]
        if not isinstance(processes, list) or any(
            not isinstance(p, dict) or "ProcessName" not in p or "Id" not in p for p in processes
        ):
            raise ValueError("Malformed process query")
    except ValueError:
        return {"allowed": False, "reason": "Cannot inspect existing processes; stop safely"}
    free = port_probe()
    if processes or not free:
        return {
            "allowed": False,
            "reason": "existing Ollama server detected or port 11434 conflict",
            "processes": processes,
            "port_available": free,
            "action": "Quit Ollama via its tray menu / original terminal yourself, then recheck. "
            "Do not assume environment changes apply to an already running server.",
        }
    return {"allowed": True, "reason": "No Ollama process and port 11434 is available"}
