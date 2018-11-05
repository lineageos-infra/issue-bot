import requests
from bot import config

class GitlabApi():
    headers = {"Private-Token": config.GITLAB_TOKEN}
    @classmethod
    def issue_reply(cls, issue, msg):
        pass

    @classmethod
    def issue_label(cls, project, issue_iid, labels):
        resp = requests.put(f"https://gitlab.com/api/v4/projects/{project}/issues/{issue_iid}", json={'labels': ','.join(labels)}, headers=cls.headers)
        if resp.status_code != 200:
            print(f"Error updating labels - ${resp.json()}")
