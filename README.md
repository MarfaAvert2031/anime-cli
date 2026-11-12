# anime-cli

Search anime in your terminal, then watch it in mpv or download it. It tries several sources (Kuhi, JustalK, HdRezka) and uses the first one that works.

## Quick start

You need **Python 3.10+** and **git**. Setup installs everything else.

```bash
git clone https://github.com/MarfaAvert2031/anime-cli
cd anime-cli
python setup.py
./run.sh
```

On Windows, use `py setup.py` and then `run.bat`.

Linux asks for your password once, to install ffmpeg, mpv and Node.js.

## How to use

1. Start the program with `./run.sh` (Windows: `run.bat`).
2. Choose **1**, type an anime name, pick an episode, and choose sub or dub.
3. Choose to watch it in mpv or download it.

Choose **4** at any time to check which sources work.

## Update

```bash
git pull
python setup.py
```

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

## Notes

- `settings.xml` is created for you from `settings.example.xml`. Edit it to turn sources on or off, or to add your own API.
- JustalK can be unreliable. Set `<enabled>false</enabled>` for it if it keeps failing.
- HdRezka supports movies only for now.
- Personal learning project. Only use it for content you have the right to watch.
