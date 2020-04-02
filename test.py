import json
import unittest
from unittest.mock import patch

import flask_testing

from bot.app import app

from bot.gitlab.webhooks import Issue

class UsesApp(flask_testing.TestCase):
    def create_app(self):
        return app

class TestGitlabWebhooksIssue(unittest.TestCase):
    def test_invalid_from_issue(self):
        with open("tests/new_invalid_issue.json") as f:
            data = json.loads(f.read())

        issue = Issue.from_issue_hook(data)
        assert issue.validated_labels == ['device:mako', 'invalid']
        assert len(issue.errors) > 0

    def test_valid(self):

        data = {
            "user": {
                "username": "banana"
            },
            "object_attributes": {
                "id": 1,
                "description": "/device mako\\n/version lineage-17.1\\n/date 2018-01-01\\n/kernel 3\\n/mods None\\n/baseband 4"
            }
        }

        issue = Issue.from_issue_hook(data)
        assert issue.validated_labels == ['device:mako', 'version:lineage-17.1', 'date', 'kernel', 'mods', 'baseband']
        assert issue.errors == []

if __name__ == "__main__":
    unittest.main()
