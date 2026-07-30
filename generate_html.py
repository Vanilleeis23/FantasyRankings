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

    # --- PRINT-LOGIK FÜR TEs MIT FPTS ODER XFP GLEICH 0 ---
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
        }}
        .player-card.dragging {{ opacity: 0.4; background: #94a3b8; }}
        .card-summary {{ display: flex; align-items: center; padding: 5px 6px; cursor: grab; user-select: none; }}
        .player-name {{ font-weight: 600; color: #1e293b; flex-grow: 1; font-size: 1em; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
        .bye-tag {{ font-size: 1em; background: #f1f5f9; color: #64748b; padding: 1px 3px; border-radius: 3px; font-weight: bold; margin-left: 4px; }}
        
        .card-details {{ display: none; padding: 8px; background: #f8fafc; border-top: 1px solid #f1f5f9; font-size: 1em; color: #475569; }}
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
        
        /* Neue Farblogik für die Differenz */
        .pos-dif {{ color: #dc2626; font-weight: bold; }} /* Rot bei > 1 */
        .neg-dif {{ color: #16a34a; font-weight: bold; }} /* Grün bei <= -1 */
        .neutral-dif {{ color: #333333; font-weight: bold; }} /* Schwarz sonst */

        .centered-section {{
            text-align: center;
            margin-bottom: 4px;
        }}
        .centered-section strong {{
            display: block;
            margin-bottom: 2px;
        }}
    </style>
</head>
<body>
    <div class="top-bar">
        <h1>Fantasy Football Board</h1>
        <button class="save-btn" onclick="handleSave()">Layout speichern</button>
    </div>
    
    <div class="board-grid">
    """

    # Headers
    html_content += """
        <div class="position-header-cell" style="background-color: #2ecc71; grid-column: span 2;">QB</div>
        <div class="position-header-cell" style="background-color: #e74c3c; grid-column: span 3;">RB</div>
        <div class="position-header-cell" style="background-color: #3498db; grid-column: span 3;">WR</div>
        <div class="position-header-cell" style="background-color: #9b59b6; grid-column: span 1;">TE</div>
    """

    # Grid Zellen befüllen
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
                
                # Dynamische Ermittlung der CSS-Klasse basierend auf dem DIF-Wert
                dif = player.get('dif', 0.0)
                if dif <= -1.0:
                    dif_class = "neg-dif" # Grün
                elif dif >= 1.0:
                    dif_class = "pos-dif" # Rot
                else:
                    dif_class = "neutral-dif" # Schwarz
                
                dif_prefix = "+" if dif > 0 else ""

                html_content += f"""
            <li class="player-card" draggable="true" style="border-left-color: {color};" data-id="{player['name']}">
                <div class="card-summary">
                    <div class="player-name">{last_name}</div>
                    <div class="bye-tag">{player['bye']}</div>
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
                </div>
            </li>
                """
            html_content += "</ul>"

    # JavaScript (Aktualisiert für den GitHub Actions Trigger)
    html_content += f"""
    </div>

    <script>
        const originalPlayers = {players_json_str};

        document.addEventListener('DOMContentLoaded', () => {{
            setupDragAndDrop();
        }});

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
                    currentLayout[pName] = {{
                        tier: tier,
                        column_id: columnId,
                        sort_order: index
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
                        sort_order: currentLayout[name].sort_order
                    }};
                }}
                return player;
            }});

            updatedPlayers.sort((a, b) => {{
                if ((a.tier || 9) !== (b.tier || 9)) return (a.tier || 9) - (b.tier || 9);
                return (a.sort_order || 0) - (b.sort_order || 0);
            }});

            // Ruft direkt deine neue Funktion unten auf – die kümmert sich selbst um den Token!
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
