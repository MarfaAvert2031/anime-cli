"""Generic loader for the <streaming_apis> section of settings.xml.

No API names are hardcoded: every <api> block is read from the XML, and the
`type` tag decides how it is called (rest, node-library, python-library).
"""
import json
import os
import subprocess
import xml.etree.ElementTree as ET

import requests

REQUIRED = {
    "rest": ["name", "url", "search_path", "extract_path"],
    "node-library": ["name", "package"],
    "python-library": ["name", "package"],
}

NODE_SCRIPT = (
    "const a=require(process.argv[1]);"
    "(async()=>{const o={};if(process.argv[4])o.website=process.argv[4];"
    "console.log(JSON.stringify(await a.stream(process.argv[2],"
    "Number(process.argv[3]),o)))})()"
)


def get_path(data, path):
    """Read 'results.0.title' style paths from nested dicts/lists."""
    for key in path.split("."):
        if isinstance(data, list):
            data = data[int(key)]
        else:
            data = data[key]
    return data


def pick_title(title):
    """Titles can be a string or a dict like {'english': ..., 'romaji': ...}."""
    if isinstance(title, dict):
        for k in ("english", "romaji", "native"):
            if title.get(k):
                return title[k]
        return next(iter(title.values()), "")
    return str(title)


def build_headers(api):
    """Optional API key, read from an environment variable (never stored in the XML)."""
    headers = {}
    key_env, key_header = api.get("api_key_env"), api.get("api_key_header")
    if key_env and key_header:
        key = os.environ.get(key_env)
        if not key:
            raise RuntimeError(f"Set the {key_env} environment variable first")
        headers[key_header] = key
    return headers


def fill_id(template, anime_id):
    """Put the id into a path. Both {id} and {anilist_id} work."""
    return template.replace("{anilist_id}", str(anime_id)).replace("{id}", str(anime_id))


def load_streaming_apis(path="settings.xml"):
    """Return enabled, valid <api> blocks from <streaming_apis> as dicts."""
    root = ET.parse(path).getroot()
    section = root if root.tag == "streaming_apis" else root.find("streaming_apis")
    apis = []
    if section is None:
        print("No <streaming_apis> section found in", path)
        return apis
    for node in section.findall("api"):
        api = {c.tag: (c.text or "").strip() for c in node}
        name = api.get("name", "?")
        if api.get("enabled", "false").lower() != "true":
            continue
        missing = [t for t in REQUIRED.get(api.get("type"), ["type"]) if not api.get(t)]
        if missing:
            print(f"Skipping '{name}': missing {', '.join(missing)}")
            continue
        apis.append(api)
    return apis


# ---------- rest (Kuhi and similar) ----------

def rest_search(api, query):
    r = requests.get(
        api["url"] + api["search_path"],
        params={api.get("query_param", "query"): query},
        headers=build_headers(api),
        timeout=20,
    )
    r.raise_for_status()
    items = get_path(r.json(), api.get("results_path", "results"))
    id_f, title_f = api.get("id_field", "id"), api.get("title_field", "title")
    return [{"id": i.get(id_f), "title": pick_title(i.get(title_f, ""))} for i in items]


def rest_streams(api, anime_id, episode, audio=None):
    path = fill_id(api["extract_path"], anime_id)
    r = requests.get(
        api["url"] + path,
        headers=build_headers(api),
        params={
            api.get("episode_param", "e"): episode,
            api.get("audio_param", "type"): audio or api.get("default_audio", "sub"),
        },
        timeout=60,
    )
    r.raise_for_status()
    streams = get_path(r.json(), api.get("streams_field", "streams"))
    return [
        {
            "url": s.get(api.get("stream_url_field", "url")),
            "type": s.get(api.get("stream_type_field", "type")),
            "referer": s.get(api.get("referer_field", "referer")),
        }
        for s in streams
    ]


# ---------- node library (JustalK) ----------

def node_streams(api, title, episode):
    cmd = ["node", "-e", NODE_SCRIPT, api["package"], title, str(episode),
           api.get("website", "")]
    out = subprocess.run(cmd, capture_output=True, text=True, timeout=90)
    if out.returncode != 0:
        raise RuntimeError(out.stderr.strip()[-300:] or "node failed")
    return [{"url": s["link"], "type": "page", "referer": None,
             "source": s.get("source")} for s in json.loads(out.stdout)]


# ---------- python library (HDrezka) ----------

def python_search(api, query):
    from HDrezka import HDrezka  # imported here so it is optional
    results = HDrezka().search(query).get()
    return [{"id": i, "title": str(p)} for i, p in enumerate(results)]


def python_movie_stream(api, query, index=0):
    from HDrezka import HDrezka
    movie = HDrezka().search(query).get()[index].get()
    url = movie.player.get_video_url(api.get("default_quality", "720p"))
    return [{"url": url, "type": "video", "referer": None}]


# ---------- one entry point per action ----------

def search(api, query):
    kind = api["type"]
    if kind == "rest":
        return rest_search(api, query)
    if kind == "python-library":
        return python_search(api, query)
    raise ValueError(f"'{api['name']}' ({kind}) has no separate search")


def get_streams(api, query_or_id, episode=1, audio=None):
    kind = api["type"]
    if kind == "rest":
        return rest_streams(api, query_or_id, episode, audio)
    if kind == "node-library":
        return node_streams(api, str(query_or_id), episode)
    if kind == "python-library":
        return python_movie_stream(api, str(query_or_id))  # movies only for now
    raise ValueError(f"Unknown type '{kind}'")


def get_details(api, anime_id):
    """Details about one title (rest APIs with an <info_path> tag)."""
    if api["type"] != "rest" or not api.get("info_path"):
        raise ValueError(f"'{api['name']}' has no <info_path>")
    r = requests.get(
        api["url"] + fill_id(api["info_path"], anime_id),
        headers=build_headers(api),
        timeout=20,
    )
    r.raise_for_status()
    data = r.json()
    fields = [f.strip() for f in api.get("info_fields", "").split(",") if f.strip()]
    if not fields:
        return data  # no <info_fields> set: give back everything
    out = {}
    for f in fields:
        try:
            value = get_path(data, f)
            out[f] = pick_title(value) if isinstance(value, dict) else value
        except (KeyError, IndexError, ValueError, TypeError):
            out[f] = None
    return out


def watch(apis, query, episode=1, audio=None):
    """Search, get details, get streams. Returns the first source that works."""
    for api in apis:
        try:
            if api["type"] == "node-library":
                streams = get_streams(api, query, episode)
                return {"source": api["name"], "title": query,
                        "details": None, "streams": streams}
            if api["type"] != "rest":
                continue
            results = search(api, query)
            if not results:
                continue
            top = results[0]
            details = get_details(api, top["id"]) if api.get("info_path") else None
            streams = get_streams(api, top["id"], episode, audio)
            return {"source": api["name"], "title": top["title"],
                    "details": details, "streams": streams}
        except Exception as e:
            print(f"[{api['name']}] failed: {e}")
    return None


def try_each(apis, func, *args):
    """Run func(api, *args) on every API; a failing one is reported, not fatal."""
    for api in apis:
        try:
            yield api["name"], func(api, *args)
        except Exception as e:
            print(f"[{api['name']}] failed: {e}")


if __name__ == "__main__":
    import sys

    query = sys.argv[1] if len(sys.argv) > 1 else "naruto"
    apis = load_streaming_apis()
    print("Enabled:", [a["name"] for a in apis])
    for name, results in try_each(
        [a for a in apis if a["type"] in ("rest", "python-library")], search, query
    ):
        print(f"\n[{name}] {len(results)} results")
        for r in results[:5]:
            print("  ", r)

    if len(sys.argv) > 2:  # py streaming.py naruto 1  -> also get details and streams
        found = watch(apis, query, int(sys.argv[2]))
        if found is None:
            print("\nNo source returned a stream.")
        else:
            print(f"\nWatch: {found['title']} (from {found['source']})")
            print("Details:", found["details"])
            for s in found["streams"]:
                print("  ", s)
