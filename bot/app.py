import requests
import re
import time

from datetime import datetime, timedelta
from threading import Timer
from bot import config

headers = {"Private-Token": config.GITLAB_TOKEN}
project = 9202919
options = {"version": [], "device": []}

label_data = {
    "device": {
        "data": True,
        "error": "- A device is required. (include /device devicecodename)",
    },
    "version": {
        "data": True,
        "error": "- The version of LineageOS running on your device is required (include /version lineage-xx.x).",
    },
    "date": {
        "data": False,
        "error": "- Build date is required (include /date YYYY-MM-DD).",
    },
}


def validate(description):
    errors = []
    labels = []
    seen = []
    for line in re.sub(r"<!--.*?-->", "", description, flags=re.DOTALL).splitlines():
        if line.startswith("/") and " " in line:
            str_list = list(filter(None, line.split("/")))
            for pair in str_list:
                if " " not in pair:
                    continue
                spaced = list(filter(None, pair.split(" ")))
                if len(spaced) < 2:
                    continue
                label, value = spaced[0:2]
                if label == "codename":
                    label = "device"
                if value:
                    if label in seen:
                        errors.append(
                            f"{label} is duplicated, please specify only one {label}"
                        )
                    else:
                        seen.append(label)
                if label in label_data.keys():
                    if label_data[label]["data"]:
                        already_valid, value = validate_version(label, value)
                        if value in options[label] or already_valid:
                            labels.append(f"{label}:{value}")
                        elif value:
                            if label == "device":
                                errors.append(
                                    f"- '{value}' is not a valid device codename "
                                    f"(like {', '.join(options[label][0:5])}, ...), see "
                                    "https://wiki.lineageos.org/devices/"
                                )
                            else:
                                errors.append(
                                    f"- '{value}' is not a valid {label}. Supported values are {options[label]}"
                                )
                    else:
                        labels.append(f"{label}")
    missing_labels = label_data.keys() - set(seen)
    for label in missing_labels:
        errors.append(label_data[label]["error"])
    return labels, errors


def validate_version(label, value):
    if label != "version" or not value:
        return False, value
    match = re.search(
        r"(?:lineage-)?((\d{2})(?:\.\d)?)(?:-20\d{6}-NIGHTLY-.+(?:\.zip)?)?", value
    )
    if not match:
        return False, value
    version_full = match.group(1)
    version_major = match.group(2)
    if version_full in options[label]:
        return True, f"lineage-{version_full}"
    if version_major in options[label]:
        return True, f"lineage-{version_major}"
    return False, value


def post_reply(iid, reply):
    try:
        resp = requests.post(
            f"https://gitlab.com/api/v4/projects/{project}/issues/{iid}/notes",
            json={"body": "\n".join(reply)},
            headers=headers,
        )
        if resp.status_code != 201:
            print(f"Error replying - ${resp.json()}")
    except requests.exceptions.RequestException as e:
        print(e)
    except requests.exceptions.JSONDecodeError:
        print(f"Error replying - status  {resp.status_code}")


def edit_issue(iid, edits):
    try:
        resp = requests.put(
            f"https://gitlab.com/api/v4/projects/{project}/issues/{iid}",
            json=edits,
            headers=headers,
        )
        if resp.status_code != 200:
            print(f"Error updating labels - ${resp.json()}")
    except requests.exceptions.RequestException as e:
        print(e)
    except requests.exceptions.JSONDecodeError:
        print(f"Error updating labels - status  {resp.status_code}")


def process_new():
    try:
        resp = requests.get(
            f"https://gitlab.com/api/v4/projects/{project}/issues?state=opened&labels=None",
            headers=headers,
        )
        if resp.status_code != 200:
            print(f"Error updating labels - ${resp.json()}")
    except requests.exceptions.RequestException as e:
        print(e)
        return
    except requests.exceptions.JSONDecodeError:
        print(f"Error replying - status  {resp.status_code}")
        return

    for issue in resp.json():
        labels, errors = validate(issue["description"])
        reply = None
        if errors:
            labels.append("invalid")
            reply = (
                [
                    "Hi! It appears you didn't read or follow the provided issue template."
                    "Your issue has been marked as invalid. Please edit your issue to include "
                    "the requested fields and follow the provided template, then reopen it."
                    "For more information please see https://wiki.lineageos.org/how-to/bugreport",
                    "",
                    "Problems:",
                    "",
                ]
                + errors
                + ["", "(this action was performed by a bot)"]
            )
        if reply:
            post_reply(issue["iid"], reply)
        # edit issue
        edits = {"labels": ",".join(labels)}
        if "invalid" in labels:
            edits["state_event"] = "close"
        edit_issue(issue["iid"], edits)
        print(f"new: {issue['web_url']}")


def process_invalid():
    try:
        resp = requests.get(
            f"https://gitlab.com/api/v4/projects/{project}/issues?state=opened&labels=invalid",
            headers=headers,
        )
        if resp.status_code != 200:
            print(f"Error getting invalid issues - {resp.json()}")
            return
        issues = resp.json()
    except requests.exceptions.RequestException | requests.exceptions.JSONDecodeError as e:
        print(e)
        return

    for issue in issues:
        labels, errors = validate(issue["description"])
        reply = None
        if errors:
            labels.append("invalid")
            reply = (
                [
                    "Hi! It appears this issue still has problems - please fix the things below and reopen it!",
                    "",
                    "Problems:",
                    "",
                ]
                + errors
                + ["", "(this action was performed by a bot)"]
            )
        if reply:
            post_reply(issue["iid"], reply)
        edits = {"labels": ",".join(labels)}
        if "invalid" in labels:
            edits["state_event"] = "close"
        edit_issue(issue["iid"], edits)
        print(f"invalid: {issue['web_url']}")


def load_valid_options():
    global options
    try:
        r = requests.get(
            "https://raw.githubusercontent.com/LineageOS/hudson/master/lineage-build-targets"
        )
    except requests.exceptions.RequestException as e:
        print(e)
        return

    new_options = []
    new_devices = []
    for line in r.text.splitlines():
        if line is None or line == "" or line.startswith("#"):
            continue
        result = re.match(r"^(\w*?) \w*? ([\w\-.]*) \w*", line)
        if result:
            new_devices.append(result.group(1))
            branch_result = re.match(
                r"(?:lineage-)?((\d{2})(?:\.\d)?)", result.group(2)
            )
            if not branch_result:
                continue
            branch_full = branch_result.group(1)
            branch_major = branch_result.group(2)
            if int(branch_major) >= 19:
                branch = branch_major
            else:
                branch = branch_full
            if branch not in new_options:
                new_options.append(branch)
    if new_options:
        options["version"] = new_options
    if new_devices:
        options["device"] = new_devices


def load_options():
    load_valid_options()

    # Do this again one day later once we got valid data
    if not options["version"] or not options["device"]:
        return

    x = datetime.today()
    y = x + timedelta(days=1)
    delta_t = y - x
    secs = delta_t.total_seconds()
    t = Timer(secs, load_options)
    t.start()


if __name__ == "__main__":
    # Load the options and make sure we only start processing if we have valid data
    while True:
        load_options()
        if options["version"] and options["device"]:
            break
        time.sleep(60)

    while True:
        process_new()
        process_invalid()
        time.sleep(60)
