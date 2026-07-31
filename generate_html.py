import json
import os

def extract_last_name(full_name):
    if not full_name:
        return ""
    parts = full_name.strip().split()
    if len(parts) <= 1:
        return full_name
    suffixes = {'jr.', 'sr.', 'ii', 'iii', 'iv', 'v'}
    if parts[-1].lower() in suffixes and len(parts) > 2:
        return f"{parts[-2]} {parts[-1]}"
    return parts[-1]

def generate_html():
    if not os.path.exists('players.json') or not os.path.exists('teams.json'):
        print("Fehler: 'players.json' oder 'teams.json' fehlt.")
        return

    with open('players.json', 'r', encoding='utf-8') as f:
        players = json.load(f)

    print("--- RBs mit fpts oder xfp == 0 ---")
    for player in players:
        if player.get('position') == 'TE':
            fpts = player.get('fpts', 0)
            xfp = player.get('xfp', 0)
            
            if fpts == 0 or xfp == 0:
                print(f"Spieler: {player.get('name')} ({player.get('team')}) | fpts: {fpts} | xfp: {xfp}")
    print("---------------------------------------")

    with open('teams.json', 'r', encoding='utf-8') as f:
        teams = json.load(f)

    teams_dict = {team['team_code']: team for team in teams}
    players_json_str = json.dumps(players, ensure_ascii=False)
    tiers_data = {t: {c: [] for c in range(9)} for t in range(1, 9)}

    columns_config = [
        (0, 'QB', 0, '#2ecc71'), (1, 'QB', 1, '#2ecc71'),
        (2, 'RB', 0, '#e74c3c'), (3, 'RB', 1, '#e74c3c'), (4, 'RB', 2, '#e74c3c'),
        (5, 'WR', 0, '#3498db'), (6, 'WR', 1, '#3498db'), (7, 'WR', 2, '#3498db'),
        (8, 'TE', 0, '#9b59b6')
    ]
    
    def get_column_id(pos, current_count):
        if pos == 'QB': return 0 if current_count % 2 == 0 else 1
        if pos == 'RB': return 2 + (current_count % 3)
        if pos == 'WR': return 5 + (current_count % 3)
        if pos == 'TE': return 8
        return 0

    pos_counters = {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0}
    
    for player in players:
        pos = player.get('position')
        if pos not in pos_counters:
            continue
            
        saved_tier = player.get('tier')
        
        if saved_tier and 1 <= int(saved_tier) <= 8:
            col_id = player.get('column_id', get_column_id(pos, pos_counters[pos]))
            tiers_data[int(saved_tier)][int(col_id)].append(player)
        else:
            c_id = get_column_id(pos, pos_counters[pos])
            pseudo_tier = min(8, max(1, (pos_counters[pos] // 4) + 1))
            tiers_data[pseudo_tier][c_id].append(player)
            
        pos_counters[pos] += 1

    html_content = f"""<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Fantasy Football Board</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #f0f2f5;
            margin: 0;
            padding: 10px;
            color: #333;
        }}
        .top-bar {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
            background: #fff;
            padding: 10px 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }}
        .top-bar-actions {{
            display: flex;
            gap: 10px;
        }}
        h1 {{ margin: 0; font-size: 1.6em; color: #2c3e50; }}
        
        .save-btn {{
            background-color: #2563eb;
            color: white;
            border: none;
            padding: 10px 20px;
            font-size: 0.9em;
            font-weight: bold;
            border-radius: 6px;
            cursor: pointer;
            transition: background 0.2s;
            box-shadow: 0 2px 4px rgba(37,99,235,0.2);
        }}
        .save-btn:hover {{ background-color: #1d4ed8; }}
        .save-btn:active {{ transform: scale(0.98); }}

        .compare-btn {{
            background-color: #007bff;
            color: white;
            border: none;
            padding: 10px 20px;
            font-size: 0.9em;
            font-weight: bold;
            border-radius: 6px;
            cursor: pointer;
            transition: background 0.2s;
            box-shadow: 0 2px 4px rgba(0,123,255,0.2);
        }}
        .compare-btn:hover {{ background-color: #0069d9; }}
        .compare-btn:active {{ transform: scale(0.98); }}

        .board-grid {{ display: grid; grid-template-columns: repeat(9, 1fr); gap: 6px; }}
        .position-header-cell {{
            font-size: 1.1em; font-weight: bold; text-align: center; color: #fff;
            padding: 8px 2px; border-radius: 6px; text-transform: uppercase;
            letter-spacing: 1px; box-shadow: 0 2px 4px rgba(0,0,0,0.06); margin-bottom: 8px;
        }}
        .tier-row-header {{
            grid-column: span 9; background: #2c3e50; color: #fff; font-size: 0.75em;
            font-weight: bold; text-align: center; padding: 5px 12px; border-radius: 4px;
            margin-top: 10px; margin-bottom: 4px; letter-spacing: 1px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .player-list-box {{
            background-color: #e2e8f0; border-radius: 6px; padding: 4px; min-height: 60px;
            list-style: none; margin: 0;
        }}
        .player-list-box.drag-over {{ background-color: #cbd5e1; border: 1px dashed #94a3b8; }}
        
        .player-card {{ 
            background: #fff; 
            border-radius: 4px; 
            margin-bottom: 4px; 
            box-shadow: 0 1px 2px rgba(0,0,0,0.04); 
            border-left: 3px solid #ccc; 
            overflow: hidden; 
            font-size: 11px; 
            text-align: center;
            transition: opacity 0.2s, filter 0.2s, background-color 0.2s;
        }}

        /* Dynamische Statusfarben */
        .player-card.status-blue {{ background-color: #dbeafe !important; }}
        .player-card.status-red {{ background-color: #fee2e2 !important; }}
        .player-card.status-green {{ background-color: #dcfce7 !important; }}

        .player-card.drafted {{
            opacity: 0.35;
            filter: grayscale(90%);
            background-color: #e2e8f0 !important;
        }}
        .player-card.dragging {{ opacity: 0.4; background: #94a3b8; }}
        .card-summary {{ display: flex; align-items: center; padding: 5px 6px; cursor: grab; user-select: none; gap: 4px; }}
        .player-name {{ font-weight: 600; color: #1e293b; flex-grow: 1; font-size: 1em; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; text-align: left; }}
        .bye-tag {{ font-size: 1em; background: #f1f5f9; color: #64748b; padding: 1px 3px; border-radius: 3px; font-weight: bold; }}
        
        .drafted-label-header {{
            display: flex;
            align-items: center;
            font-size: 0.9em;
            color: #64748b;
            cursor: pointer;
        }}
        .drafted-label-header input {{
            margin: 0;
            cursor: pointer;
        }}

        .card-details {{ display: none; padding: 8px; background: rgba(248, 250, 252, 0.7); border-top: 1px solid #f1f5f9; font-size: 1em; color: #475569; }}
        .player-card.expanded .card-details {{ display: block; }}
        
        .full-name-title {{ font-weight: bold; color: #0f172a; margin-bottom: 2px; font-size: 1em; }}
        .team-title {{ color: #475569; margin-bottom: 6px; font-style: italic; font-size: 1em; }}
        
        .card-divider {{
            border: 0;
            border-top: 1px dashed #cbd5e1;
            margin: 6px 0;
        }}

        .stats-grid {{ 
            display: grid; 
            grid-template-columns: repeat(3, 1fr); 
            gap: 4px; 
            background: transparent; 
            padding: 0; 
            border: none; 
            margin-bottom: 5px; 
            text-align: center;
        }}
        .stats-grid div {{ font-size: 1em; }}
        
        .pos-dif {{ color: #dc2626; font-weight: bold; }} 
        .neg-dif {{ color: #16a34a; font-weight: bold; }} 
        .neutral-dif {{ color: #333333; font-weight: bold; }} 

        .centered-section {{
            text-align: center;
            margin-bottom: 4px;
        }}
        .centered-section strong {{
            display: block;
            margin-bottom: 2px;
        }}

        .action-section-details {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-top: 8px;
            padding-top: 6px;
            border-top: 1px dashed #cbd5e1;
            gap: 6px;
        }}
        .action-section-details label {{
            display: flex;
            align-items: center;
            gap: 4px;
            cursor: pointer;
            font-weight: bold;
            font-size: 10px;
            color: #475569;
        }}
        .note-select {{
            width: 110px;
            font-size: 10px;
            padding: 2px;
            border: 1px solid #cbd5e1;
            border-radius: 4px;
            color: #334155;
            background-color: #fff;
        }}

        /* Compare Popup Styles */
        .compare-popup-overlay {{
            position: fixed;
            top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(0,0,0,0.6);
            z-index: 9999;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        .compare-popup-content {{
            background: #fff;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.2);
            max-width: 90%;
            max-height: 85vh;
            overflow-y: auto;
            position: relative;
        }}
        .compare-popup-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
            border-bottom: 2px solid #e2e8f0;
            padding-bottom: 10px;
        }}
        .compare-popup-header h2 {{ margin: 0; font-size: 1.4em; color: #2c3e50; }}
        .close-popup-btn {{
            background: #dc3545; color: white; border: none; padding: 6px 12px;
            border-radius: 4px; cursor: pointer; font-weight: bold;
        }}
        .compare-cards-container {{
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
            justify-content: center;
        }}
        .compare-cards-container .player-card {{
            width: 200px;
            font-size: 12px;
        }}
        .compare-cards-container .card-details {{
            display: block !important;
        }}
        .compare-cards-container .action-section-details {{
            display: none !important;
        }}
        .compare-cards-container .drafted-label-header {{
            display: none !important;
        }}
    </style>
</head>
<body>
    <div class="top-bar">
        <h1>Fantasy Football Board</h1>
        <div class="top-bar-actions">
            <button class="compare-btn" onclick="openComparePopup()">Spieler vergleichen (<span id="compare-count">0</span>)</button>
            <button class="save-btn" onclick="handleSave()">Layout speichern</button>
        </div>
    </div>
    
    <div class="board-grid">
    """

    html_content += """
        <div class="position-header-cell" style="background-color: #2ecc71; grid-column: span 2;">QB</div>
        <div class="position-header-cell" style="background-color: #e74c3c; grid-column: span 3;">RB</div>
        <div class="position-header-cell" style="background-color: #3498db; grid-column: span 3;">WR</div>
        <div class="position-header-cell" style="background-color: #9b59b6; grid-column: span 1;">TE</div>
    """

    for tier_num in range(1, 9):
        html_content += f'<div class="tier-row-header">TIER {tier_num}</div>'
        
        for col_id, pos_name, sub_idx, color in columns_config:
            html_content += f'<ul class="player-list-box" data-tier="{tier_num}" data-column="{col_id}">'
            
            tier_players = tiers_data[tier_num][col_id]
            for player in tier_players:
                full_name = player['name']
                last_name = extract_last_name(full_name)
                t_code = player.get('team')
                team_info = teams_dict.get(t_code, {})
                current_note = player.get('note', '')
                
                dif = player.get('dif', 0.0)
                if dif <= -1.0:
                    dif_class = "neg-dif"
                elif dif >= 1.0:
                    dif_class = "pos-dif"
                else:
                    dif_class = "neutral-dif"
                
                dif_prefix = "+" if dif > 0 else ""

                html_content += f"""
            <li class="player-card" draggable="true" style="border-left-color: {color};" data-id="{player['name']}" data-pos="{player['position']}" id="player-card-{player['name'].replace(' ', '_').replace('.', '_')}">
                <div class="card-summary">
                    <div class="player-name">{last_name}</div>
                    <div class="bye-tag">{player['bye']}</div>
                    <label class="drafted-label-header" onclick="event.stopPropagation();">
                        <input type="checkbox" class="drafted-cb" onchange="toggleDrafted(this)">
                    </label>
                </div>
                <div class="card-details">
                    <div class="full-name-title">{full_name} ({player['position']})</div>
                    <div class="team-title">{team_info.get('team_name', player['team'])} ({t_code})</div>
                    
                    <hr class="card-divider">
                    
                    <div class="stats-grid">
                        <div><strong>FPTS</strong><br>{player['fpts']}</div>
                        <div><strong>XFP</strong><br>{player['xfp']}</div>
                        <div><strong>DIF</strong><br><span class="{dif_class}">{dif_prefix}{dif}</span></div>
                    </div>
                    
                    <hr class="card-divider">
                    
                    <div class="centered-section">
                        <strong>Slots</strong>
                        <span>19h ({team_info.get('slots_1900', '-')}) • 22h ({team_info.get('slots_2200', '-')}) • Prime ({team_info.get('primetime', '-')})</span>
                    </div>
                    
                    <hr class="card-divider">
                    
                    <div class="centered-section">
                        <strong>Playoffs</strong>
                        <span>{team_info.get('playoffs_schedule', 'Kein Spielplan')}</span>
                    </div>

                    <div class="action-section-details">
                        <label onclick="event.stopPropagation();">
                            <input type="checkbox" class="compare-cb" onchange="toggleCompare(this, '{player['name'].replace(' ', '_').replace('.', '_')}')"> Compare
                        </label>
                        <select class="note-select" onclick="event.stopPropagation();" onchange="updateCardColor(this.closest('.player-card'))" title="Dynasty Kader-Status">
                            <option value="" {"selected" if current_note == "" else ""}>Free</option>
                            <option value="OWNED" {"selected" if current_note == "OWNED" else ""}>OWNED</option>
                            <option value="QB" {"selected" if current_note == "QB" else ""}>QB vorhanden</option>
                            <option value="RB" {"selected" if current_note == "RB" else ""}>RB vorhanden</option>
                            <option value="WR/TE" {"selected" if current_note == "WR/TE" else ""}>WR/TE vorhanden</option>
                        </select>
                    </div>
                </div>
            </li>
                """
            html_content += "</ul>"

    html_content += f"""
    </div>

    <script>
        const originalPlayers = {players_json_str};
        let selectedComparePlayers = [];

        document.addEventListener('DOMContentLoaded', () => {{
            setupDragAndDrop();
            // Initiale Einfärbung aller Karten beim Laden
            document.querySelectorAll('.player-card').forEach(card => updateCardColor(card));
        }});

        function updateCardColor(card) {{
            const pos = card.getAttribute('data-pos');
            const noteSelect = card.querySelector('.note-select');
            if (!noteSelect) return;
            
            const value = noteSelect.value;
            
            // Erst alle alten Statusklassen entfernen
            card.classList.remove('status-blue', 'status-red', 'status-green');
            
            if (value === 'OWNED') {{
                card.classList.add('status-blue');
                return;
            }}
            
            // Logik für ROT
            if (pos === 'RB' && (value === 'QB' || value === 'WR/TE')) {{
                card.classList.add('status-red');
            }} else if ((pos === 'QB' || pos === 'WR' || pos === 'TE') && value === 'RB') {{
                card.classList.add('status-red');
            }}
            
            // Logik für GRÜN
            if (pos === 'QB' && value === 'WR/TE') {{
                card.classList.add('status-green');
            }} else if ((pos === 'WR' || pos === 'TE') && value === 'QB') {{
                card.classList.add('status-green');
            }}
        }}

        function toggleDrafted(checkbox) {{
            const card = checkbox.closest('.player-card');
            if (card) {{
                if (checkbox.checked) {{
                    card.classList.add('drafted');
                }} else {{
                    card.classList.remove('drafted');
                }}
            }}
        }}

        function toggleCompare(checkbox, cardId) {{
            if (checkbox.checked) {{
                if (!selectedComparePlayers.includes(cardId)) {{
                    selectedComparePlayers.push(cardId);
                }}
            }} else {{
                selectedComparePlayers = selectedComparePlayers.filter(id => id !== cardId);
            }}
            document.getElementById('compare-count').innerText = selectedComparePlayers.length;
        }}

        function openComparePopup() {{
            if (selectedComparePlayers.length === 0) {{
                alert('Bitte wähle zuerst mindestens einen Spieler über die \"Compare\"-Checkbox aus.');
                return;
            }}

            const overlay = document.createElement('div');
            overlay.className = 'compare-popup-overlay';
            overlay.id = 'compare-overlay';
            overlay.onclick = closeComparePopup;

            const content = document.createElement('div');
            content.className = 'compare-popup-content';
            content.onclick = (e) => e.stopPropagation();

            let popupContent = `
                <div class="compare-popup-header">
                    <h2>Spieler-Vergleich</h2>
                    <button class="close-popup-btn" onclick="closeComparePopup()">Schließen</button>
                </div>
                <div class="compare-cards-container">
            `;

            selectedComparePlayers.forEach(id => {{
                const originalCard = document.getElementById(`player-card-${{id}}`);
                if (originalCard) {{
                    const clone = originalCard.cloneNode(true);
                    clone.className = originalCard.className + ' expanded'; // Behält die Farbeklassen bei
                    clone.id = '';
                    clone.style.borderLeftWidth = originalCard.style.borderLeftWidth;
                    clone.style.borderLeftColor = originalCard.style.borderLeftColor;
                    popupContent += clone.outerHTML;
                }}
            }});

            popupContent += '</div>';
            content.innerHTML = popupContent;
            overlay.appendChild(content);
            document.body.appendChild(overlay);
        }}

        function closeComparePopup() {{
            const overlay = document.getElementById('compare-overlay');
            if (overlay) overlay.remove();
        }}

        function setupDragAndDrop() {{
            const grid = document.querySelector('.board-grid');

            grid.addEventListener('dragstart', (e) => {{
                if (e.target.classList.contains('player-card')) {{
                    e.target.classList.add('dragging');
                    e.dataTransfer.setData('text/plain', '');
                }}
            }});

            grid.addEventListener('dragend', (e) => {{
                if (e.target.classList.contains('player-card')) {{
                    e.target.classList.remove('dragging');
                    document.querySelectorAll('.player-list-box').forEach(b => b.classList.remove('drag-over'));
                }}
            }});

            grid.addEventListener('click', (e) => {{
                if (e.target.closest('input') || e.target.closest('select') || e.target.closest('label')) return;
                
                const summary = e.target.closest('.card-summary');
                if (!summary) return;
                const card = summary.parentElement;
                if (card.classList.contains('dragging')) return;
                
                const isExpanded = card.classList.contains('expanded');
                card.parentElement.querySelectorAll('.player-card').forEach(c => c.classList.remove('expanded'));
                if (!isExpanded) card.classList.add('expanded');
            }});

            const boxes = document.querySelectorAll('.player-list-box');
            boxes.forEach(box => {{
                box.addEventListener('dragover', (e) => {{
                    e.preventDefault();
                    box.classList.add('drag-over');
                    const draggingItem = document.querySelector('.dragging');
                    if (!draggingItem) return;

                    const siblings = [...box.querySelectorAll('.player-card:not(.dragging)')];
                    const nextSibling = siblings.find(sibling => {{
                        const r = sibling.getBoundingClientRect();
                        return e.clientY <= r.top + r.height / 2;
                    }});
                    box.insertBefore(draggingItem, nextSibling);
                }});

                box.addEventListener('dragleave', () => {{
                    box.classList.remove('drag-over');
                }});
            }});
        }}

        function handleSave() {{
            const boxes = document.querySelectorAll('.player-list-box');
            const currentLayout = {{}};

            boxes.forEach(box => {{
                const tier = parseInt(box.getAttribute('data-tier'));
                const columnId = parseInt(box.getAttribute('data-column'));
                const cards = box.querySelectorAll('.player-card');

                cards.forEach((card, index) => {{
                    const pName = card.getAttribute('data-id');
                    const noteSelect = card.querySelector('.note-select');
                    const noteVal = noteSelect ? noteSelect.value : "";
                    
                    currentLayout[pName] = {{
                        tier: tier,
                        column_id: columnId,
                        sort_order: index,
                        note: noteVal
                    }};
                }});
            }});

            const updatedPlayers = originalPlayers.map(player => {{
                const name = player.name;
                if (currentLayout[name]) {{
                    return {{
                        ...player,
                        tier: currentLayout[name].tier,
                        column_id: currentLayout[name].column_id,
                        sort_order: currentLayout[name].sort_order,
                        note: currentLayout[name].note
                    }};
                }}
                return player;
            }});

            updatedPlayers.sort((a, b) => {{
                if ((a.tier || 9) !== (b.tier || 9)) return (a.tier || 9) - (b.tier || 9);
                return (a.sort_order || 0) - (b.sort_order || 0);
            }});

            saveToGitHub(updatedPlayers);
        }}

        async function saveToGitHub(payload) {{
            const GITHUB_REPO = "Vanilleeis23/FantasyRankings"; 
            
            let GITHUB_TOKEN = localStorage.getItem('github_token');
            
            if (!GITHUB_TOKEN) {{
                GITHUB_TOKEN = prompt("Bitte gib deinen GitHub Personal Access Token ein (wird nur lokal im Browser gespeichert):");
                if (!GITHUB_TOKEN) return;
                localStorage.setItem('github_token', GITHUB_TOKEN);
            }}

            try {{
                const response = await fetch(`https://api.github.com/repos/${{GITHUB_REPO}}/dispatches`, {{
                    method: 'POST',
                    headers: {{
                        'Authorization': `Bearer ${{GITHUB_TOKEN}}`,
                        'Accept': 'application/vnd.github.v3+json',
                        'Content-Type': 'application/json'
                    }},
                    body: JSON.stringify({{
                        event_type: 'save_layout',
                        client_payload: {{
                            players_data: payload
                        }}
                    }})
                }});

                if (response.status === 204) {{
                    alert('Speichervorgang auf GitHub erfolgreich gestartet!');
                }} else if (response.status === 401 || response.status === 403) {{
                    alert('Fehler: Token ist ungültig oder abgelaufen. Er wird zurückgesetzt.');
                    localStorage.removeItem('github_token');
                }} else {{
                    const errText = await response.text();
                    alert(`Fehler beim Speichern (Status ${{response.status}}): ${{errText}}`);
                }}
            }} catch (err) {{
                console.error(err);
                alert('Netzwerkfehler beim Kommunizieren mit der GitHub API.');
            }}
        }}
    </script>
</body>
</html>
    """

    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    print("HTML-Board erfolgreich generiert.")

if __name__ == '__main__':
    generate_html()