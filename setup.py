"""One-time setup for anime-cli. Run: python setup.py"""
import os
import platform
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
VENV = os.path.join(ROOT, "venv")
SYSTEM = platform.system()  # "Linux", "Windows", "Darwin"

if SYSTEM == "Windows":
    VENV_PYTHON = os.path.join(VENV, "Scripts", "python.exe")
else:
    VENV_PYTHON = os.path.join(VENV, "bin", "python")

# program to look for -> package name for each package manager
TOOLS = {
    "ffmpeg": {"pacman": "ffmpeg", "apt": "ffmpeg", "dnf": "ffmpeg", "brew": "ffmpeg",
               "winget": "Gyan.FFmpeg"},
    "mpv": {"pacman": "mpv", "apt": "mpv", "dnf": "mpv", "brew": "mpv",
            "winget": "shinchiro.mpv"},
    "node": {"pacman": "nodejs", "apt": "nodejs", "dnf": "nodejs", "brew": "node",
             "winget": "OpenJS.NodeJS.LTS"},
    "npm": {"pacman": "npm", "apt": "npm", "dnf": "npm", "brew": None, "winget": None},
    "git": {"pacman": "git", "apt": "git", "dnf": "git", "brew": "git",
            "winget": "Git.Git"},
}


def run(cmd, **kwargs):
    print("  $", " ".join(cmd))
    return subprocess.run(cmd, **kwargs)


def package_manager():
    if SYSTEM == "Windows":
        return "winget" if shutil.which("winget") else None
    if SYSTEM == "Darwin":
        return "brew" if shutil.which("brew") else None
    for pm in ("pacman", "apt", "dnf"):
        if shutil.which(pm):
            return pm
    return None


def install_system_tools():
    print("\n[1/5] System tools (ffmpeg, mpv, node, npm, git)")
    missing = [t for t in TOOLS if not shutil.which(t)]
    if not missing:
        print("  All installed.")
        return
    pm = package_manager()
    if pm is None:
        print("  Could not find a package manager. Please install by hand:", ", ".join(missing))
        return
    packages = [TOOLS[t][pm] for t in missing if TOOLS[t][pm]]
    if not packages:
        return
    print("  Missing:", ", ".join(missing))
    if pm == "pacman":
        run(["sudo", "pacman", "-S", "--needed", "--noconfirm", *packages])
    elif pm == "apt":
        run(["sudo", "apt", "install", "-y", *packages])
    elif pm == "dnf":
        run(["sudo", "dnf", "install", "-y", *packages])
    elif pm == "brew":
        run(["brew", "install", *packages])
    elif pm == "winget":
        for p in packages:
            run(["winget", "install", "--id", p, "-e", "--accept-package-agreements",
                 "--accept-source-agreements"])
        print("  On Windows, close and reopen the terminal so the new programs are found.")


def make_venv_and_install_python_packages():
    print("\n[2/5] Python virtual environment and packages")
    if not os.path.exists(VENV_PYTHON):
        run([sys.executable, "-m", "venv", VENV], check=True)
    run([VENV_PYTHON, "-m", "pip", "install", "-r", os.path.join(ROOT, "requirements.txt")],
        check=True)


def install_node_packages():
    print("\n[3/5] Node packages (JustalK)")
    if not shutil.which("npm"):
        print("  npm not found, skipping. Install Node.js and run setup again.")
        return
    run(["npm", "install"], cwd=ROOT, shell=(SYSTEM == "Windows"))


def create_settings():
    print("\n[4/5] settings.xml")
    settings = os.path.join(ROOT, "settings.xml")
    example = os.path.join(ROOT, "settings.example.xml")
    if os.path.exists(settings):
        print("  settings.xml already exists, leaving it alone.")
    elif os.path.exists(example):
        shutil.copy(example, settings)
        print("  Created settings.xml from settings.example.xml")
    else:
        print("  settings.example.xml not found.")


def install_kuhi():
    print("\n[5/5] Kuhi")
    code = "import player; player.install_kuhi()"
    result = run([VENV_PYTHON, "-c", code], cwd=ROOT)
    if result.returncode != 0:
        print("  Kuhi install failed. Run run.sh (or run.bat) and choose option 5.")


if __name__ == "__main__":
    install_system_tools()
    make_venv_and_install_python_packages()
    install_node_packages()
    create_settings()
    install_kuhi()
    print("\nDone. Start the program with ./run.sh (Linux/macOS) or run.bat (Windows).")
