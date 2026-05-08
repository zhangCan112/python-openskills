import builtins
from unittest.mock import MagicMock
from click.testing import CliRunner
from openskills.cli import cli
from openskills.models import Skill, SkillLocation


def test_version_flag():
    runner = CliRunner()
    result = runner.invoke(cli, ['--version'])
    assert result.exit_code == 0
    assert 'OpenSkills v' in result.output


def test_no_args_shows_help():
    runner = CliRunner()
    result = runner.invoke(cli, [])
    assert result.exit_code == 0
    assert 'Universal skills manager' in result.output


def test_list_no_skills(monkeypatch):
    monkeypatch.setattr('openskills.cli.find_all_skills', lambda: [])
    runner = CliRunner()
    result = runner.invoke(cli, ['list'])
    assert result.exit_code == 0
    assert 'No skills installed' in result.output


def test_list_with_skills(monkeypatch):
    skills = [
        Skill(name='alpha-skill', description='desc a', location=SkillLocation.PROJECT, path='/p/a'),
        Skill(name='beta-skill', description='desc b', location=SkillLocation.GLOBAL, path='/p/b'),
    ]
    monkeypatch.setattr('openskills.cli.find_all_skills', lambda: skills)
    runner = CliRunner()
    result = runner.invoke(cli, ['list'])
    assert result.exit_code == 0
    assert 'alpha-skill' in result.output
    assert 'beta-skill' in result.output
    assert 'Summary:' in result.output


def test_install_calls_install_skill(monkeypatch):
    mock_install = MagicMock()
    monkeypatch.setattr('openskills.cli.install_skill', mock_install)
    runner = CliRunner()
    result = runner.invoke(cli, ['install', 'some-source'])
    assert result.exit_code == 0
    mock_install.assert_called_once()
    args, kwargs = mock_install.call_args
    assert args[0] == 'some-source'
    opts = args[1]
    assert opts.global_install is False
    assert opts.yes is False


def test_install_global_flag(monkeypatch):
    mock_install = MagicMock()
    monkeypatch.setattr('openskills.cli.install_skill', mock_install)
    runner = CliRunner()
    result = runner.invoke(cli, ['install', 'some-source', '--global'])
    assert result.exit_code == 0
    opts = mock_install.call_args[0][1]
    assert opts.global_install is True


def test_install_yes_flag(monkeypatch):
    mock_install = MagicMock()
    monkeypatch.setattr('openskills.cli.install_skill', mock_install)
    runner = CliRunner()
    result = runner.invoke(cli, ['install', 'some-source', '-y'])
    assert result.exit_code == 0
    opts = mock_install.call_args[0][1]
    assert opts.yes is True


def test_remove_calls_remove_skill(monkeypatch):
    mock_remove = MagicMock()
    monkeypatch.setattr('openskills.cli.remove_skill', mock_remove)
    runner = CliRunner()
    result = runner.invoke(cli, ['remove', 'skill-name'])
    assert result.exit_code == 0
    mock_remove.assert_called_once_with('skill-name')


def test_rm_alias_calls_remove_skill(monkeypatch):
    mock_remove = MagicMock()
    monkeypatch.setattr('openskills.cli.remove_skill', mock_remove)
    runner = CliRunner()
    result = runner.invoke(cli, ['rm', 'skill-name'])
    assert result.exit_code == 0
    mock_remove.assert_called_once_with('skill-name')


def test_update_no_args(monkeypatch):
    mock_update = MagicMock()
    monkeypatch.setattr('openskills.cli.update_skills', mock_update)
    runner = CliRunner()
    result = runner.invoke(cli, ['update'])
    assert result.exit_code == 0
    mock_update.assert_called_once_with(None)


def test_update_with_skill_names(monkeypatch):
    mock_update = MagicMock()
    monkeypatch.setattr('openskills.cli.update_skills', mock_update)
    monkeypatch.setattr('openskills.cli.list', builtins.list)
    runner = CliRunner()
    result = runner.invoke(cli, ['update', 'skill1', 'skill2'])
    assert result.exit_code == 0
    mock_update.assert_called_once_with(['skill1', 'skill2'])


def test_market_list(monkeypatch):
    mock_market_list = MagicMock()
    monkeypatch.setattr('openskills.cli.market_list', mock_market_list)
    runner = CliRunner()
    result = runner.invoke(cli, ['market', 'list'])
    assert result.exit_code == 0
    mock_market_list.assert_called_once()


def test_market_search(monkeypatch):
    mock_market_search = MagicMock()
    monkeypatch.setattr('openskills.cli.market_search', mock_market_search)
    runner = CliRunner()
    result = runner.invoke(cli, ['market', 'search', 'keyword'])
    assert result.exit_code == 0
    mock_market_search.assert_called_once_with('keyword')
