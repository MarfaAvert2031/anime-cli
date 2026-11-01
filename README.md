# anime-cli

A command-line tool to search anime and get watch links. It asks several streaming sources (Kuhi, JustalK, HdRezka) and returns the first one that works.

## Requirements

- Python 3.10+
- Node.js and npm (only for JustalK)
- git

## Install

```bash
git clone https://github.com/MarfaAvert2031/anime-cli
cd anime-cli
```

### Python packages

Use a virtual environment (required on Arch/CachyOS).

**Linux / macOS (fish):**

```fish
python -m venv venv
source venv/bin/activate.fish
pip install requests yt-dlp git+https://github.com/kristal374/hdrezka-api.git
```

**Linux / macOS (bash/zsh):** use `source venv/bin/activate` instead.

**Windows:**

```powershell
py -m venv venv
venv\Scripts\activate
pip install requests yt-dlp git+https://github.com/kristal374/hdrezka-api.git
```

### Node packages (JustalK)

```bash
npm install
```

## Settings

`settings.xml` is not on GitHub, so create it from the example:

```bash
cp settings.example.xml settings.xml
```

Open `settings.xml` and set `<enabled>true</enabled>` for the sources you want.

| Source | Type | Notes |
|---|---|---|
| Kuhi | `rest` | Needs its own server running (see below). |
| JustalK | `node-library` | Needs `npm install`. Can be unreliable. |
| HdRezka | `python-library` | Movies only for now. |

## Run

```bash
python player.py
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

Install it once with menu option 5. Then, in a second terminal, start it and leave it open:

```bash
cd kuhi
uvicorn api:app
```

On Windows use `py -m uvicorn api:app`. You can also add `<start_dir>` to the Kuhi block in `settings.xml` so the CLI starts it for you.

## Adding your own API

Add an `<api>` block to `settings.xml` with a `name`, `type`, and the tags that type needs. No Python changes are needed for normal `rest` APIs. See `settings.example.xml` for examples.

## Troubleshooting

| Problem | Fix |
|---|---|
| `externally-managed-environment` | Use a virtual environment (see Install). |
| `[Kuhi] is not running` | Start it with `uvicorn api:app`. |
| A source never runs | Check it is `<enabled>true</enabled>` in `settings.xml`. |
| `No module named HDrezka` | Activate the venv, then run the pip install again. |
| `py: Unknown command` on Linux | Use `python` instead of `py`. |

## Notes

Personal learning project. Use it only with content you have the right to watch.
