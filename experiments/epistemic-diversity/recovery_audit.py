"""Print an offline workload audit. No writes, network, model calls or recovery attempts."""

import json

from operational_recovery.workload import audit

if __name__ == "__main__":
    print(json.dumps(audit(), ensure_ascii=False, indent=2))
