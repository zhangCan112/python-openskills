import os
import re
import json
import tempfile
import webbrowser
from collections import defaultdict
from typing import Any, Dict, List

import click

MARKETSKILLS_INDEX = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'marketskills', 'market_index.json')


class MarketSkill:

    def __init__(self, name: str, description: str, repo: str, branch: str,
                 subpath: str = '', version: str = '', author: str = ''):
        self.name = name
        self.description = description
        self.repo = repo
        self.branch = branch
        self.subpath = subpath
        self.version = version
        self.author = author

    @property
    def source(self) -> str:
        if self.subpath:
            return f"{self.repo}/{self.subpath}"
        return self.repo

    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'description': self.description,
            'repo': self.repo,
            'branch': self.branch,
            'subpath': self.subpath,
            'version': self.version,
            'author': self.author
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any], repo: str, branch: str) -> 'MarketSkill':
        return cls(
            name=data['name'],
            description=data.get('description', ''),
            repo=repo,
            branch=branch,
            subpath=data.get('subpath', ''),
            version=data.get('version', ''),
            author=data.get('author', '')
        )


def load_market_skills() -> List[MarketSkill]:
    skills = []
    if not os.path.exists(MARKETSKILLS_INDEX):
        return skills
    try:
        with open(MARKETSKILLS_INDEX, 'r', encoding='utf-8') as f:
            data = json.load(f)
        for source_data in data.get('sources', []):
            repo = source_data.get('repo', '')
            branch = source_data.get('branch', 'main')
            for skill_data in source_data.get('skills', []):
                try:
                    skill = MarketSkill.from_dict(skill_data, repo, branch)
                    skills.append(skill)
                except KeyError:
                    continue
    except (json.JSONDecodeError, KeyError):
        pass
    return skills


def find_skill_by_name(name: str) -> List[MarketSkill]:
    all_skills = load_market_skills()
    return [skill for skill in all_skills if skill.name.lower() == name.lower()]


def search_skills(keyword: str) -> List[MarketSkill]:
    all_skills = load_market_skills()
    keyword_lower = keyword.lower()
    matched_skills = []
    for skill in all_skills:
        if keyword_lower in skill.name.lower():
            matched_skills.append(skill)
            continue
        if keyword_lower in skill.description.lower():
            matched_skills.append(skill)
    return matched_skills


def list_all_skills() -> List[MarketSkill]:
    return load_market_skills()


def get_unique_skill_names() -> List[str]:
    all_skills = load_market_skills()
    unique_names = set(skill.name.lower() for skill in all_skills)
    return sorted(list(unique_names))


def market_list(html=False):
    skills = list_all_skills()
    if not skills:
        click.echo(click.style("No skills found in market", fg='yellow'))
        click.echo("Use 'openskills market search <keyword>' to search")
        return
    if html:
        temp_path = generate_market_html(skills)
        click.echo(click.style("[OK] HTML page opened in browser", fg='green', bold=True))
        click.echo(click.style(f"  Temp file path: {temp_path}", fg='cyan'))
        return
    _display_terminal_output(skills)


def market_search(keyword: str):
    skills = search_skills(keyword)
    if not skills:
        click.echo(click.style(f"No skills found matching '{keyword}'", fg='yellow'))
        return
    click.echo(click.style(f"Found {len(skills)} skill(s) matching '{keyword}'\n", bold=True))
    _display_terminal_output(skills, keyword)


def _display_terminal_output(skills, keyword: str | None = None):
    skills_by_name = defaultdict(list)
    for skill in skills:
        skills_by_name[skill.name].append(skill)
    for skill_name, skill_variants in sorted(skills_by_name.items()):
        click.echo(click.style(f"{skill_name}", fg='cyan', bold=True))
        for i, skill in enumerate(skill_variants):
            if len(skill_variants) > 1:
                variant_label = f"  [{i+1}] "
            else:
                variant_label = "      "
            if skill.description:
                description = skill.description
                if keyword:
                    description = re.sub(
                        f'({keyword})',
                        click.style(r'\1', fg='yellow', bold=True),
                        description,
                        flags=re.IGNORECASE
                    )
                click.echo(f"{variant_label}{description}")
            else:
                click.echo(f"{variant_label}No description")
            click.echo(f"      Source: {skill.source}")
            if skill.author:
                click.echo(f"      Author: {skill.author}")
            if skill.version:
                click.echo(f"      Version: {skill.version}")
            click.echo()


def generate_market_html(skills):
    skills_data = []
    for skill in skills:
        repo = skill.repo
        skills_data.append({
            'name': skill.name,
            'description': skill.description,
            'source': skill.source,
            'repo': repo,
            'author': skill.author,
            'version': skill.version,
            'install_command': f'openskills install {skill.source}'
        })

    css_styles = """
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            min-height: 100vh;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
        }

        h1 {
            color: white;
            text-align: center;
            margin-bottom: 30px;
            font-size: 2.5em;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }

        .search-box {
            background: white;
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }

        .search-input {
            width: 100%;
            padding: 15px 20px;
            font-size: 16px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            transition: border-color 0.3s;
        }

        .search-input:focus {
            outline: none;
            border-color: #667eea;
        }

        .stats {
            margin-top: 15px;
            color: #666;
            font-size: 14px;
        }

        .skills-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
            gap: 20px;
        }

        .skill-card {
            background: white;
            border-radius: 12px;
            padding: 25px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            transition: transform 0.3s, box-shadow 0.3s;
            display: flex;
            flex-direction: column;
        }

        .skill-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 12px rgba(0,0,0,0.15);
        }

        .skill-name {
            color: #667eea;
            font-size: 1.5em;
            font-weight: bold;
            margin-bottom: 10px;
        }

        .skill-description {
            color: #555;
            line-height: 1.6;
            margin-bottom: 15px;
            flex-grow: 1;
        }

        .skill-meta {
            margin-bottom: 15px;
            color: #777;
            font-size: 0.9em;
        }

        .skill-meta div {
            margin: 3px 0;
        }

        .source-section {
            background: white;
            border-radius: 16px;
            padding: 25px;
            margin-bottom: 30px;
            box-shadow: 0 6px 10px rgba(0,0,0,0.1);
        }

        .source-section-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 25px;
            padding-bottom: 15px;
            border-bottom: 3px solid #f0f0f0;
            cursor: pointer;
            transition: background 0.3s;
        }

        .source-section-header:hover {
            background: #f8f9fa;
            padding-left: 10px;
            padding-right: 10px;
        }

        .header-left {
            display: flex;
            align-items: center;
            flex: 1;
        }

        .collapse-button {
            font-size: 24px;
            color: #667eea;
            cursor: pointer;
            transition: transform 0.3s;
            user-select: none;
            padding: 5px 10px;
            margin-right: 15px;
        }

        .collapse-button:hover {
            transform: scale(1.1);
        }

        .source-section.collapsed .collapse-button {
            transform: rotate(-90deg);
        }

        .source-section.collapsed .skills-grid {
            display: none;
        }

        .source-section-title {
            font-size: 1.8em;
            font-weight: bold;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        .source-section-count {
            margin-left: 15px;
            padding: 5px 15px;
            background: #f0f0f0;
            border-radius: 20px;
            color: #666;
            font-size: 0.9em;
            font-weight: 600;
        }

        .source-section .skills-grid {
            gap: 20px;
        }

        .copy-button {
            background: #667eea;
            color: white;
            border: none;
            padding: 12px 20px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 14px;
            font-weight: bold;
            transition: background 0.3s;
            width: 100%;
        }

        .copy-button:hover {
            background: #5568d3;
        }

        .copy-button.copied {
            background: #4caf50;
        }

        .install-command {
            margin-top: 10px;
            padding: 10px;
            background: #f5f5f5;
            border-radius: 6px;
            font-family: 'Courier New', monospace;
            font-size: 13px;
            color: #333;
            word-break: break-all;
        }

        .no-results {
            text-align: center;
            color: white;
            font-size: 1.5em;
            padding: 50px;
            background: rgba(255,255,255,0.1);
            border-radius: 12px;
        }

        .highlight {
            background: linear-gradient(120deg, #ffd54f 0%, #ffca28 100%);
            padding: 2px 4px;
            border-radius: 3px;
            font-weight: 600;
            color: #333;
        }

        @media (max-width: 768px) {
            .skills-grid {
                grid-template-columns: 1fr;
            }

            h1 {
                font-size: 2em;
            }

            .source-section-title {
                font-size: 1.4em;
            }
        }
"""

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OpenSkills Market</title>
    <style>{css_styles}</style>
</head>
<body>
    <div class="container">
        <h1>🛠️ OpenSkills Market</h1>

        <div class="search-box">
            <input type="text" class="search-input" id="searchInput" placeholder="🔍 Search skill name or description...">
            <div class="stats" id="stats"></div>
        </div>

        <div id="contentContainer"></div>
        <div id="noResults" class="no-results" style="display: none;">No matching skills found</div>
    </div>

    <script>
        const skills = {json.dumps(skills_data, ensure_ascii=False, indent=2)};

        const searchInput = document.getElementById('searchInput');
        const contentContainer = document.getElementById('contentContainer');
        const noResults = document.getElementById('noResults');
        const stats = document.getElementById('stats');

        function init() {{
            console.log('Initializing page...');
            console.log('Skills count:', skills.length);
            renderSkillsGroupedBySource(skills);
            updateStats(skills.length, skills.length);
            console.log('Page initialized successfully!');
        }}

        function highlightText(text, searchTerm) {{
            if (!searchTerm) return escapeHtml(text || '');
            const escapedText = escapeHtml(text || '');
            const escapedSearchTerm = escapeHtml(searchTerm);
            const regex = new RegExp('(' + escapeRegex(escapedSearchTerm) + ')', 'gi');
            return escapedText.replace(regex, '<span class="highlight">$1</span>');
        }}

        function escapeRegex(string) {{
            return string.replace(/[.*+?^${{}}()|[\\]\\\\]/g, '\\\\$&');
        }}

        function renderSkillsGroupedBySource(skillsToRender, searchTerm) {{
            console.log('Rendering skills grouped by repo:', skillsToRender.length);

            const grouped = {{}};
            skillsToRender.forEach(skill => {{
                if (!grouped[skill.repo]) {{
                    grouped[skill.repo] = [];
                }}
                grouped[skill.repo].push(skill);
            }});

            const sourcesHtml = Object.entries(grouped).map(([repo, repoSkills]) => `
                <div class="source-section">
                    <div class="source-section-header">
                        <div class="header-left">
                            <span class="collapse-button">▼</span>
                            <div class="source-section-title">${{escapeHtml(repo)}}</div>
                            <div class="source-section-count">${{repoSkills.length}} skills</div>
                        </div>
                    </div>
                    <div class="skills-grid">
                        ${{repoSkills.map(skill => `
                            <div class="skill-card">
                                <div class="skill-name">${{highlightText(skill.name, searchTerm)}}</div>
                                <div class="skill-description">${{highlightText(skill.description || 'No description available', searchTerm)}}</div>
                                <div class="skill-meta">
                                    ${{skill.author ? `<div>👤 Author: ${{highlightText(skill.author, searchTerm)}}</div>` : ''}}
                                    ${{skill.version ? `<div>📦 Version: ${{highlightText(skill.version, searchTerm)}}</div>` : ''}}
                                </div>
                                <button class="copy-button" data-command="${{escapeHtml(skill.install_command)}}">
                                    📋 Copy Install Command
                                </button>
                                <div class="install-command">${{escapeHtml(skill.install_command)}}</div>
                            </div>
                        `).join('')}}
                    </div>
                </div>
            `).join('');

            contentContainer.innerHTML = sourcesHtml;

            noResults.style.display = skillsToRender.length === 0 ? 'block' : 'none';
            if (skillsToRender.length === 0) {{
                contentContainer.innerHTML = noResults.outerHTML;
            }}
        }}

        function filterSkills() {{
            const searchTerm = searchInput.value;
            const searchTermLower = searchTerm.toLowerCase();

            const filtered = skills.filter(skill => {{
                const matchesSearch = !searchTermLower ||
                    skill.name.toLowerCase().includes(searchTermLower) ||
                    (skill.description && skill.description.toLowerCase().includes(searchTermLower)) ||
                    skill.author.toLowerCase().includes(searchTermLower);

                return matchesSearch;
            }});

            renderSkillsGroupedBySource(filtered, searchTerm);
            updateStats(filtered.length, skills.length);
        }}

        function updateStats(visible, total) {{
            stats.textContent = `Showing ${{visible}} / ${{total}} skills`;
        }}

        function copyCommand(button) {{
            const command = button.getAttribute('data-command');
            navigator.clipboard.writeText(command).then(() => {{
                button.textContent = '✅ Copied!';
                button.classList.add('copied');
                setTimeout(() => {{
                    button.textContent = '📋 Copy Install Command';
                    button.classList.remove('copied');
                }}, 2000);
            }}).catch(err => {{
                console.error('Copy failed:', err);
                button.textContent = '❌ Copy Failed';
                setTimeout(() => {{
                    button.textContent = '📋 Copy Install Command';
                }}, 2000);
            }});
        }}

        function escapeHtml(text) {{
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }}

        searchInput.addEventListener('input', filterSkills);

        contentContainer.addEventListener('click', (e) => {{
            if (e.target.classList.contains('copy-button')) {{
                copyCommand(e.target);
            }}

            if (e.target.classList.contains('collapse-button') ||
                e.target.closest('.source-section-header') && !e.target.closest('.copy-button')) {{
                const section = e.target.closest('.source-section');
                if (section) {{
                    section.classList.toggle('collapsed');
                }}
            }}
        }});

        if (document.readyState === 'loading') {{
            document.addEventListener('DOMContentLoaded', init);
        }} else {{
            init();
        }}
    </script>
</body>
</html>"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
        f.write(html_content)
        temp_path = f.name

    webbrowser.open(f'file://{temp_path}')

    return temp_path
