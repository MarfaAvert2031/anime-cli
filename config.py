import xml.etree.ElementTree as ET
import os
import shutil
# Returns a tag's text, or None if the tag doesn't exist (so old entries don't crash)
def get_text(element, tag):
    found = element.find(tag)
    return found.text if found is not None else None
def ensure_settings(path="settings.xml"):
    """Create settings.xml from settings.example.xml the first time."""
    if os.path.exists(path):
        return True
    example = os.path.join(os.path.dirname(path) or ".", "settings.example.xml")
    if os.path.exists(example):
        shutil.copy(example, path)
        print(f"Created {path} from settings.example.xml")
        return True
    print(f"{path} and settings.example.xml are both missing")
    return False

def load_apis(path="settings.xml"):
    if not ensure_settings(path):
        print(f"{path} not found. Run: cp settings.example.xml {path}")
        return []
    tree = ET.parse(path)
    root = tree.getroot()

    apis_element = root.find("apis")
    if apis_element is None:
        print("No <apis> section found in", path)
        return []

    apis = []
    for api in apis_element:
        apis.append({
            "name": api.find("name").text,
            "url": api.find("url").text,
            "type": api.find("type").text,
            "results_path": api.find("results_path").text,
            "title_field": api.find("title_field").text,
            "episodes_field": api.find("episodes_field").text,
            "status_field": get_text(api, "status_field"),
            "score_field": get_text(api, "score_field"),
            "year_field": get_text(api, "year_field"),
            "query_param": get_text(api, "query_param"),
        })
    return apis
# Adds a new <api> entry to settings.xml permanently, so the user doesn't have to retype it
REQUIRED_TAGS = {"name", "url", "type", "results_path", "title_field", "episodes_field"}
OPTIONAL_TAGS = {"status_field", "score_field", "year_field", "query_param"}
def save_api_to_settings(api, path="settings.xml"):
    if not ensure_settings(path):
        return False
    tree = ET.parse(path)      # load the existing file
    root = tree.getroot()      # get <settings>
    apis_element = root.find("apis")  # get <apis>, where all API entries live
    if apis_element is None:
        apis_element = ET.SubElement(root, "apis")

    new_api = ET.SubElement(apis_element, "api")    
# Build a new <api> element and its child tags, one by one
    for tag in REQUIRED_TAGS:
        ET.SubElement(new_api, tag).text = api[tag]
    for tag in OPTIONAL_TAGS:
        if api.get(tag):
            ET.SubElement(new_api, tag).text = api[tag]    
    ET.indent(tree)
    tree.write(path)
    return True

# Digs into a nested dictionary using a dot-separated path string
# e.g. get_nested_value(data, "data.Page.media") walks data -> "data" -> "Page" -> "media"
def get_nested_value(data, path):
    """Follow a dot path like 'data.Page.media.0.title'. Returns None if anything is missing."""
    if not path:
        return None  # optional field not set in settings.xml
    for key in path.split("."):
        if isinstance(data, dict):
            data = data.get(key)
        elif isinstance(data, list):
            try:
                data = data[int(key)]  # numbers in the path are list positions
            except (ValueError, IndexError):
                return None
        else:
            return None
    return data
# ---------- streaming APIs (the <streaming_apis> section) ----------
 
# These tags run programs on your computer, so they are never copied in from imported files
LOCAL_ONLY_TAGS = {"start_dir", "start_command"}
 
# Adds (or replaces, if the name already exists) one <api> in <streaming_apis>
def save_streaming_api(api, path="settings.xml"):
    if not ensure_settings(path):
        return False
    tree = ET.parse(path)
    root = tree.getroot()
    section = root.find("streaming_apis")
    if section is None:
        section = ET.SubElement(root, "streaming_apis")
    for old in section.findall("api"):
        if (old.findtext("name") or "").strip() == api["name"]:
            section.remove(old)
    node = ET.SubElement(section, "api")
    for tag, value in api.items():
        if value:  # skip empty values
            ET.SubElement(node, tag).text = str(value)
    ET.indent(tree)
    tree.write(path)
    return True
 
# Copies every <api> from another XML file into your settings. Returns how many were added.
def import_apis_from_file(file_path, path="settings.xml"):
    try:
        root = ET.parse(file_path).getroot()
    except (OSError, ET.ParseError) as e:
        print(f"Could not read {file_path}: {e}")
        return 0
    section = root if root.tag == "streaming_apis" else root.find("streaming_apis")
    nodes = section.findall("api") if section is not None else root.findall("api")
    added = 0
    for node in nodes:
        api = {c.tag: (c.text or "").strip() for c in node}
        if not api.get("name") or not api.get("type"):
            print("Skipped an <api> without a name or type")
            continue
        for tag in LOCAL_ONLY_TAGS:
            api.pop(tag, None)
        api.setdefault("enabled", "true")
        if save_streaming_api(api, path):
            added += 1
    return added
 
 
# Sets one tag of one streaming API (e.g. Kuhi's start_dir). Returns True if it worked.
def set_streaming_api_value(name, tag, value, path="settings.xml"):
    if not ensure_settings(path):
        return False
    tree = ET.parse(path)
    section = tree.getroot().find("streaming_apis")
    if section is None:
        return False
    for api in section.findall("api"):
        if (api.findtext("name") or "").strip() == name:
            node = api.find(tag)
            if node is None:
                node = ET.SubElement(api, tag)
            node.text = value
            ET.indent(tree)
            tree.write(path)
            return True
    return False

def get_preference(tag,default="", path="settings.xml"):
    if not ensure_settings(path):
        return default
    try:
        value=ET.parse(path).getroot().findtext(f"preferences/{tag}")
    except ET.ParseError:
        return default
    return value.strip() if value and value.strip() else default