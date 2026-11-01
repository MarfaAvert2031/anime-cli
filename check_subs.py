import requests, streaming

api = next(a for a in streaming.load_streaming_apis() if a["name"] == "Kuhi")
streaming.ensure_server(api)
for provider in (None, "anizone", "animeonsen"):
    params = {"e": 1}
    if provider:
        params["provider"] = provider
    r = requests.get(api["url"] + "/anime/extract/9253", params=params, timeout=90)
    if r.status_code != 200:
        print(provider or "race", "-> error", r.status_code)
        continue
    data = r.json()
    subs = [(s.get("srclang"), s.get("label")) for s in data.get("subtitles", [])]
    print(provider or "race", "->", data.get("provider"), "| subtitles:", subs)