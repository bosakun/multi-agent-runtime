"""Verify hashes recorded by a Guided Review UI v2 bundle manifest."""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from review_v3.html_review_v2.renderer import renderer_hash  # noqa: E402
from review_v3.storage import file_hash  # noqa: E402


def verify(bundle):
    bundle = Path(bundle)
    manifest_path = bundle / "render-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    errors = []
    for name, expected in manifest["html_sha256"].items():
        target = bundle / name
        actual = file_hash(target) if target.is_file() else None
        if actual != expected:
            errors.append(f"HTML hash mismatch: {name}")
    if renderer_hash() != manifest["renderer_source_hash"]:
        errors.append("Renderer source hash mismatch")
    source = Path(manifest["source_json_path"])
    if not source.is_file() or file_hash(source) != manifest["source_json_sha256"]:
        errors.append("Source JSON missing or hash mismatch")
    translation_name = manifest.get("translation_asset_path")
    translation_hash = manifest.get("translation_asset_sha256")
    if translation_name and (
        not Path(translation_name).is_file() or file_hash(translation_name) != translation_hash
    ):
        errors.append("Translation asset missing or hash mismatch")
    if errors:
        return {"valid": False, "errors": errors}
    return {
        "valid": True,
        "phase": manifest["phase"],
        "case_aliases": manifest["case_aliases"],
        "human_review_started": manifest["human_review_started"],
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle", help="Path to one generated phase bundle")
    result = verify(parser.parse_args().bundle)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result["valid"] else 1)
