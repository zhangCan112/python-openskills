import types
from unittest.mock import patch, MagicMock

from openskills.remover import remove_skill, manage_skills
from openskills.models import Skill, SkillLocation


class TestRemoveWithRecommenders:
    def test_remove_with_no_recommenders(self, monkeypatch):
        skill_mock = types.SimpleNamespace(base_dir="/fake/skill", source="/project")
        monkeypatch.setattr("openskills.remover.find_skill", lambda n: skill_mock)
        monkeypatch.setattr("openskills.remover.get_recommenders", lambda n: [])
        with patch("shutil.rmtree"):
            remove_skill("solo-skill")

    def test_remove_with_recommenders_user_confirms(self, monkeypatch):
        skill_mock = types.SimpleNamespace(base_dir="/fake/skill", source="/project")
        monkeypatch.setattr("openskills.remover.find_skill", lambda n: skill_mock)
        monkeypatch.setattr("openskills.remover.get_recommenders", lambda n: [
            {"name": "child-skill", "location": "project"},
        ])
        with patch("openskills.remover.click.confirm", return_value=True), \
             patch("shutil.rmtree"):
            remove_skill("parent-skill")

    def test_remove_with_recommenders_user_declines(self, monkeypatch):
        skill_mock = types.SimpleNamespace(base_dir="/fake/skill", source="/project")
        monkeypatch.setattr("openskills.remover.find_skill", lambda n: skill_mock)
        monkeypatch.setattr("openskills.remover.get_recommenders", lambda n: [
            {"name": "child-skill", "location": "project"},
        ])
        with patch("openskills.remover.click.confirm", return_value=False), \
             patch("shutil.rmtree") as mock_rm:
            remove_skill("parent-skill")
            mock_rm.assert_not_called()


class TestManageSkills:
    def test_manage_shows_no_ansi_in_choice_names(self, monkeypatch):
        project_skill = Skill(
            name="my-project-skill",
            description="test",
            location=SkillLocation.PROJECT,
            path="/fake/project/my-project-skill",
        )
        global_skill = Skill(
            name="my-global-skill",
            description="test",
            location=SkillLocation.GLOBAL,
            path="/fake/global/my-global-skill",
        )
        monkeypatch.setattr("openskills.remover.find_all_skills", lambda: [project_skill, global_skill])

        captured_choices = {}

        def fake_prompt(message, choices):
            captured_choices['choices'] = choices
            return []

        monkeypatch.setattr("openskills.remover._prompt_for_selection", fake_prompt)

        manage_skills()

        for choice in captured_choices['choices']:
            assert '\x1b' not in choice['name'], f"ANSI escape found in: {choice['name']!r}"
            assert '(project)' in choice['name'] or '(global)' in choice['name']

    def test_manage_no_skills(self, monkeypatch, capsys):
        monkeypatch.setattr("openskills.remover.find_all_skills", lambda: [])
        manage_skills()
        assert "No skills installed" in capsys.readouterr().out
