import glob
import os
import re
import shutil
import subprocess
import sys
import platform
import time

from config import (import_apis_from_file, save_streaming_api, set_streaming_api_value,
                    get_preference)
from streaming import (load_streaming_apis, watch, search, get_streams,
                       ensure_server, check_sources, short_error)

KUHI_REPO = "https://github.com/aryaniiil/kuhi-anime-api"
# Kuhi is downloaded into a "kuhi" folder next to this file
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
KUHI_DIR = os.path.join(PROJECT_DIR, "kuhi")
UPDATE_STAMP = os.path.join(PROJECT_DIR, ".last_update")   # remembers when you last updated
UPDATE_EVERY_DAYS = 7
BROWSER_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")

# Stream types mpv can play directly. Others (embed, page) are web pages.
PLAYABLE = {"hls", "mp4", "dash", "video", "m3u8"}


def install_hint(program):
    system = platform.system()
    if system == "Windows":
        ids = {"mpv": "shinchiro.mpv", "ffmpeg": "Gyan.FFmpeg"}
        return f"Install it with: winget install --id {ids[program]} -e"
    if system == "Darwin":
        return f"Install it with: brew install {program}"
    return (f"Install it with: sudo pacman -S {program} (Arch/CachyOS)\n"
            f"or: sudo apt install {program} (Ubuntu/Debian)")


def find_program(name):
    """Look on the PATH first, then in the folders Windows installers use."""
    found = shutil.which(name)
    if found:
        return found
    if platform.system() == "Windows":
        patterns = []
        local = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "WinGet")
        patterns.append(os.path.join(local, "Links", f"{name}.exe"))
        patterns.append(os.path.join(local, "Packages", "*", f"{name}.exe"))
        patterns.append(os.path.join(local, "Packages", "*", "*", f"{name}.exe"))
        patterns.append(os.path.join(local, "Packages", "*", "*", "*", f"{name}.exe"))
        for var in ("ProgramFiles", "ProgramFiles(x86)"):
            base = os.environ.get(var)
            if base:
                patterns.append(os.path.join(base, f"{name}*", f"{name}.exe"))
        for pattern in patterns:
            hits = glob.glob(pattern)
            if hits:
                return hits[0]
    return None


# Names a subtitle can use for a language: the 2-letter code, the 3-letter code, the full name
LANG_NAMES = {"en": {"en", "eng", "english"}, "ru": {"ru", "rus", "russian"},
              "ja": {"ja", "jpn", "japanese"}, "es": {"es", "spa", "spanish"},
              "fr": {"fr", "fra", "fre", "french"}, "de": {"de", "deu", "ger", "german"}}


def preferred_languages():
    """Subtitle languages from settings.xml (<subtitle_language>en,ru</subtitle_language>)."""
    raw = get_preference("subtitle_language", "en,ru")
    return [x.strip().lower() for x in raw.split(",") if x.strip()]


def lang_matches(sub, lang):
    names = LANG_NAMES.get(lang, {lang})
    code = (sub.get("lang") or "").lower().split("-")[0]
    label = (sub.get("label") or "").lower()
    # Full names are matched inside the label ("English (Full)"); short codes only exactly
    return code in names or any(n in label for n in names if len(n) > 3)


def pick_subtitles(subtitles, langs):
    """One subtitle per preferred language, in your order of preference."""
    chosen = []
    for lang in langs:
        for sub in sorted(subtitles, key=lambda s: not s.get("default")):
            if lang_matches(sub, lang) and sub not in chosen:
                chosen.append(sub)
                break
    return chosen


def play(stream):
    mpv = find_program("mpv")
    if not mpv:
        print("mpv is not installed.")
        print(install_hint("mpv"))
        return
    langs = preferred_languages()
    cmd = [mpv, stream["url"]]
    if stream.get("referer"):
        cmd.append(f"--referrer={stream['referer']}")
    for sub in pick_subtitles(stream.get("subtitles") or [], langs):
        cmd.append(f"--sub-file={sub['url']}")
    # Also prefer these languages when the video has subtitle tracks built in
    codes = []
    for lang in langs:
        codes += sorted(c for c in LANG_NAMES.get(lang, {lang}) if len(c) <= 3)
    cmd.append("--slang=" + ",".join(codes))
    subprocess.run(cmd)


def download(stream, title, episode):
    safe = re.sub(r'[\\/:*?"<>|%]', "", title)
    os.makedirs("downloads", exist_ok=True)
    if stream["type"] in ("hls", "m3u8"):
        # ffmpeg reads the playlist once and copies the video without re-encoding
        ffmpeg = find_program("ffmpeg")
        if not ffmpeg:
            print("ffmpeg is not installed.")
            print(install_hint("ffmpeg"))
            return
        out = f"downloads/{safe} - E{episode}.mkv"
        cmd = [ffmpeg, "-y", "-user_agent", BROWSER_UA]
        if stream.get("referer"):
            cmd += ["-headers", f"Referer: {stream['referer']}\r\n"]
        cmd += ["-i", stream["url"], "-c", "copy", out]
    else:
        out = f"downloads/{safe} - E{episode}"
        cmd = [sys.executable, "-m", "yt_dlp", "-o", out + ".%(ext)s", stream["url"]]
        if stream.get("referer"):
            cmd += ["--referer", stream["referer"]]
    if subprocess.run(cmd).returncode == 0:
        print(f"Saved: {out}")
    else:
        print("The download failed. Stream links expire after a few minutes, "
              "so search again and download right away.")


# Asks a question. Pressing Enter gives back the [default].
def ask(prompt, default=""):
    shown = f" [{default}]" if default else ""
    return input(f"{prompt}{shown}: ").strip() or default


def watch_flow():
    apis = load_streaming_apis()
    if not apis:
        print("No streaming sources are enabled in settings.xml.")
        return
    query = input("Anime: ").strip()
    if not query:
        return
    ep = input("Episode (Enter for 1): ").strip() or "1"
    if not ep.isdigit():
        print("Episode must be a number.")
        return
    episode = int(ep)

    default_audio = get_preference("default_audio", "sub")[:1].lower()
    answer = ask("Audio: (s)ub or (d)ub", default_audio if default_audio in "sd" else "s").lower()
    audio = "dub" if answer.startswith("d") else "sub"

    found = watch(apis, query, episode, audio)
    if not found and audio == "dub":
        print("No dubbed version found. Trying with subtitles ...")
        audio = "sub"
        found = watch(apis, query, episode, audio)
    if not found:
        print("No streams found. Use option 4 in the menu to check your sources.")
        return

    print(f"\n{found['title']} (from {found['source']})")
    for key, value in (found["details"] or {}).items():
        print(f"  {key}: {value}")

    streams = found["streams"]
    print()
    for i, s in enumerate(streams, start=1):
        note = "" if s["type"] in PLAYABLE else "   (web page, may not play)"
        print(f"{i}. [{s['type']}] {s['url']}{note}")

    # Default choice: the first stream mpv can play directly
    default = next((i for i, s in enumerate(streams, start=1) if s["type"] in PLAYABLE), 1)
    n = input(f"Pick a stream number (Enter for {default}): ").strip() or str(default)
    if not (n.isdigit() and 1 <= int(n) <= len(streams)):
        print("Invalid choice.")
        return
    stream = streams[int(n) - 1]

    action = input("(w)atch or (d)ownload? ").strip().lower()
    if action == "d":
        download(stream, found["title"], episode)
    else:
        langs = preferred_languages()
        subs = pick_subtitles(stream.get("subtitles") or [], langs)
        if subs:
            print("Subtitles: " + ", ".join(s["label"] or s["lang"] for s in subs))
        elif audio == "sub":
            print(f"No {' or '.join(langs)} subtitle files from this source. "
                  "The video may have them built in: press j in mpv to switch.")
        play(stream)


# Lets the user type in their own streaming API, tests it, then saves it to settings.xml
def add_streaming_api():
    print("Add your own streaming API. Press Enter to accept the [default].")
    api = {
        "name": ask("Name"),
        "url": ask("Base URL (e.g. http://127.0.0.1:8000)"),
        "type": "rest",
        "search_path": ask("Search path (e.g. /search)"),
        "query_param": ask("Search parameter name", "query"),
        "results_path": ask("Where the results list is (dot path)", "results"),
        "id_field": ask("ID field", "id"),
        "title_field": ask("Title field", "title"),
        "extract_path": ask("Stream path, {id} stands for the id (e.g. /watch/{id})"),
        "episode_param": ask("Episode parameter name", "e"),
        "audio_param": ask("Audio parameter name", "type"),
        "default_audio": "sub",
        "streams_field": ask("Where the streams list is", "streams"),
        "stream_url_field": ask("Stream URL field", "url"),
        "stream_type_field": ask("Stream type field", "type"),
        "referer_field": ask("Referer field", "referer"),
        "info_path": ask("Details path (optional, Enter to skip)"),
        "api_key_env": ask("Name of the environment variable that holds your API key (optional)"),
    }
    if api["api_key_env"]:
        api["api_key_header"] = ask("Header name for the key", "X-API-Key")
    api["enabled"] = "true"

    missing = [k for k in ("name", "url", "search_path", "extract_path") if not api[k]]
    if missing:
        print(f"Missing: {', '.join(missing)}. Nothing was saved.")
        return

    test = ask("Test search", "naruto")
    ok = False
    try:
        if not ensure_server(api):
            raise ConnectionError("could not connect (is the server running?)")
        results = search(api, test)
        if not results:
            raise ValueError(f"search for '{test}' returned no results")
        print(f"Search works: {results[0]}")
        streams = get_streams(api, results[0]["id"], 1)
        if not streams:
            raise ValueError("no streams came back for episode 1")
        print(f"Streams work: {streams[0]['url']}")
        ok = True
    except Exception as e:
        print(f"Test failed: {short_error(e)}")

    if not ok and ask("Save it anyway? (y/n)", "n").lower() != "y":
        print("Not saved.")
        return
    if save_streaming_api(api):
        print(f"Saved '{api['name']}' to settings.xml")


# Copies the <api> blocks from someone else's XML file into settings.xml
def import_flow():
    file_path = input("Path to the XML file: ").strip().strip('"')
    if not file_path:
        return
    count = import_apis_from_file(file_path)
    print(f"Imported {count} API(s). Only import files from people you trust.")
    print("Use option 4 to check that they work.")


# One-time setup: downloads Kuhi, installs its libraries, tells settings.xml where it is
def install_kuhi():
    if not shutil.which("git"):
        print("git is not installed. Install it first (winget install --id Git.Git -e), "
              "reopen the terminal and try again.")
        return
    if not os.path.isfile(os.path.join(KUHI_DIR, "api.py")):
        print("Downloading Kuhi ...")
        if subprocess.run(["git", "clone", "--depth", "1", KUHI_REPO, KUHI_DIR]).returncode != 0:
            print("The download failed. Check your internet connection and try again.")
            return
    print("Installing Kuhi's libraries ...")
    requirements = os.path.join(KUHI_DIR, "requirements.txt")
    if subprocess.run([sys.executable, "-m", "pip", "install", "-r", requirements]).returncode != 0:
        print("Installing the libraries failed. Read the message above.")
        return
    if set_streaming_api_value("Kuhi", "start_dir", KUHI_DIR):
        print("Done. Kuhi will now start by itself when you search.")
    else:
        print("Kuhi is installed, but there is no 'Kuhi' entry in <streaming_apis> in settings.xml.")
        print(f"Add this line inside it: <start_dir>{KUHI_DIR}</start_dir>")


# Updates the tools that change often. You choose when; nothing updates silently.
def update_flow():
    requirements = os.path.join(PROJECT_DIR, "requirements.txt")
    print("Updating Python libraries (requests, yt-dlp, HDrezka) ...")
    subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "-r", requirements])

    npm = shutil.which("npm")
    if npm and os.path.isdir(os.path.join(PROJECT_DIR, "node_modules")):
        print("Updating JustalK ...")
        subprocess.run([npm, "update", "@justalk/anime-api"], cwd=PROJECT_DIR)

    if os.path.isdir(os.path.join(KUHI_DIR, ".git")) and shutil.which("git"):
        print("Updating Kuhi ...")
        subprocess.run(["git", "pull", "--ff-only"], cwd=KUHI_DIR)
        subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "-r",
                        os.path.join(KUHI_DIR, "requirements.txt")])

    with open(UPDATE_STAMP, "w") as f:
        f.write(str(time.time()))
    print("\nDone. To update mpv and ffmpeg too, run: winget upgrade --all  (Windows)")


# Prints a reminder if it has been a while since the last update
def update_reminder():
    if not os.path.exists(UPDATE_STAMP):
        with open(UPDATE_STAMP, "w") as f:   # first run: start counting from now
            f.write(str(time.time()))
        return
    try:
        age = (time.time() - float(open(UPDATE_STAMP).read())) / 86400
    except ValueError:
        return
    if age >= UPDATE_EVERY_DAYS:
        print(f"Tip: tools were last updated {int(age)} days ago. "
              "Choose 6 to update yt-dlp and the rest.")


def status_flow():
    apis = load_streaming_apis()
    if not apis:
        print("No streaming sources are enabled in settings.xml.")
        return
    for name, ok, note in check_sources(apis):
        print(f"[{'OK' if ok else 'X '}] {name} - {note}")
    if any(name == "Kuhi" and not ok for name, ok, _ in check_sources(apis)) \
            and not os.path.isfile(os.path.join(KUHI_DIR, "api.py")):
        print("Kuhi is not installed yet. Choose option 5 and it is set up for you.")
    for tool in ("mpv", "ffmpeg"):
        found = "OK" if find_program(tool) else "X "
        print(f"[{found}] {tool}")


def main():
    update_reminder()
    while True:
        print("\n1. Watch or download")
        print("2. Add my own streaming API")
        print("3. Import APIs from an XML file")
        print("4. Check my sources")
        print("5. Install Kuhi (one time)")
        print("6. Update tools")
        print("q. Quit")
        choice = input("Choose: ").strip().lower()
        if choice == "1":
            watch_flow()
        elif choice == "2":
            add_streaming_api()
        elif choice == "3":
            import_flow()
        elif choice == "4":
            status_flow()
        elif choice == "5":
            install_kuhi()
        elif choice == "6":
            update_flow()
        elif choice == "q":
            break
        else:
            print("Invalid choice.")


if __name__ == "__main__":
    main()