"""Portable environment observations: unavailable measurements stay null."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class Observation(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Check(Observation):
    name: str
    status: Literal["pass", "fail", "warning"]
    detail: str


class PlatformInfo(Observation):
    os: str
    version: str | None = None
    build: str | None = None
    architecture: str | None = None


class CPU(Observation):
    model: str | None = None
    logical_count: int | None = None


class Memory(Observation):
    total_bytes: int | None = None


class GPU(Observation):
    vendor: str = "NVIDIA"
    name: str
    uuid: str | None = None
    vram_mb: int | None = None
    driver_version: str | None = None
    driver_supported_cuda: str | None = None
    installed_cuda_runtime: str | None = None


class Residency(Observation):
    state: Literal["full_gpu", "partial_gpu", "cpu", "loaded_unknown", "not_loaded", "unavailable"]
    source: str
    processor: str | None = None
    gpu_percent: int | None = None
    cpu_percent: int | None = None
    size_bytes: int | None = None
    size_vram_bytes: int | None = None
    gpu_memory_fraction: float | None = None
    context_length: int | None = None
    digest: str | None = None


class Ollama(Observation):
    endpoint: str | None = None
    model: str = "qwen3:14b"
    version: str | None = None
    digest: str | None = None
    model_size_bytes: int | None = None
    quantization: str | None = None
    model_context_lengths: dict[str, int] = Field(default_factory=dict)
    residency: Residency = Field(
        default_factory=lambda: Residency(state="unavailable", source="none")
    )


class RuntimeInfo(Observation):
    python: str
    python_utf8_mode: bool
    uv_version: str | None = None
    git_commit: str | None = None
    git_branch: str | None = None
    git_dirty: bool | None = None


class Fingerprint(Observation):
    schema_version: str = "host-environment-1.0.0"
    captured_at: str
    execution_profile: Literal["local_ollama"] = "local_ollama"
    platform: PlatformInfo
    cpu: CPU
    memory: Memory
    gpu: list[GPU]
    gpu_count: int | None
    ollama: Ollama
    runtime: RuntimeInfo
    checks: list[Check]
    generation_calls: Literal[0] = 0

    @property
    def passed(self) -> bool:
        return all(check.status != "fail" for check in self.checks)
