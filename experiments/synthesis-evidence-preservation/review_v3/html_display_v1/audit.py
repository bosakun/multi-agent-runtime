"""Read-only byte/pointer/projection checks; no annotation or research metrics."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from review_v3.bilingual import text_hash  # noqa: E402
from review_v3.html_display_v1.renderer import pointer_get, render, renderer_hash  # noqa: E402
from review_v3.storage import file_hash, read  # noqa: E402


def verify(root):
    root = Path(root)
    manifest = read(root / "render-manifest.json")
    if file_hash(manifest["source_json_path"]) != manifest["source_json_sha256"]:
        raise ValueError("Source JSON byte hash changed")
    if manifest["renderer_source_hash"] != renderer_hash():
        raise ValueError("Renderer sources changed since generation")
    if file_hash(root / "index.html") != manifest["index_html_sha256"]:
        raise ValueError("Phase index hash mismatch")
    source = read(manifest["source_json_path"])
    asset = read(manifest["translation_json_path"]) if manifest["translation_json_path"] else None
    if (
        asset
        and file_hash(manifest["translation_json_path"]) != manifest["translation_json_sha256"]
    ):
        raise ValueError("Translation JSON byte hash changed")
    for entry in manifest["entries"]:
        path = root / entry["html_file"]
        if path.parent != root or file_hash(path) != entry["html_sha256"]:
            raise ValueError("HTML path/hash mismatch")
        unit = pointer_get(source, entry["source_pointer"]) if entry["source_pointer"] else source
        if render(unit, manifest["phase"], asset)[1] != path.read_bytes():
            raise ValueError("HTML differs from deterministic canonical-source projection")
        for pair in entry["text_lineage"]:
            en = pointer_get(source, pair["source_pointer"])
            pointer = pair["translation_pointer"]
            if pointer is None:
                ja = ""
            elif pointer.startswith("translation_asset/"):
                ja = pointer_get(asset, pointer.split("/", 1)[1])
            else:
                ja = pointer_get(source, pointer)
            if text_hash(en) != pair["english_sha256"] or text_hash(ja) != pair["japanese_sha256"]:
                raise ValueError("Original/translation pointer and text hash mismatch")
    return dict(
        passed=True,
        phase=manifest["phase"],
        cases_checked=len(manifest["entries"]),
        manifest_sha256=file_hash(root / "render-manifest.json"),
        renderer_source_hash=manifest["renderer_source_hash"],
    )


if __name__ == "__main__":
    print(json.dumps(verify(sys.argv[1]), indent=2))
