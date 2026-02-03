import importlib.util
import os
import sys
import unittest


MODULE_PATH = os.path.join(os.path.dirname(__file__), "publish_chat_epic.py")
SPEC = importlib.util.spec_from_file_location("publish_chat_epic", MODULE_PATH)
publish_chat_epic = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules["publish_chat_epic"] = publish_chat_epic
SPEC.loader.exec_module(publish_chat_epic)


class TestEpicLabels(unittest.TestCase):
    def test_default_epic_added(self) -> None:
        labels = publish_chat_epic.build_epic_labels(
            labels=["bug"], epic_labels=["priority"]
        )
        self.assertEqual(labels, ["bug", "priority", "epic"])

    def test_epic_not_duplicated(self) -> None:
        labels = publish_chat_epic.build_epic_labels(
            labels=["epic", "bug"], epic_labels=["epic"]
        )
        self.assertEqual(labels.count("epic"), 1)


if __name__ == "__main__":
    unittest.main()
