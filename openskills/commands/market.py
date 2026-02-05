"""
Market commands for listing and searching skills
"""

import click
import json
import tempfile
import webbrowser
from pathlib import Path
from openskills.utils.market import (
    list_all_skills,
    search_skills,
    find_skill_by_name
)


def generate_market_html(skills):
    """Generate an interactive HTML page for browsing market skills"""
    # Collect all unique tags
    all_tags = set()
    for skill in skills:
        all_tags.update(skill.tags)
    all_tags = sorted(all_tags)
    
    # Prepare skills data for JavaScript
    skills_data = []
    for skill in skills:
        skills_data.append({
            'name': skill.name,
            'description': skill.description,
            'source': skill.source,
            'author': skill.author,
            'version': skill.version,
            'tags': skill.tags,
            'install_command': f'openskills install {skill.source}'
        })
    
    # Generate tags HTML
    tags_html = ''.join(f'<span class="tag" data-tag="{tag}">{tag}</span>' for tag in all_tags)
    
    # CSS styles
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
        
        .tags-section {
            background: white;
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        
        .tags-section h3 {
            margin-bottom: 15px;
            color: #333;
        }
        
        .tag {
            display: inline-block;
            padding: 8px 16px;
            margin: 5px;
            background: #f0f0f0;
            border-radius: 20px;
            cursor: pointer;
            transition: all 0.3s;
            user-select: none;
        }
        
        .tag:hover {
            background: #e0e0e0;
        }
        
        .tag.selected {
            background: #667eea;
            color: white;
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
        
        .skill-tags {
            margin-bottom: 15px;
        }
        
        .skill-tags .tag {
            font-size: 12px;
            padding: 4px 10px;
            margin: 3px;
            background: #e8f4f8;
            color: #1976d2;
        }
        
        .skill-tags .tag.selected {
            background: #667eea;
            color: white;
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
        
        @media (max-width: 768px) {
            .skills-grid {
                grid-template-columns: 1fr;
            }
            
            h1 {
                font-size: 2em;
            }
        }
"""
    
    # Build HTML content
    html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
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
            <input type="text" class="search-input" id="searchInput" placeholder="🔍 搜索技能名称、描述或标签...">
        </div>
        
        <div class="tags-section">
            <h3>📌 按标签筛选</h3>
            <div id="tagsContainer">{tags_html}</div>
            <div class="stats">
                <span id="stats"></span>
            </div>
        </div>
        
        <div class="skills-grid" id="skillsGrid"></div>
        <div id="noResults" class="no-results" style="display: none;">没有找到匹配的技能</div>
    </div>
    
    <script>
        // Skills data
        const skills = {json.dumps(skills_data, ensure_ascii=False, indent=2)};
        let selectedTags = [];
        
        const searchInput = document.getElementById('searchInput');
        const skillsGrid = document.getElementById('skillsGrid');
        const tagsContainer = document.getElementById('tagsContainer');
        const noResults = document.getElementById('noResults');
        const stats = document.getElementById('stats');
        
        // Initialize
        function init() {{
            console.log('Initializing page...');
            console.log('Skills count:', skills.length);
            renderSkills(skills);
            updateStats(skills.length, skills.length);
            console.log('Page initialized successfully!');
        }}
        
        // Render skills cards
        function renderSkills(skillsToRender) {{
            console.log('Rendering skills:', skillsToRender.length);
            skillsGrid.innerHTML = skillsToRender.map(skill => `
                <div class="skill-card">
                    <div class="skill-name">${{escapeHtml(skill.name)}}</div>
                    <div class="skill-description">${{escapeHtml(skill.description || '暂无描述')}}</div>
                    <div class="skill-meta">
                        ${{skill.author ? `<div>👤 作者: ${{escapeHtml(skill.author)}}</div>` : ''}}
                        ${{skill.version ? `<div>📦 版本: ${{escapeHtml(skill.version)}}</div>` : ''}}
                        <div>🔗 源: ${{escapeHtml(skill.source)}}</div>
                    </div>
                    <div class="skill-tags">
                        ${{skill.tags.map(tag => `<span class="tag" data-tag="${{escapeHtml(tag)}}">${{escapeHtml(tag)}}</span>`).join('')}}
                    </div>
                    <button class="copy-button" data-command="${{escapeHtml(skill.install_command)}}">
                        📋 复制安装命令
                    </button>
                    <div class="install-command">${{escapeHtml(skill.install_command)}}</div>
                </div>
            `).join('');
            
            // Show/hide no results message
            noResults.style.display = skillsToRender.length === 0 ? 'block' : 'none';
        }}
        
        // Filter skills based on search and tags
        function filterSkills() {{
            const searchTerm = searchInput.value.toLowerCase();
            
            const filtered = skills.filter(skill => {{
                // Check search term
                const matchesSearch = !searchTerm ||
                    skill.name.toLowerCase().includes(searchTerm) ||
                    (skill.description && skill.description.toLowerCase().includes(searchTerm)) ||
                    skill.tags.some(tag => tag.toLowerCase().includes(searchTerm));
                
                // Check tags (AND logic)
                const matchesTags = selectedTags.length === 0 ||
                    selectedTags.every(tag => skill.tags.includes(tag));
                
                return matchesSearch && matchesTags;
            }});
            
            renderSkills(filtered);
            updateStats(filtered.length, skills.length);
            
            // Update tag visibility based on filtered skills
            updateTagVisibility(filtered);
        }}
        
        // Update tag visibility
        function updateTagVisibility(filteredSkills) {{
            const visibleTags = new Set();
            filteredSkills.forEach(skill => {{
                skill.tags.forEach(tag => visibleTags.add(tag));
            }});
            
            document.querySelectorAll('#tagsContainer .tag').forEach(tagEl => {{
                const tag = tagEl.dataset.tag;
                if (!visibleTags.has(tag) && !selectedTags.includes(tag)) {{
                    tagEl.style.opacity = '0.3';
                    tagEl.style.pointerEvents = 'none';
                }} else {{
                    tagEl.style.opacity = '1';
                    tagEl.style.pointerEvents = 'auto';
                }}
            }});
        }}
        
        // Update stats
        function updateStats(visible, total) {{
            stats.textContent = `显示 ${{visible}} / 共 ${{total}} 个技能`;
        }}
        
        // Copy command to clipboard
        function copyCommand(button) {{
            const command = button.getAttribute('data-command');
            navigator.clipboard.writeText(command).then(() => {{
                button.textContent = '✅ 已复制!';
                button.classList.add('copied');
                setTimeout(() => {{
                    button.textContent = '📋 复制安装命令';
                    button.classList.remove('copied');
                }}, 2000);
            }}).catch(err => {{
                console.error('复制失败:', err);
                button.textContent = '❌ 复制失败';
                setTimeout(() => {{
                    button.textContent = '📋 复制安装命令';
                }}, 2000);
            }});
        }}
        
        // Escape HTML to prevent XSS
        function escapeHtml(text) {{
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }}
        
        // Event listeners
        searchInput.addEventListener('input', filterSkills);
        
        skillsGrid.addEventListener('click', (e) => {{
            if (e.target.classList.contains('copy-button')) {{
                copyCommand(e.target);
            }}
        }});
        
        tagsContainer.addEventListener('click', (e) => {{
            if (e.target.classList.contains('tag')) {{
                const tag = e.target.dataset.tag;
                const index = selectedTags.indexOf(tag);
                
                if (index === -1) {{
                    selectedTags.push(tag);
                    e.target.classList.add('selected');
                }} else {{
                    selectedTags.splice(index, 1);
                    e.target.classList.remove('selected');
                }}
                
                filterSkills();
            }}
        }});
        
        // Wait for DOM to be fully loaded before initializing
        if (document.readyState === 'loading') {{
            document.addEventListener('DOMContentLoaded', init);
        }} else {{
            init();
        }}
    </script>
</body>
</html>"""
    
    # Create temporary HTML file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
        f.write(html_content)
        temp_path = f.name
    
    # Open in browser
    webbrowser.open(f'file://{temp_path}')
    
    click.echo(click.style("[OK] HTML page opened in browser", fg='green', bold=True))
    click.echo(click.style(f"  Temp file path: {temp_path}", fg='cyan'))


def market_list(tags=None, html=False):
    """List all market skills (optional: filter by tags, display in HTML)"""
    skills = list_all_skills()
    
    # Filter by tags if provided
    if tags:
        tags_list = list(tags)
        skills = [
            skill for skill in skills
            if all(tag.lower() in (t.lower() for t in skill.tags) for tag in tags_list)
        ]
    
    if not skills:
        click.echo(click.style("No skills found in market", fg='yellow'))
        click.echo("Use 'openskills market search <keyword>' to search")
        return
    
    # If HTML mode, generate and display HTML page
    if html:
        generate_market_html(skills)
        return
    
    # Otherwise, display in terminal
    click.echo(click.style(f"Found {len(skills)} skill(s) in market\n", bold=True))
    
    # Group skills by name
    from collections import defaultdict
    skills_by_name = defaultdict(list)
    for skill in skills:
        skills_by_name[skill.name].append(skill)
    
    # Display each skill (with duplicates grouped)
    for skill_name, skill_variants in sorted(skills_by_name.items()):
        click.echo(click.style(f"{skill_name}", fg='cyan', bold=True))
        
        for i, skill in enumerate(skill_variants):
            if len(skill_variants) > 1:
                # Show variant number if there are duplicates
                variant_label = f"  [{i+1}] "
            else:
                variant_label = "      "
            
            # Description
            if skill.description:
                click.echo(f"{variant_label}{skill.description}")
            else:
                click.echo(f"{variant_label}No description")
            
            # Metadata
            click.echo(f"      Source: {skill.source}")
            
            if skill.author:
                click.echo(f"      Author: {skill.author}")
            
            if skill.version:
                click.echo(f"      Version: {skill.version}")
            
            if skill.tags:
                click.echo(f"      Tags: {', '.join(skill.tags)}")
            
            click.echo()


def market_search(keyword: str):
    """Search market skills by keyword"""
    skills = search_skills(keyword)
    
    if not skills:
        click.echo(click.style(f"No skills found matching '{keyword}'", fg='yellow'))
        return
    
    click.echo(click.style(f"Found {len(skills)} skill(s) matching '{keyword}'\n", bold=True))
    
    # Group skills by name
    from collections import defaultdict
    skills_by_name = defaultdict(list)
    for skill in skills:
        skills_by_name[skill.name].append(skill)
    
    # Display each skill
    for skill_name, skill_variants in sorted(skills_by_name.items()):
        click.echo(click.style(f"{skill_name}", fg='cyan', bold=True))
        
        for i, skill in enumerate(skill_variants):
            if len(skill_variants) > 1:
                variant_label = f"  [{i+1}] "
            else:
                variant_label = "      "
            
            # Highlight matching keyword in description
            if skill.description:
                description = skill.description
                # Highlight matches
                import re
                highlighted = re.sub(
                    f'({keyword})',
                    click.style(r'\1', fg='yellow', bold=True),
                    description,
                    flags=re.IGNORECASE
                )
                click.echo(f"{variant_label}{highlighted}")
            else:
                click.echo(f"{variant_label}No description")
            
            click.echo(f"      Source: {skill.source}")
            
            if skill.tags:
                click.echo(f"      Tags: {', '.join(skill.tags)}")
            
            click.echo()