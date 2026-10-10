import requests  # third-party library that lets us send web requests (GET/POST) to APIs
from config import load_apis, get_nested_value, save_api_to_settings
# Reads an optional field; returns "?" if the API has no path for it or the value is missing
def get_optional(item, path):
    if not path:
        return "?"
    return get_nested_value(item, path) or "?"
# Tries ONE api config and returns clean results, or [] if it failed
def try_single_api(api, query, media="anime"):
    try:
        # Check what "dialect" this API speaks — REST APIs and GraphQL APIs are built differently
        if api["type"] == "rest":
            # REST: send a GET request, with our search term and result limit as URL parameters
            # timeout=5 means: give up waiting after 5 seconds instead of hanging forever
            param_name = api.get("query_param") or "q"
            response = requests.get(api["url"], params={param_name: query, "limit": 10}, timeout=5)
        else:
            # GraphQL: instead of URL parameters, we send a "query" string describing
            # exactly what fields we want back. $search is a placeholder filled in below.
             gql = '''query ($search: String, $type: MediaType) {
                Page(perPage: 10) {
                    media(search: $search, type: $type) {
                        title { romaji }
                        episodes
                        chapters
                        status
                        averageScore
                        seasonYear
                        startDate { year }
                    }
                }
            }'''
            # GraphQL always uses POST, with the query + its variables sent as JSON in the body
             requests = requests.post(api["url"], json={"query": gql, "variables": {"search": query, "type": media.upper()}}, timeout=5)

        # If the server responded with an error status (404, 500, 504, etc.),
        # this line throws an exception on purpose — sending us straight to 'except' below
        response.raise_for_status()

        # Convert the raw response text into a Python dictionary we can work with
        data = response.json()

        # Every API buries its actual results at a different depth inside the JSON.
        # 'results_path' (from settings.xml) tells get_nested_value() exactly where to dig.
        # "or []" means: if nothing is found, use an empty list instead of None (safer to loop over)
        results = get_nested_value(data, api["results_path"]) or []

        # This will hold our results in ONE consistent shape, no matter which API we used
        clean_results = []
           
        # Go through each raw result and pull out just the title and episode count,
        # using the field names this specific API told us to look for (also from settings.xml)
        for item in results:
            title = get_nested_value(item, api["title_field"]) or "Unknown"
            episodes = get_nested_value(item, api["episodes_field"]) or "?"
            clean_results.append({
                "title": title,
                "episodes": episodes,
                "status": get_optional(item, api.get("status_field")),
                "score": get_optional(item, api.get("score_field")),
                "year": get_optional(item, api.get("year_field")),
            })

        # Let the user know which API actually answered successfully
        print(f"Using {api['name']}")

        # Hand back the cleaned-up list to whoever called this function
        return clean_results

    # Catches ANY kind of failure: bad network, timeout, wrong path, broken JSON, etc.
    except Exception as e:
        # Print what went wrong and why, so it's not a silent failure
        print(f"{api['name']} failed: {e}")
        # Return an empty list instead of crashing — lets the caller just try the next API
        return []
# Manga APIs, hardcoded in the same shape as the entries in settings.xml
MANGA_APIS = [
    {"name": "AniList Manga", "url": "https://graphql.anilist.co", "type": "graphql",
     "results_path": "data.Page.media", "title_field": "title.romaji",
     "episodes_field": "chapters", "status_field": "status",
     "score_field": "averageScore", "year_field": "startDate.year"},
    {"name": "Jikan Manga", "url": "https://api.jikan.moe/v4/manga", "type": "rest",
     "results_path": "data", "title_field": "title",
     "episodes_field": "chapters", "status_field": "status",
     "score_field": "score", "year_field": "published.prop.from.year",
     "query_param": "q"},
]
# Loops through every API in settings.xml, using try_single_api() for each one
def search_anime(query, media="anime"):
    # Read the full list of configured APIs from settings.xml
    apis = MANGA_APIS if media=="manga" else load_apis()

    # Try each API one at a time, in the order they appear in the file
    for api in apis:
        results = try_single_api(api, query, media)

        # The moment ONE api succeeds, stop immediately and return its results —
        # no need to waste time calling the remaining APIs in the list
        if results:
            return results

    # If every single API failed, return an empty list so the caller can handle "no results"
    return []
# Shows the results as a numbered list and lets the user pick one
def pick_result(results):
    for i, item in enumerate(results, start=1):
        print(f"{i}. {item['title']}")

    while True:
        choice = input("Pick a number (or q to quit): ").strip()
        if choice.lower() == "q":
            return None
        # isdigit() checks it's a number, then we check it's in range
        if choice.isdigit() and 1 <= int(choice) <= len(results):
            return results[int(choice) - 1]
        print("Invalid choice, try again.")

# Prints the details of the chosen anime
def show_details(item, media="anime"):
    label = "Chapters" if media == "manga" else "Episodes"
    print()
    print(f"Title:    {item['title']}")
    print(f"{label}: {item['episodes']}")
    print(f"Status:   {item['status']}")
    print(f"Score:    {item['score']}")
    print(f"Year:     {item['year']}")

def add_custom_api():
    api= {
        "name": input("Name:").strip(),
        "url":  input("URL: ").strip(),
        "type": input("Type (rest/grapqL): ").strip() .lower(),
        "results_path":  input("Results path (e.g data): ").strip(),
        "title_field": input("Title field (e.g title): ").strip(),
        "episodes_field": input("Episodes field: ").strip(),
  }
    if api["type"] == "rest":
        api["query_param"] = input("Search parameter name (Enter for q): ").strip() or "q"
    if try_single_api(api, "naruto"):
        save_api_to_settings(api)
        print("It works and it is saved")
    else:
        print("That API didn't work, so it wasn't saved")
# Runs only when you start this file directly (python search.py)
if __name__ == "__main__":
    print("1. Anime")
    print("2. Manga")
    print("3. Add my own API")
    choice = input("Choose 1, 2 or 3: ").strip()

    if choice == "3":
        add_custom_api()
        choice = "1"          # single = (assign), not ==
    media = "manga" if choice == "2" else "anime"

    query = input(f"Search {media}: ").strip()
    results = search_anime(query, media)

    if not results:
        print("No results found.")
    else:
        chosen = pick_result(results)
        if chosen:
            show_details(chosen, media)   # pass media so manga says "Chapters"