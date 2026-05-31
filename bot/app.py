import requests
import time

from bot import config

headers = {"Private-Token": config.GITLAB_TOKEN}
project = 9202919
options = {"version": [], "device": []}


def post_reply(iid, reply):
    try:
        resp = requests.post(
            f"https://gitlab.com/api/v4/projects/{project}/issues/{iid}/notes",
            json={"body": "\n".join(reply)},
            headers=headers,
            timeout=10,
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
            timeout=10,
        )
        if resp.status_code != 200:
            print(f"Error updating labels - ${resp.json()}")
    except requests.exceptions.RequestException as e:
        print(e)
    except requests.exceptions.JSONDecodeError:
        print(f"Error updating labels - status  {resp.status_code}")


def process_new_or_invalid():
    issues = []

    try:
        resp = requests.get(
            f"https://gitlab.com/api/v4/projects/{project}/issues?state=opened&labels=None",
            headers=headers,
            timeout=10,
        )
        if resp.status_code != 200:
            print(f"Error getting new issues - {resp.json()}")
            return
        issues += resp.json()
    except Exception as e:
        print(e)

    try:
        resp = requests.get(
            f"https://gitlab.com/api/v4/projects/{project}/issues?state=opened&labels=invalid",
            headers=headers,
            timeout=10,
        )
        if resp.status_code != 200:
            print(f"Error getting invalid issues - {resp.json()}")
            return
        issues += resp.json()
    except Exception as e:
        print(e)

    for issue in issues:
        post_reply(
            issue["iid"],
            [
                "Hi! We've migrated the issue tracker over to [GitHub](https://github.com/LineageOS/issues/issues), please report your issue over there.",
                "",
                "(this action was performed by a bot)",
            ],
        )
        edit_issue(issue["iid"], {"state_event": "close"})
        print(f"closed: {issue['web_url']}")


if __name__ == "__main__":
    while True:
        process_new_or_invalid()
        time.sleep(60)
