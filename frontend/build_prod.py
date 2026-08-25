"""
JudiQ AI — Production Frontend Build & Subresource Integrity (SRI) Generator
Optimizes frontend assets for CDN delivery with SHA-384 cryptographic integrity hashes.
"""

import hashlib
import os
import re
from pathlib import Path

FRONTEND_DIR = Path(__file__).resolve().parent

def generate_sri_hash(file_path: Path) -> str:
    with open(file_path, "rb") as f:
        digest = hashlib.sha384(f.read()).digest()
    import base64
    return f"sha384-{base64.b64encode(digest).decode()}"

def build_production_manifest():
    manifest = {}
    print("[*] Building JudiQ AI Production Frontend Manifest...")

    critical_files = [
        "styles.css",
        "renderer.js",
        "wizard.js",
        "api.js",
        "draft_templates.js",
        "js/main.js",
        "js/modules/store.js",
        "js/modules/charts.js",
        "js/modules/simulator.js",
        "js/modules/counsel_dock.js"
    ]

    for rel_path in critical_files:
        full_path = FRONTEND_DIR / rel_path
        if full_path.exists():
            sri = generate_sri_hash(full_path)
            size_kb = os.path.getsize(full_path) / 1024
            manifest[rel_path] = {
                "sri_integrity": sri,
                "size_kb": round(size_kb, 2)
            }
            print(f"  + {rel_path:<25} [{size_kb:>6.2f} KB] SRI: {sri[:24]}...")

    import json
    manifest_path = FRONTEND_DIR / "asset_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print(f"[+] Production Asset Manifest generated at: {manifest_path}")
    return manifest

if __name__ == "__main__":
    build_production_manifest()
