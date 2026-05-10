import types
from unittest.mock import patch

from openskills.remover import remove_skill


class TestRemoveWithDependencies:
    def test_remove_with_no_dependents(self, monkeypatch):
        skill_mock = types.SimpleNamespace(base_dir="/fake/skill", source="/project")
        monkeypatch.setattr("openskills.remover.find_skill", lambda n: skill_mock)
        monkeypatch.setattr("openskills.remover.get_dependents", lambda n: [])
        with patch("shutil.rmtree"):
            remove_skill("solo-skill")

    def test_remove_with_dependents_user_confirms(self, monkeypatch):
        skill_mock = types.SimpleNamespace(base_dir="/fake/skill", source="/project")
        monkeypatch.setattr("openskills.remover.find_skill", lambda n: skill_mock)
        monkeypatch.setattr("openskills.remover.get_dependents", lambda n: [
            {"name": "child-skill", "location": "project"},
        ])
        with patch("openskills.remover.click.confirm", return_value=True), \
             patch("shutil.rmtree"):
            remove_skill("parent-skill")

    def test_remove_with_dependents_user_declines(self, monkeypatch):
        skill_mock = types.SimpleNamespace(base_dir="/fake/skill", source="/project")
        monkeypatch.setattr("openskills.remover.find_skill", lambda n: skill_mock)
        monkeypatch.setattr("openskills.remover.get_dependents", lambda n: [
            {"name": "child-skill", "location": "project"},
        ])
        with patch("openskills.remover.click.confirm", return_value=False), \
             patch("shutil.rmtree") as mock_rm:
            remove_skill("parent-skill")
            mock_rm.assert_not_called()
