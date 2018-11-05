from flask import Flask, request, abort
import json

from bot.gitlab.webhooks import Issue
from bot.gitlab import GitlabApi
app = Flask(__name__)

@app.route("/", methods=("POST",))
@app.route("/webhook", methods=("POST",))
def webhook():
    if request.headers.get("X-Gitlab-Token") != config.GITLAB_WEBHOOK_TOKEN:
        abort(403)
    if request.headers.get("X-Gitlab-Event") == "Issue Hook":
        print('changes' in request.json)
        issue = Issue.from_issue_hook(request.json)

        print(issue.validated_labels)
        print(issue.errors)
    print('foo')
if __name__ == "__main__":
    app.run()