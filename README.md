# anime-cli

<<<<<<< HEAD
Search anime in your terminal, then watch it in mpv or download it. It tries several sources (Kuhi, JustalK, HdRezka) and uses the first one that works.

## Quick start

You need **Python 3.10+** and **git**. Setup installs everything else.
=======
A command-line tool to search anime and get watch links. It asks several streaming sources (Kuhi, JustalK, HdRezka) and returns the first one that works. It can play the stream in mpv or download it.

## Quick start
>>>>>>> 7ccb00bfdaaf4f02079267aa9404b4788e0a2263

```bash
git clone https://github.com/MarfaAvert2031/anime-cli
cd anime-cli
<<<<<<< HEAD
python setup.py
./run.sh
```

On Windows, use `py setup.py` and then `run.bat`.
=======
python setup.py        # Windows: py setup.py
```

`setup.py` installs the system tools (ffmpeg, mpv, Node.js, git), creates a virtual environment, installs the Python and Node packages, creates `settings.xml`, and installs Kuhi.

Then start the program:

```bash
./run.sh               # Windows: run.bat
```

If you prefer to install things yourself, see [Manual install](#manual-install).

## Requirements

**Required**

- Python 3.10 or newer
- git
- mpv (to play streams)

**Optional**

- ffmpeg (only for downloading episodes)
- Node.js and npm (only for the JustalK source)

## Manual install
>>>>>>> 7ccb00bfdaaf4f02079267aa9404b4788e0a2263

Linux asks for your password once, to install ffmpeg, mpv and Node.js.

## How to use

<<<<<<< HEAD
1. Start the program with `./run.sh` (Windows: `run.bat`).
2. Choose **1**, type an anime name, pick an episode, and choose sub or dub.
3. Choose to watch it in mpv or download it.
=======
```fish
python -m venv venv
source venv/bin/activate.fish
pip install -r requirements.txt
```
>>>>>>> 7ccb00bfdaaf4f02079267aa9404b4788e0a2263

Choose **4** at any time to check which sources work.

<<<<<<< HEAD
## Update
=======
**Windows:**

```powershell
py -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

**Node packages (only for JustalK):**
>>>>>>> 7ccb00bfdaaf4f02079267aa9404b4788e0a2263

```bash
git pull
python setup.py
```

<<<<<<< HEAD
## Problems

| Problem | Fix |
|---|---|
| `externally-managed-environment` or `No module named HDrezka` | Start with `./run.sh`, not `python player.py` or `pip`. |
| `run.sh: permission denied` | Run `chmod +x run.sh` once. |
| `[Kuhi] is not running` | Run `python setup.py` again. If it still fails, see below. |
| Stream link expired | Search again and download right away. |

### Kuhi still not running

1. Run `pwd` inside the `anime-cli` folder to get its full path.
2. Open `settings.xml` and find the `Kuhi` block.
3. Set the folder, ending with `/kuhi`:
   ```xml
   <start_dir>/home/yourname/anime-cli/kuhi</start_dir>
   ```
   Windows: `<start_dir>C:\Users\yourname\anime-cli\kuhi</start_dir>`
4. Save and run the program again.
=======
The install downloads Chromium, which can fail on restricted networks. If it does, run `PUPPETEER_SKIP_DOWNLOAD=1 npm install` (Windows: `set PUPPETEER_SKIP_DOWNLOAD=1` first).

## Settings

`settings.xml` is not on GitHub. `setup.py` creates it, or you can copy the example yourself:

```bash
cp settings.example.xml settings.xml
```

Set `<enabled>true</enabled>` for the sources you want.

| Source | Type | Notes |
|---|---|---|
| Kuhi | `rest` | Needs its own server (see below). Supports sub and dub. |
| JustalK | `node-library` | **Off by default.** Needs `npm install`. Can be unreliable. |
| HdRezka | `python-library` | Movies only for now. |

### Providers, sub and dub

Kuhi can get a video from several providers. List them in the Kuhi block, in the order you want them tried:

```xml
<providers>anizone,anineko,anikoto</providers>
```

When you ask for dub, the program tries dub on **every** provider first. Only if none has it does it fall back to sub, and it tells you so.

### Subtitles

Choose subtitle languages (in order of preference) with:

```xml
 <preferences>
    <fullscreen>true</fullscreen>
    <subtitle_language>ru,en</subtitle_language>
    <default_audio>sub</default_audio>
    </preferences>
```
- `subtitle_language`: subtitle languages in order of preference.
- `fullscreen`: `true` starts mpv in fullscreen (the default), `false` starts it in a window. Inside mpv, press `f` to toggle fullscreen and `Esc` to leave it.
## Run

```bash
./run.sh               # Windows: run.bat
```

Menu:

1. Watch or download
2. Add my own streaming API
3. Import APIs from an XML file
4. Check my sources
5. Install Kuhi (one time)
6. Update tools

Use option 4 to see which sources are working.

### Kuhi

Install it once with menu option 5 (or `setup.py` does it for you). Then either add `<start_dir>` to the Kuhi block in `settings.xml` so the CLI starts it automatically, or start it yourself in a second terminal and leave it open:

```bash
cd kuhi
uvicorn api:app
```

On Windows use `py -m uvicorn api:app`.

## Adding your own API

Add an `<api>` block to `settings.xml` with a `name`, `type`, and the tags that type needs. No Python changes are needed for normal `rest` APIs. See `settings.example.xml` for examples.

## Troubleshooting

| Problem | Fix |
|---|---|
| `externally-managed-environment` | Use a virtual environment (see Manual install). |
| `[Kuhi] is not running` | Add `<start_dir>` to the Kuhi block, or start it with `uvicorn api:app`. |
| `Package not installed. Run ... npm install` | Run `npm install` in the project folder (JustalK only). |
| `npm install` fails with a Chromium error | Run it with `PUPPETEER_SKIP_DOWNLOAD=1`. |
| `no streams found` | That source has nothing for this title or episode. Try another source. |
| Dub is not found | Not every provider has dubs. The program falls back to sub and says so. |
| A source never runs | Check it is `<enabled>true</enabled>` in `settings.xml`. |
| `No module named HDrezka` | Activate the venv, then run `pip install -r requirements.txt` again. |
| `mpv is not installed` | Install it (`winget install --id shinchiro.mpv`, `sudo pacman -S mpv`, or `sudo apt install mpv`). |
| `py: Unknown command` on Linux | Use `python` instead of `py`. |
>>>>>>> 7ccb00bfdaaf4f02079267aa9404b4788e0a2263

## Disclaimer

<<<<<<< HEAD
- `settings.xml` is created for you from `settings.example.xml`. Edit it to turn sources on or off, or to add your own API.
- JustalK can be unreliable. Set `<enabled>false</enabled>` for it if it keeps failing.
- HdRezka supports movies only for now.
- Personal learning project. Only use it for content you have the right to watch.
=======
This is a personal learning project. It does not host, store or distribute any video. It only links to third-party sources, and it is your responsibility to follow the laws of your country. Use it only with content you have the right to watch.
>>>>>>> 7ccb00bfdaaf4f02079267aa9404b4788e0a2263
