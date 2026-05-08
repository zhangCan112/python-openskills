import json
import os
from typing import List

import pytest

from openskills.market import (
    MarketSkill,
    find_skill_by_name,
    get_unique_skill_names,
    list_all_skills,
    load_market_skills,
    search_skills,
)


class TestMarketSkillInit:
    def test_creation_with_required_fields(self):
        skill = MarketSkill(
            name='my-skill',
            description='A test skill',
            repo='https://github.com/owner/repo',
            branch='main',
        )
        assert skill.name == 'my-skill'
        assert skill.description == 'A test skill'
        assert skill.repo == 'https://github.com/owner/repo'
        assert skill.branch == 'main'

    def test_default_optional_fields(self):
        skill = MarketSkill(
            name='my-skill',
            description='desc',
            repo='https://github.com/owner/repo',
            branch='main',
        )
        assert skill.subpath == ''
        assert skill.version == ''
        assert skill.author == ''


class TestMarketSkillSource:
    def test_source_without_subpath(self):
        skill = MarketSkill(
            name='s',
            description='d',
            repo='https://github.com/owner/repo',
            branch='main',
        )
        assert skill.source == 'https://github.com/owner/repo'

    def test_source_with_subpath(self):
        skill = MarketSkill(
            name='s',
            description='d',
            repo='https://github.com/owner/repo',
            branch='main',
            subpath='skills/sub',
        )
        assert skill.source == 'https://github.com/owner/repo/skills/sub'


class TestMarketSkillToDict:
    def test_to_dict_returns_all_fields(self):
        skill = MarketSkill(
            name='s',
            description='d',
            repo='https://github.com/owner/repo',
            branch='main',
            subpath='sub',
            version='1.0',
            author='me',
        )
        result = skill.to_dict()
        assert result == {
            'name': 's',
            'description': 'd',
            'repo': 'https://github.com/owner/repo',
            'branch': 'main',
            'subpath': 'sub',
            'version': '1.0',
            'author': 'me',
        }


class TestMarketSkillFromDict:
    def test_from_dict_with_defaults(self):
        data = {'name': 'my-skill'}
        skill = MarketSkill.from_dict(data, repo='https://github.com/o/r', branch='dev')
        assert skill.name == 'my-skill'
        assert skill.description == ''
        assert skill.repo == 'https://github.com/o/r'
        assert skill.branch == 'dev'
        assert skill.subpath == ''
        assert skill.version == ''
        assert skill.author == ''

    def test_from_dict_with_all_fields(self):
        data = {
            'name': 'my-skill',
            'description': 'desc',
            'subpath': 'path',
            'version': '2.0',
            'author': 'you',
        }
        skill = MarketSkill.from_dict(data, repo='https://github.com/o/r', branch='main')
        assert skill.name == 'my-skill'
        assert skill.description == 'desc'
        assert skill.subpath == 'path'
        assert skill.version == '2.0'
        assert skill.author == 'you'


class TestLoadMarketSkills:
    def test_returns_empty_when_dir_missing(self, monkeypatch, tmp_path):
        nonexistent = os.path.join(str(tmp_path), 'no_such_dir')
        monkeypatch.setattr('openskills.market.MARKETSKILLS_DIR', nonexistent)
        assert load_market_skills() == []

    def test_returns_empty_for_empty_directory(self, monkeypatch, tmp_path):
        monkeypatch.setattr('openskills.market.MARKETSKILLS_DIR', str(tmp_path))
        assert load_market_skills() == []

    def test_loads_skills_from_valid_json(self, monkeypatch, tmp_path):
        data = {
            'repo': 'https://github.com/owner/repo',
            'branch': 'main',
            'skills': [
                {'name': 'skill-a', 'description': 'First skill'},
                {'name': 'skill-b', 'description': 'Second skill'},
            ],
        }
        filepath = os.path.join(str(tmp_path), 'skills.json')
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f)
        monkeypatch.setattr('openskills.market.MARKETSKILLS_DIR', str(tmp_path))

        skills = load_market_skills()
        assert len(skills) == 2
        assert skills[0].name == 'skill-a'
        assert skills[1].name == 'skill-b'
        assert skills[0].repo == 'https://github.com/owner/repo'
        assert skills[0].branch == 'main'

    def test_skips_non_json_files(self, monkeypatch, tmp_path):
        txt_file = os.path.join(str(tmp_path), 'readme.txt')
        with open(txt_file, 'w') as f:
            f.write('not json')
        monkeypatch.setattr('openskills.market.MARKETSKILLS_DIR', str(tmp_path))
        assert load_market_skills() == []

    def test_skips_invalid_json(self, monkeypatch, tmp_path):
        filepath = os.path.join(str(tmp_path), 'bad.json')
        with open(filepath, 'w') as f:
            f.write('not valid json{{{')
        monkeypatch.setattr('openskills.market.MARKETSKILLS_DIR', str(tmp_path))
        assert load_market_skills() == []

    def test_skips_entry_missing_name_key(self, monkeypatch, tmp_path):
        data = {
            'repo': 'https://github.com/owner/repo',
            'branch': 'main',
            'skills': [
                {'description': 'No name field'},
            ],
        }
        filepath = os.path.join(str(tmp_path), 'bad_skill.json')
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f)
        monkeypatch.setattr('openskills.market.MARKETSKILLS_DIR', str(tmp_path))
        assert load_market_skills() == []


def _make_skill(name, description='', repo='https://github.com/o/r', branch='main'):
    return MarketSkill(name=name, description=description, repo=repo, branch=branch)


class TestFindSkillByName:
    def test_returns_empty_when_no_match(self, monkeypatch):
        skills = [_make_skill('alpha'), _make_skill('beta')]
        monkeypatch.setattr('openskills.market.load_market_skills', lambda: skills)
        assert find_skill_by_name('gamma') == []

    def test_case_insensitive_match(self, monkeypatch):
        s1 = _make_skill('My-Skill')
        skills = [_make_skill('alpha'), s1]
        monkeypatch.setattr('openskills.market.load_market_skills', lambda: skills)
        result = find_skill_by_name('my-skill')
        assert len(result) == 1
        assert result[0].name == 'My-Skill'

    def test_multiple_skills_same_name_different_repos(self, monkeypatch):
        s1 = _make_skill('dup', repo='https://github.com/a/r1')
        s2 = _make_skill('dup', repo='https://github.com/b/r2')
        skills = [s1, s2]
        monkeypatch.setattr('openskills.market.load_market_skills', lambda: skills)
        result = find_skill_by_name('dup')
        assert len(result) == 2


class TestSearchSkills:
    def test_returns_empty_when_no_match(self, monkeypatch):
        skills = [_make_skill('alpha', 'desc a')]
        monkeypatch.setattr('openskills.market.load_market_skills', lambda: skills)
        assert search_skills('zzz') == []

    def test_matches_name_case_insensitive(self, monkeypatch):
        s = _make_skill('Python-Tool', 'some desc')
        monkeypatch.setattr('openskills.market.load_market_skills', lambda: [s])
        result = search_skills('python')
        assert len(result) == 1

    def test_matches_description_case_insensitive(self, monkeypatch):
        s = _make_skill('tool', 'Great for Data Science')
        monkeypatch.setattr('openskills.market.load_market_skills', lambda: [s])
        result = search_skills('data science')
        assert len(result) == 1

    def test_matches_name_or_description(self, monkeypatch):
        s1 = _make_skill('web-scraper', 'scrapes websites')
        s2 = _make_skill('data-tool', 'processes web data')
        s3 = _make_skill('other', 'unrelated')
        monkeypatch.setattr(
            'openskills.market.load_market_skills', lambda: [s1, s2, s3]
        )
        result = search_skills('web')
        assert len(result) == 2


class TestListAllSkills:
    def test_returns_all_loaded_skills(self, monkeypatch):
        skills = [_make_skill('a'), _make_skill('b'), _make_skill('c')]
        monkeypatch.setattr('openskills.market.load_market_skills', lambda: skills)
        assert list_all_skills() == skills


class TestGetUniqueSkillNames:
    def test_returns_sorted_unique_lowercase(self, monkeypatch):
        skills = [_make_skill('Charlie'), _make_skill('Alpha'), _make_skill('Bravo')]
        monkeypatch.setattr('openskills.market.load_market_skills', lambda: skills)
        assert get_unique_skill_names() == ['alpha', 'bravo', 'charlie']

    def test_deduplicates_from_different_sources(self, monkeypatch):
        s1 = _make_skill('MySkill', repo='https://github.com/a/r1')
        s2 = _make_skill('myskill', repo='https://github.com/b/r2')
        monkeypatch.setattr('openskills.market.load_market_skills', lambda: [s1, s2])
        assert get_unique_skill_names() == ['myskill']
