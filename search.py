import requests  # third-party library that lets us send web requests (GET/POST) to APIs
from config import load_apis, get_nested_value
# Tries ONE api config and returns clean results, or [] if it failed
def try_single_api(api, query):
    try:
        # Check what "dialect" this API speaks — REST APIs and GraphQL APIs are built differently
        if api["type"] == "rest":
            # REST: send a GET request, with our search term and result limit as URL parameters
            # timeout=5 means: give up waiting after 5 seconds instead of hanging forever
            response = requests.get(api["url"], params={"q": query, "limit": 10}, timeout=5)
        else:
            # GraphQL: instead of URL parameters, we send a "query" string describing
            # exactly what fields we want back. $search is a placeholder filled in below.
            gql = '''query ($search: String) {
                Page(perPage: 10) {
                    media(search: $search, type: ANIME) {
                        title { romaji }
                        episodes
                    }
                }
            }'''
            # GraphQL always uses POST, with the query + its variables sent as JSON in the body
            response = requests.post(api["url"], json={"query": gql, "variables": {"search": query}}, timeout=5)

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
            clean_results.append({"title": title, "episodes": episodes})

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

# Loops through every API in settings.xml, using try_single_api() for each one
def search_anime(query):
    # Read the full list of configured APIs from settings.xml
    apis = load_apis()

    # Try each API one at a time, in the order they appear in the file
    for api in apis:
        results = try_single_api(api, query)

        # The moment ONE api succeeds, stop immediately and return its results —
        # no need to waste time calling the remaining APIs in the list
        if results:
            return results

    # If every single API failed, return an empty list so the caller can handle "no results"
    return []