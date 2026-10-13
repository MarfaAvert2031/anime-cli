import re
import shutil
import subprocess
import sys

from streaming import load_streaming_apis, watch


def play(stream):
    if not shutil.which("mpv"):
        print("mpv is not installed.")
        print("Windows: winget install --id shinchiro.mpv")
        print("Debian/Ubuntu: sudo apt install mpv   Arch: sudo pacman -S mpv")
        return
    cmd = ["mpv", stream["url"]]
    if stream.get("referer"):
        cmd.append(f"--referrer={stream['referer']}")
    subprocess.run(cmd)


def download(stream, title, episode):
    if not shutil.which("ffmpeg"):
        print("ffmpeg is not installed. Windows: winget install --id Gyan.FFmpeg")
        return
    safe = re.sub(r'[\\/:*?"<>|%]', "", title)
    cmd = [sys.executable, "-m", "yt_dlp",
           "-o", f"downloads/{safe} - E{episode}.%(ext)s", stream["url"]]
    if stream.get("referer"):
        cmd += ["--referer", stream["referer"]]
    subprocess.run(cmd)


def main():
    query = input("Anime: ").strip()
    episode = int(input("Episode (Enter for 1): ").strip() or 1)
    found = watch(load_streaming_apis(), query, episode)
    if not found or not found["streams"]:
        print("No streams found")
        return
    print(f"\n{found['title']} (from {found['source']})")
    for i, s in enumerate(found["streams"], start=1):
        print(f"{i}. {s['type']} {s['url']}")

    n = input("Pick a stream number: ").strip()
    if not (n.isdigit() and 1 <= int(n) <= len(found["streams"])):
        print("Invalid choice.")
        return
    stream = found["streams"][int(n) - 1]

    action = input("(w)atch or (d)ownload? ").strip().lower()
    if action == "d":
        download(stream, found["title"], episode)
    else:
        play(stream)


if __name__ == "__main__":
    main()