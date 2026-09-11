"""
JudiQ AI — Android APK Compiler & Packager
------------------------------------------
Copies the embedded production frontend into android/app/src/main/assets/frontend/,
configures local Android SDK paths, and compiles the standalone APK using Gradle.
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path
from typing import Optional

ROOT_DIR = Path(__file__).resolve().parent
ANDROID_DIR = ROOT_DIR / "android"
FRONTEND_DIR = ROOT_DIR / "frontend"
ASSETS_DIR = ANDROID_DIR / "app" / "src" / "main" / "assets" / "frontend"
DIST_DIR = ROOT_DIR / "dist"

def detect_android_sdk() -> Optional[Path]:
    candidates = [
        os.environ.get("ANDROID_HOME"),
        os.environ.get("ANDROID_SDK_ROOT"),
        Path(os.environ.get("LOCALAPPDATA", "")) / "Android" / "Sdk",
        Path.home() / "AppData" / "Local" / "Android" / "Sdk",
    ]
    for c in candidates:
        if c:
            p = Path(c)
            if p.exists() and (p / "platform-tools").exists():
                return p
    return None

def sync_frontend_assets():
    print("[1/4] Synchronizing production frontend into Android assets...")
    
    # Run build_prod.py to update SRI hashes
    prod_script = FRONTEND_DIR / "build_prod.py"
    if prod_script.exists():
        subprocess.run([sys.executable, str(prod_script)], check=True)

    ASSETS_DIR.mkdir(parents=True, exist_ok=True)

    # Exclude development files, node_modules, and git files
    ignored_patterns = shutil.ignore_patterns(
        ".git*", "node_modules", "*.pyc", "__pycache__", "Dockerfile", "docker-compose*", "nginx.conf"
    )
    shutil.copytree(FRONTEND_DIR, ASSETS_DIR, ignore=ignored_patterns, dirs_exist_ok=True)
    print(f"      Assets copied to: {ASSETS_DIR}")

def ensure_local_properties(sdk_dir: Path):
    local_prop = ANDROID_DIR / "local.properties"
    escaped_path = str(sdk_dir).replace("\\", "\\\\")
    with open(local_prop, "w", encoding="utf-8") as f:
        f.write(f"sdk.dir={escaped_path}\n")
    print(f"[2/4] Configured Android SDK: {sdk_dir}")

def find_gradle_executable() -> str:
    # 1. Check user profile for pre-installed gradle distributions
    user_gradle_dists = Path.home() / ".gradle" / "wrapper" / "dists"
    if user_gradle_dists.exists():
        candidates = list(user_gradle_dists.glob("**/bin/gradle.bat"))
        if candidates:
            candidates.sort(reverse=True)
            return str(candidates[0])

    # 2. Check system PATH
    system_gradle = shutil.which("gradle")
    if system_gradle:
        return system_gradle

    # 3. Fallback to project gradlew wrapper
    gradlew = ANDROID_DIR / "gradlew.bat" if os.name == "nt" else ANDROID_DIR / "gradlew"
    return str(gradlew)

def compile_apk():
    print("\n[3/4] Compiling Android APK via Gradle...")
    gradle_bin = find_gradle_executable()
    print(f"      Using Gradle: {gradle_bin}")

    cmd = [gradle_bin, "assembleDebug", "--no-daemon"]
    result = subprocess.run(cmd, cwd=str(ANDROID_DIR))
    if result.returncode != 0:
        print(f"[-] Gradle build failed with code {result.returncode}")
        sys.exit(result.returncode)

def finalize_apk():
    print("\n[4/4] Verifying and copying compiled APK...")
    output_apk = ANDROID_DIR / "app" / "build" / "outputs" / "apk" / "debug" / "app-debug.apk"
    if not output_apk.exists():
        print(f"[-] Error: Compiled APK not found at {output_apk}")
        sys.exit(1)

    DIST_DIR.mkdir(exist_ok=True)
    target_apk = DIST_DIR / "JudiQ_AI.apk"
    shutil.copy2(output_apk, target_apk)

    size_mb = target_apk.stat().st_size / (1024 * 1024)
    print("=" * 70)
    print("  [+] SUCCESS! Android APK compiled and packaged successfully:")
    print(f"      Output APK: {target_apk}")
    print(f"      Size:       {size_mb:.2f} MB")
    print("      Package:    ai.judiq.app (Debug Standalone)")
    print("=" * 70)

def main():
    print("=" * 70)
    print("  JUDIQ AI — ANDROID APPLICATION COMPILER (APK)")
    print("=" * 70)

    sdk_dir = detect_android_sdk()
    if not sdk_dir:
        print("[-] Error: Android SDK not found in standard paths.")
        print("    Please set ANDROID_HOME or install Android SDK command-line tools.")
        sys.exit(1)

    sync_frontend_assets()
    ensure_local_properties(sdk_dir)
    compile_apk()
    finalize_apk()

if __name__ == "__main__":
    main()
