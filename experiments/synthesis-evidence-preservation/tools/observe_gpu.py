"""Read-only host observations; never issue a model generation request."""

import json
import subprocess
import sys
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path

STUDY = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(STUDY / "src"))
import httpx  # noqa: E402
from synthesis_study.io import exclusive  # noqa: E402

samples = []
with httpx.Client(
    base_url="http://127.0.0.1:11434", timeout=10, trust_env=False, follow_redirects=False
) as client:
    for number in range(10):
        query = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=name,driver_version,utilization.gpu,memory.used,"
                "memory.total,temperature.gpu,power.draw",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        sample = {
            "time": datetime.now(UTC).isoformat(),
            "sample": number + 1,
            "gpu_csv": query.stdout.strip(),
            "residency": client.get("/api/ps").raise_for_status().json(),
        }
        samples.append(sample)
        print(json.dumps({"sample": number + 1, "gpu_csv": sample["gpu_csv"]}), flush=True)
        if number < 9:
            time.sleep(5)
exclusive(
    STUDY / "reports" / ("gpu-observations-" + uuid.uuid4().hex + ".json"),
    {
        "generation_calls": 0,
        "samples": samples,
        "interpretation": (
            "GPU utilization is host-level sampling, not per-call compute attribution"
        ),
    },
)
