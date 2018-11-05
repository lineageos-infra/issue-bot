class Issue():
    labels = {
        "device": {
            "data": True,
            "error": "- A device is required. Reply with /device <yourmodel>"
        },
        "version": {
            "data": True,
            "error": "- The version of LineageOS running on your device is required. Reply with /version (cm-14.1,lineage-15.1)"
        },
        "date": {
            "data": False,
            "error": "- Build date is required. Reply with /date YYYY-MM-DD"
        },
        "kernel": {
            "data": False,
            "error": "- Kernel version is required. Reply with /kernel <version>"
        },
        "baseband": {
            "data": False,
            "error": "- Device baseband version is required. Reply with /baseband <version>"
        },
        "mods": {
            "data": False,
            "error": "- A list of system modifications is required. Reply with /mods <list>. If none are present, reply with /mods None"
        }
    }

    def _get_labels(self):
        errors = []
        for line in self.description.split("\\n"):
            if line.startswith("/") and " " in line:
                label, value = line.split(" ")[0:2]

                if label[1:] in self.labels.keys():
                    if self.labels[label[1:]]["data"]:
                        self.validated_labels.append(f"{label[1:]}:{value}")
                    else:
                        self.validated_labels.append(f"{label[1:]}")

    def _validate_labels(self):
        missing_labels = set(self.labels.keys()) - set(self.validated_labels)

        for label in missing_labels:
            if self.labels[label]['data']:
                if not any(label in x for x in self.labels.keys()):
                    self.errors.append(self.labels[label]["error"])
            else:
                self.errors.append(self.labels[label]["error"])

        if self.errors:
            self.validated_labels.append("invalid")

    def _process_issue(self):
        self._get_labels()
        self._validate_labels()

    def _process_comment(self):
        pass

    @classmethod
    def from_issue_hook(cls, data):
        instance = cls(data=data)
        instance._process_issue()
        return instance

    @classmethod
    def from_note_hook(cls, data):
        instance = cls(data=data)
        instance._process_comment()
        return instance

    def __init__(self, data):
        self.description = data.get("object_attributes", {}).get("description")
        self.iid = data.get("object_attributes", {}).get("iid")
        self.project_id = data.get("project", {}).get("id")
        self.validated_labels = []
        self.errors = []