import requests
import json
import re
import time

from urllib.parse import urlencode
from bot import config

headers = {"Private-Token": config.GITLAB_TOKEN}
project = 9202919
options = {
    'version': ["lineage-16.0", "lineage-17.1"],
    'device':  [x["model"] for x in requests.get("https://raw.githubusercontent.com/LineageOS/hudson/master/updater/devices.json").json()]
}

print(options)

label_data = {
    "device": {
        "data": True,
        "error": "- A device is required. (include /device devicecodename)",
    },
    "version": {
        "data": True,
        "error": "- The version of LineageOS running on your device is required (include /version (lineage-16.0,lineage-17.1)."
    },
    "date": {
        "data": False,
        "error": "- Build date is required (include /date YYYY-MM-DD)."
    }
}



def validate(description):
    errors = []
    labels = []
    seen = []
    for line in re.sub("(<!--.*?-->)", "", description, flags=re.DOTALL).splitlines():
        if line.startswith("/") and " " in line:
            label, value = line.split(" ")[0:2]
            if value:
                seen.append(label[1:])
            if label[1:] in label_data.keys():
                if label_data[label[1:]]["data"]:
                    if value in options[label[1:]]:
                        labels.append(f"{label[1:]}:{value}")
                    elif value:
                        errors.append(f"- {value} is not a valid {label[1:]}. Supported values are {options[label[1:]]}")
                else:
                    labels.append(f"{label[1:]}")
    missing_labels = label_data.keys() - set(seen)
    for label in missing_labels:
        errors.append(label_data[label]["error"])
    return labels, errors

def post_reply(iid, reply):
    resp = requests.post(f"https://gitlab.com/api/v4/projects/{project}/issues/{iid}/notes", json={"body": "\n".join(reply)}, headers=headers)
    if resp.status_code != 201:
        print(f"Error replying - ${resp.json()}")

def edit_issue(iid, edits):
    resp = requests.put(f"https://gitlab.com/api/v4/projects/{project}/issues/{iid}", json=edits, headers=headers)
    if resp.status_code != 200:
        print(f"Error updating labels - ${resp.json()}")

def process_new():
    resp = requests.get(f"https://gitlab.com/api/v4/projects/{project}/issues?state=opened&labels=None", headers=headers)
    if resp.status_code != 200:
        print(f"Error getting issues - {resp.json()}")
        return
    for issue in resp.json():
        labels, errors = validate(issue["description"])
        reply = None
        if errors:
            labels.append("invalid")
            reply = [
                "Hi! It appears you didn't read or follow the provided issue template. Your issue has been marked as invalid. You can either edit your issue to include the requested fields and reopen it, or create a new issue following the provided template. For more information, please see https://wiki.lineageos.org/bugreport-howto.html",
                "",
                "Problems:",
                ""
            ] + errors + ["", "(this action was performed by a bot)"]
        if reply:
            post_reply(issue["iid"], reply)
        # edit issue
        edits = {
            "labels": ",".join(labels)
        }
        if "invalid" in labels:
            edits["state_event"] = "close"
        edit_issue(issue["iid"], edits)
        print(f"new: {issue['web_url']}")

def process_invalid():
    resp = requests.get(f"https://gitlab.com/api/v4/projects/{project}/issues?state=opened&labels=invalid", headers=headers)
    if resp.status_code != 200:
        print(f"Error getting invalid issues - {resp.json()}")
        return
    for issue in resp.json():
        labels, errors = validate(issue["description"])
        reply = None
        if errors:
            labels.append("invalid")
            reply = [
                "Hi! It appears this issue still has problems - please fix the things below and reopen it!",
                "",
                "Problems:",
                ""
            ] + errors + ["", "(this action was performed by a bot)"]
        if reply:
            post_reply(issue["iid"], reply)
        edits = {
            "labels": ",".join(labels)
        }
        if "invalid" in labels:
            edits["state_event"] = "close"
        edit_issue(issue["iid"], edits)
        print(f"invalid: {issue['web_url']}")

if __name__ == "__main__":
    while True:
        process_new()
        process_invalid()
        time.sleep(60)

