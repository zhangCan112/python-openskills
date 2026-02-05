"""
Market command HTML generation
"""

import json
import tempfile
import webbrowser


def generate_market_html(skills):
    """
    Generate an interactive HTML page for browsing market skills
    
    Args:
        skills: List of MarketSkill objects
    """
    # Collect all unique tags
    all_tags = set()
    for skill in skills:
        all_tags.update(skill.tags)
    all_tags = sorted(all_tags)
    
    # Prepare skills data for JavaScript
    skills_data = []
    for skill in skills:
        # Use the repo field directly from MarketSkill for grouping
        # This is the base repository without subpaths
        repo = skill.repo
        
        skills_data.append({
            'name': skill.name,
            'description': skill.description,
            'source': skill.source,
            'repo': repo,  # Use repo for grouping
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
            margin-bottom: 25px;
            padding-bottom: 15px;
            border-bottom: 3px solid #f0f0f0;
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
    
    # Build HTML content
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
            <input type="text" class="search-input" id="searchInput" placeholder="🔍 Search skill name, description, or tags...">
        </div>
        
        <div class="tags-section">
            <h3>📌 Filter by Tags</h3>
            <div id="tagsContainer">{tags_html}</div>
            <div class="stats">
                <span id="stats"></span>
            </div>
        </div>
        
        <div id="contentContainer"></div>
        <div id="noResults" class="no-results" style="display: none;">No matching skills found</div>
    </div>
    
    <script>
        // Skills data
        const skills = {json.dumps(skills_data, ensure_ascii=False, indent=2)};
        let selectedTags = [];
        
        const searchInput = document.getElementById('searchInput');
        const tagsContainer = document.getElementById('tagsContainer');
        const contentContainer = document.getElementById('contentContainer');
        const noResults = document.getElementById('noResults');
        const stats = document.getElementById('stats');
        
        // Initialize
        function init() {{
            console.log('Initializing page...');
            console.log('Skills count:', skills.length);
            renderSkillsGroupedBySource(skills);
            updateStats(skills.length, skills.length);
            console.log('Page initialized successfully!');
        }}
        
        // Highlight search terms in text
        function highlightText(text, searchTerm) {{
            if (!searchTerm) return escapeHtml(text || '');
            const escapedText = escapeHtml(text || '');
            const escapedSearchTerm = escapeHtml(searchTerm);
            const regex = new RegExp('(' + escapeRegex(escapedSearchTerm) + ')', 'gi');
            return escapedText.replace(regex, '<span class="highlight">$1</span>');
        }}
        
        // Escape special regex characters
        function escapeRegex(string) {{
            return string.replace(/[.*+?^${{}}()|[\\]\\\\]/g, '\\\\$&');
        }}
        
        // Render skills grouped by repo
        function renderSkillsGroupedBySource(skillsToRender, searchTerm) {{
            console.log('Rendering skills grouped by repo:', skillsToRender.length);
            
            // Group skills by repo
            const grouped = {{}};
            skillsToRender.forEach(skill => {{
                if (!grouped[skill.repo]) {{
                    grouped[skill.repo] = [];
                }}
                grouped[skill.repo].push(skill);
            }});
            
            // Generate HTML for each repo section
            const sourcesHtml = Object.entries(grouped).map(([repo, repoSkills]) => `
                <div class="source-section">
                    <div class="source-section-header">
                        <div class="source-section-title">${{escapeHtml(repo)}}</div>
                        <div class="source-section-count">${{repoSkills.length}} skills</div>
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
                                <div class="skill-tags">
                                    ${{skill.tags.map(tag => `<span class="tag" data-tag="${{escapeHtml(tag)}}">${{highlightText(tag, searchTerm)}}</span>`).join('')}}
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
            
            // Show/hide no results message
            noResults.style.display = skillsToRender.length === 0 ? 'block' : 'none';
            if (skillsToRender.length === 0) {{
                contentContainer.innerHTML = noResults.outerHTML;
            }}
        }}
        
        // Filter skills based on search and tags
        function filterSkills() {{
            const searchTerm = searchInput.value;
            const searchTermLower = searchTerm.toLowerCase();
            
            const filtered = skills.filter(skill => {{
                // Check search term
                const matchesSearch = !searchTermLower ||
                    skill.name.toLowerCase().includes(searchTermLower) ||
                    (skill.description && skill.description.toLowerCase().includes(searchTermLower)) ||
                    skill.tags.some(tag => tag.toLowerCase().includes(searchTermLower)) ||
                    skill.author.toLowerCase().includes(searchTermLower);
                
                // Check tags (AND logic)
                const matchesTags = selectedTags.length === 0 ||
                    selectedTags.every(tag => skill.tags.includes(tag));
                
                return matchesSearch && matchesTags;
            }});
            
            renderSkillsGroupedBySource(filtered, searchTerm);
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
            stats.textContent = `Showing ${{visible}} / ${{total}} skills`;
        }}
        
        // Copy command to clipboard
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
        
        // Escape HTML to prevent XSS
        function escapeHtml(text) {{
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }}
        
        // Event listeners
        searchInput.addEventListener('input', filterSkills);
        
        contentContainer.addEventListener('click', (e) => {{
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
    
    return temp_path