import xml.etree.ElementTree as ET

def load_apis(path="settings.xml"):
    tree = ET.parse(path)
    root = tree.getroot()

    apis = []
    
    for api in root.find("apis"):
        apis.append({
            "name": api.find("name").text,
            "url": api.find("url").text,
            "type": api.find("type").text,
            # New: paths that tell us where to find data in THIS api's specific JSON shape
            "results_path": api.find("results_path").text,
            "title_field": api.find("title_field").text,
            "episodes_field": api.find("episodes_field").text,
        })
    return apis
# Adds a new <api> entry to settings.xml permanently, so the user doesn't have to retype it
def save_api_to_settings(api, path="settings.xml"):
    tree = ET.parse(path)      # load the existing file
    root = tree.getroot()      # get <settings>
    apis_element = root.find("apis")  # get <apis>, where all API entries live

    # Build a new <api> element and its child tags, one by one
    new_api = ET.SubElement(apis_element, "api")
    ET.SubElement(new_api, "name").text = api["name"]
    ET.SubElement(new_api, "url").text = api["url"]
    ET.SubElement(new_api, "type").text = api["type"]
    ET.SubElement(new_api, "results_path").text = api["results_path"]
    ET.SubElement(new_api, "title_field").text = api["title_field"]
    ET.SubElement(new_api, "episodes_field").text = api["episodes_field"]

    # Write the whole tree back to the file, saving the change permanently
    tree.write(path)
# Digs into a nested dictionary using a dot-separated path string
# e.g. get_nested_value(data, "data.Page.media") walks data -> "data" -> "Page" -> "media"
def get_nested_value(data, path):
    keys = path.split(".")  # turn "data.Page.media" into ["data", "Page", "media"]
    for key in keys:
        if isinstance(data, dict):
            data = data.get(key)  # step one level deeper each time
        else:
            return None  # if we hit something that's not a dict, the path is wrong — bail out safely
    return data