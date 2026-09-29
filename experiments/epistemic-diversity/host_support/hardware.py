"""Native Windows CIM and NVIDIA observations, including multiple GPU adapters."""

import json
import os
import platform
import re
import sys
import xml.etree.ElementTree as ET
from typing import Literal

from host_support.commands import CIM_SCRIPT, POWERSHELL_PREFIX, Commands
from host_support.models import CPU, GPU, Check, Memory, PlatformInfo, RuntimeInfo


def positive_integer(value: object) -> int | None:
    if isinstance(value, bool):
        return None
    try:
        number = int(str(value))
        return number if number > 0 else None
    except ValueError:
        return None


def parse_nvidia(text: str) -> list[GPU]:
    """nvidia-smi -q -x reports driver-supported CUDA, not installed CUDA runtime."""
    if "<!ENTITY" in text or len(text) > 2_000_000:
        raise ValueError("Unsupported NVIDIA XML")
    try:
        root = ET.fromstring(text)
    except ET.ParseError as exc:
        raise ValueError("Malformed NVIDIA XML") from exc
    if root.tag != "nvidia_smi_log":
        raise ValueError("Unexpected NVIDIA root")
    cards = []
    for node in root.findall("gpu"):
        name = node.findtext("product_name")
        if not name or name in {"N/A", "Unknown"}:
            raise ValueError("GPU name unavailable")
        memory = node.findtext("fb_memory_usage/total", "")
        match = re.fullmatch(r"\s*(\d+)\s*MiB\s*", memory)
        driver, cuda = root.findtext("driver_version"), root.findtext("cuda_version")
        cards.append(
            GPU(
                name=name,
                uuid=node.findtext("uuid"),
                vram_mb=int(match[1]) if match and int(match[1]) > 0 else None,
                driver_version=driver if driver not in {"N/A", "Unknown"} else None,
                driver_supported_cuda=cuda if cuda not in {"N/A", "Unknown"} else None,
            )
        )
    return cards


def capture_hardware(
    commands: Commands,
) -> tuple[PlatformInfo, CPU, Memory, list[GPU], list[Check]]:
    host = PlatformInfo(
        os=platform.system(), version=platform.version(), architecture=platform.machine() or None
    )
    cpu = CPU(model=platform.processor() or None, logical_count=os.cpu_count())
    memory = Memory()
    checks = [
        Check(
            name="windows",
            status="pass" if host.os == "Windows" else "fail",
            detail=f"Observed OS: {host.os}",
        )
    ]
    if host.os == "Windows":
        result = commands.run([*POWERSHELL_PREFIX, CIM_SCRIPT])
        try:
            data = json.loads(result.output or "null")
            if not isinstance(data, dict):
                raise ValueError("CIM unavailable")
            host.version = str(data["version"]) if data.get("version") else None
            host.build = str(data["build"]) if data.get("build") else None
            # Keep platform.machine() (AMD64/ARM64) rather than CIM's localized bitness string.
            cpu.model = str(data["cpu"]) if data.get("cpu") else None
            memory.total_bytes = positive_integer(data.get("memory"))
        except (ValueError, TypeError):
            checks.append(Check(name="windows_cim", status="warning", detail="CIM unavailable"))
    checks += [
        Check(
            name="cpu",
            status="pass" if cpu.model else "warning",
            detail="CPU model observed" if cpu.model else "CPU model unavailable",
        ),
        Check(
            name="ram",
            status="pass" if memory.total_bytes else "warning",
            detail="Physical RAM observed" if memory.total_bytes else "Physical RAM unavailable",
        ),
        Check(
            name="nvidia_smi",
            status="pass" if commands.which("nvidia-smi") else "fail",
            detail="NVIDIA management CLI availability",
        ),
    ]
    result = commands.run(["nvidia-smi", "-q", "-x"])
    status: Literal["pass", "fail"]
    try:
        cards = parse_nvidia(result.output or "")
        status = "pass" if cards else "fail"
        detail = f"Observed {len(cards)} NVIDIA GPU(s)"
    except ValueError:
        cards, status, detail = [], "fail", "NVIDIA data unavailable or malformed"
    checks.append(Check(name="nvidia_gpu", status=status, detail=detail))
    checks.append(
        Check(
            name="vram",
            status="pass" if cards and all(c.vram_mb for c in cards) else "fail",
            detail="VRAM must be reported for every detected adapter",
        )
    )
    return host, cpu, memory, cards, checks


def capture_runtime(commands: Commands) -> tuple[RuntimeInfo, list[Check]]:
    uv = commands.run(["uv", "--version"])
    commit = commands.run(["git", "rev-parse", "HEAD"])
    branch = commands.run(["git", "branch", "--show-current"])
    dirty = commands.run(["git", "status", "--porcelain", "--untracked-files=normal"])
    valid_git = bool(
        commit.output
        and re.fullmatch(r"[a-f0-9]{40,64}", commit.output)
        and branch.output is not None
        and dirty.output is not None
    )
    info = RuntimeInfo(
        python=platform.python_version(),
        python_utf8_mode=bool(sys.flags.utf8_mode),
        uv_version=uv.output,
        git_commit=commit.output if valid_git else None,
        git_branch=(branch.output or "DETACHED") if valid_git else None,
        git_dirty=bool(dirty.output) if valid_git else None,
    )
    return info, [
        Check(
            name="python",
            status="pass" if sys.version_info >= (3, 12) else "fail",
            detail=info.python,
        ),
        Check(
            name="python_utf8",
            status="pass" if info.python_utf8_mode else "warning",
            detail="Use python -X utf8 or PYTHONUTF8=1 for frozen UTF-8 research files",
        ),
        Check(name="uv", status="pass" if uv.output else "fail", detail="uv availability"),
        Check(
            name="git",
            status="pass" if valid_git else "fail",
            detail="Commit, branch and dirty state availability",
        ),
    ]
