"""Bounded read-only native commands; arguments and environment are never shell-expanded."""

import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True)
class CommandResult:
    output: str | None
    error: str | None = None


class Commands(Protocol):
    def which(self, name: str) -> str | None: ...
    def run(self, args: list[str], *, env: dict[str, str] | None = None) -> CommandResult: ...


class NativeCommands:
    """No environment dump, stderr forwarding, shell=True, or executable path interpolation."""

    def __init__(self, repository: Path) -> None:
        self.repository = repository

    def which(self, name: str) -> str | None:
        return shutil.which(name)

    def run(self, args: list[str], *, env: dict[str, str] | None = None) -> CommandResult:
        binary = self.which(args[0])
        if binary is None:
            return CommandResult(None, "executable_unavailable")
        try:
            result = subprocess.run(
                [binary, *args[1:]],
                cwd=self.repository,
                shell=False,
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=10,
                env={**os.environ, **(env or {})},
            )
        except subprocess.TimeoutExpired:
            return CommandResult(None, "command_timeout")
        except OSError:
            return CommandResult(None, "command_unavailable")
        if result.returncode:
            return CommandResult(None, f"exit_{result.returncode}")
        return CommandResult(result.stdout.strip())


POWERSHELL_PREFIX = ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command"]
UTF8 = "[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false); "
CIM_SCRIPT = UTF8 + (
    "$ErrorActionPreference='Stop'; "
    "$o=Get-CimInstance Win32_OperatingSystem; $s=Get-CimInstance Win32_ComputerSystem; "
    "$c=@(Get-CimInstance Win32_Processor); "
    "[ordered]@{version=$o.Version; build=$o.BuildNumber; architecture=$o.OSArchitecture; "
    "cpu=($c.Name -join '; '); memory=$s.TotalPhysicalMemory} | ConvertTo-Json -Compress"
)
PROCESS_SCRIPT = UTF8 + (
    "$ErrorActionPreference='Stop'; "
    "@(Get-Process | Where-Object { $_.ProcessName -like 'ollama*' } | "
    "Select-Object ProcessName,Id) | ConvertTo-Json -Compress"
)
