"""
Automated PyInstaller Build Script for Rogue 2D: Dungeon Descent
Builds a standalone Rogue2.exe with custom icon, bundled assets, and no console window.
Outputs directly to:
  Rogue2.exe (project root; canonical game executable)
"""

import os
import sys
import subprocess

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def main():
    os.chdir(PROJECT_ROOT)
    print(f"[Build] Target project directory: {PROJECT_ROOT}")

    main_py = os.path.join(PROJECT_ROOT, "main.py")
    icon_ico = os.path.join(PROJECT_ROOT, "assets", "icon.ico")
    assets_dir = os.path.join(PROJECT_ROOT, "assets")
    settings_json = os.path.join(PROJECT_ROOT, "settings.json")

    if not os.path.exists(main_py):
        print(f"[Error] main.py not found at {main_py}")
        sys.exit(1)

    # Prepare PyInstaller command: disable UPX and exclude win32ui/Pythonwin MFC to prevent decompression code -3 error
    pyinstaller_cmd = [
        sys.executable,
        "-m", "PyInstaller",
        "--name=Rogue2",
        "--onefile",
        f"--distpath={PROJECT_ROOT}",
        "--windowed",
        "--clean",
        "--noconfirm",
        "--noupx",
        "--exclude-module=Pythonwin",
        "--exclude-module=win32ui",
        "--exclude-module=tkinter",
        "--exclude-module=tcl",
        "--exclude-module=tk",
        f"--add-data={assets_dir};assets",
    ]

    if os.path.exists(icon_ico):
        pyinstaller_cmd.append(f"--icon={icon_ico}")
        print(f"[Build] Using icon: {icon_ico}")

    if os.path.exists(settings_json):
        pyinstaller_cmd.append(f"--add-data={settings_json};.")

    pyinstaller_cmd.append(main_py)

    print("[Build] Running PyInstaller compilation...")
    print(f"Command: {' '.join(pyinstaller_cmd)}")

    result = subprocess.run(pyinstaller_cmd)
    if result.returncode != 0:
        print(f"[Error] PyInstaller failed with exit code {result.returncode}")
        sys.exit(result.returncode)

    root_exe = os.path.join(PROJECT_ROOT, "Rogue2.exe")
    if not os.path.exists(root_exe):
        print(f"[Error] Expected output {root_exe} was not found.")
        sys.exit(1)

    file_size_mb = os.path.getsize(root_exe) / (1024 * 1024)
    print("=" * 60)
    print(f" [SUCCESS] Rogue2.exe successfully built! ({file_size_mb:.2f} MB)")
    print(f" Location: {root_exe}")
    print("=" * 60)

if __name__ == "__main__":
    main()
