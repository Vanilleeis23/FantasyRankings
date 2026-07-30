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

    with open('teams.json', 'r', encoding='utf-8') as f:
        teams = json.load(f)

    teams_dict = {team['team_code']: team for team in teams}

    # Initialisiere Struktur für 8 Tiers und 9 Spalten
    # Struktur: tiers_data[tier_num][col_id] = [spieler]
    tiers_data = {t: {c: [] for c in range(9)} for t in range(1, 9)}

    columns_config = [
        (0, 'QB', 0, '#2ecc71'), (1, 'QB', 1, '#2ecc71'),
        (2, 'RB', 0, '#e74c3c'), (3, 'RB', 1, '#e74c3c'), (4, 'RB', 2, '#e74c3c'),
        (5, 'WR', 0, '#3498db'), (6, 'WR', 1, '#3498db'), (7, 'WR', 2, '#3498db'),
        (8, 'TE', 0, '#9b59b6')
    ]
    
    # Helfer, um schnell die Spalten-ID anhand von Position und internem Split zu finden
    def get_column_id(pos, current_count):
        if pos == 'QB': return 0 if current_count % 2 == 0 else 1
        if pos == 'RB': return 2 + (current_count % 3)
        if pos == 'WR': return 5 + (current_count % 3)
        if pos == 'TE': return 8
        return 0

    # Spieler einsortieren
    # Wenn ein Spieler bereits ein gespeichertes "tier" hat, nutzen wir das.
    # Ansonsten verteilen wir sie wie gewohnt mathematisch als Startwert.
    pos_counters = {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0}
    
    for player in players:
        pos = player.get('position')
        if pos not in pos_counters:
            continue
            
        saved_tier = player.get('tier')
        
        if saved_tier and 1 <= int(saved_tier) <= 8:
            # Wenn bereits manuell verschoben und gespeichert, behalte die Spalten-Zuweisung bei
            # Falls keine Spalten-ID gespeichert ist, berechnen wir sie temporär
            col_id = player.get('column_id', get_column_id(pos, pos_counters[pos]))
            tiers_data[int(saved_tier)][int(col_id)].append(player)
        else:
            # Mathematische Erstverteilung auf die 8 Tiers
            c_id = get_column_id(pos, pos_counters[pos])
            # Bestimme ein Pseudo-Tier basierend auf der Position in der Liste
            pseudo_tier = min(8, max(1, (pos_counters[pos] // 4) + 1))
            tiers_data[pseudo_tier][c_id].append(player)
            
        pos_counters[pos] += 1

    # HTML Generierung
    html_content = """<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Fantasy Football Board</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #f0f2f5;
            margin: 0;
            padding: 10px;
            color: #333;
        }
        .top-bar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
            background: #fff;
            padding: 10px 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
        h1 { margin: 0; font-size: 1.6em; color: #2c3e50; }
        
        /* Speicher Button Styling */
        .save-btn {
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
        }
        .save-btn:hover { background-color: #1d4ed8; }
        .save-btn:active { transform: scale(0.98); }

        .board-grid { display: grid; grid-template-columns: repeat(9, 1fr); gap: 6px; }
        .position-header-cell {
            font-size: 1.1em; font-weight: bold; text-align: center; color: #fff;
            padding: 8px 2px; border-radius: 6px; text-transform: uppercase;
            letter-spacing: 1px; box-shadow: 0 2px 4px rgba(0,0,0,0.06); margin-bottom: 8px;
        }
        .tier-row-header {
            grid-column: span 9; background: #2c3e50; color: #fff; font-size: 0.75em;
            font-weight: bold; text-align: center; padding: 5px 12px; border-radius: 4px;
            margin-top: 10px; margin-bottom: 4px; letter-spacing: 1px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .player-list-box {
            background-color: #e2e8f0; border-radius: 6px; padding: 4px; min-height: 60px;
            list-style: none; margin: 0;
        }
        .player-list-box.drag-over { background-color: #cbd5e1; border: 1px dashed #94a3b8; }
        
        .player-card { background: #fff; border-radius: 4px; margin-bottom: 4px; box-shadow: 0 1px 2px rgba(0,0,0,0.04); border-left: 3px solid #ccc; overflow: hidden; }
        .player-card.dragging { opacity: 0.4; background: #94a3b8; }
        .card-summary { display: flex; align-items: center; padding: 5px 6px; cursor: grab; user-select: none; }
        .player-name { font-weight: 600; color: #1e293b; flex-grow: 1; font-size: 0.8em; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
        .bye-tag { font-size: 0.7em; background: #f1f5f9; color: #64748b; padding: 1px 3px; border-radius: 3px; font-weight: bold; margin-left: 4px; }
        .card-details { display: none; padding: 8px; background: #f8fafc; border-top: 1px solid #f1f5f9; font-size: 0.75em; color: #475569; }
        .player-card.expanded .card-details { display: block; }
        .full-name-title { font-weight: bold; color: #0f172a; margin-bottom: 2px; font-size: 1.05em; }
        .team-title { color: #475569; margin-bottom: 6px; font-style: italic;}
        .stats-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 4px; background: #fff; padding: 4px; border-radius: 3px; border: 1px solid #e2e8f0; margin-bottom: 5px; }
        .slots-info { font-size: 0.9em; color: #64748b; margin-bottom: 5px; }
        .schedule-box { border-top: 1px dashed #cbd5e1; padding-top: 4px; color: #d97706; }
        .pos-dif { color: #16a34a; font-weight: bold; }
        .neg-dif { color: #dc2626; font-weight: bold; }
    </style>
</head>
<body>
    <div class="top-bar">
        <h1>Fantasy Football Board</h1>
        <button class="save-btn" onclick="saveBoardLayout()">Layout speichern</button>
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
                
                dif = player.get('dif', 0.0)
                dif_class = "pos-dif" if dif >= 0 else "neg-dif"
                dif_prefix = "+" if dif >= 0 else ""

                html_content += f"""
            <li class="player-card" draggable="true" style="border-left-color: {color};" data-id="{player['name']}">
                <div class="card-summary">
                    <div class="player-name">{last_name}</div>
                    <div class="bye-tag">{player['bye']}</div>
                </div>
                <div class="card-details">
                    <div class="full-name-title">{full_name} ({player['position']})</div>
                    <div class="team-title">{team_info.get('team_name', player['team'])} ({t_code})</div>
                    <div class="stats-grid">
                        <div><strong>FPTS:</strong> {player['fpts']}</div>
                        <div><strong>XFP:</strong> {player['xfp']}</div>
                        <div><strong>DIF:</strong> <span class="{dif_class}">{dif_prefix}{dif}</span></div>
                    </div>
                    <div class="slots-info">
                        <strong>Slots:</strong> 19h ({team_info.get('slots_1900', '-')}) • 22h ({team_info.get('slots_2200', '-')}) • Prime ({team_info.get('primetime', '-')})
                    </div>
                    <div class="schedule-box">
                        <strong>Playoffs:</strong> {team_info.get('playoffs_schedule', 'Kein Spielplan')}
                    </div>
                </div>
            </li>
                """
            html_content += "</ul>"

    # JavaScript inkl. Speicherfunktion
    html_content += """
    </div>

    <script>
        document.addEventListener('DOMContentLoaded', () => {
            setupDragAndDrop();
        });

        function setupDragAndDrop() {
            const grid = document.querySelector('.board-grid');

            grid.addEventListener('dragstart', (e) => {
                if (e.target.classList.contains('player-card')) {
                    e.target.classList.add('dragging');
                    e.dataTransfer.setData('text/plain', '');
                }
            });

            grid.addEventListener('dragend', (e) => {
                if (e.target.classList.contains('player-card')) {
                    e.target.classList.remove('dragging');
                    document.querySelectorAll('.player-list-box').forEach(b => b.classList.remove('drag-over'));
                }
            });

            grid.addEventListener('click', (e) => {
                const summary = e.target.closest('.card-summary');
                if (!summary) return;
                const card = summary.parentElement;
                if (card.classList.contains('dragging')) return;
                
                const isExpanded = card.classList.contains('expanded');
                card.parentElement.querySelectorAll('.player-card').forEach(c => c.classList.remove('expanded'));
                if (!isExpanded) card.classList.add('expanded');
            });

            const boxes = document.querySelectorAll('.player-list-box');
            boxes.forEach(box => {
                box.addEventListener('dragover', (e) => {
                    e.preventDefault();
                    box.classList.add('drag-over');
                    const draggingItem = document.querySelector('.dragging');
                    if (!draggingItem) return;

                    const siblings = [...box.querySelectorAll('.player-card:not(.dragging)')];
                    const nextSibling = siblings.find(sibling => {
                        const r = sibling.getBoundingClientRect();
                        return e.clientY <= r.top + r.height / 2;
                    });
                    box.insertBefore(draggingItem, nextSibling);
                });

                box.addEventListener('dragleave', () => {
                    box.classList.remove('drag-over');
                });
            });
        }

        // Sendet die neue Struktur via POST-Request an den Python Server
        async function saveBoardLayout() {
            const boxes = document.querySelectorAll('.player-list-box');
            const payload = [];

            boxes.forEach(box => {
                const tier = parseInt(box.getAttribute('data-tier'));
                const columnId = parseInt(box.getAttribute('data-column'));
                const cards = box.querySelectorAll('.player-card');

                cards.forEach((card, index) => {
                    payload.push({
                        name: card.getAttribute('data-id'),
                        tier: tier,
                        column_id: columnId,
                        sort_order: index
                    });
                });
            });

            try {
                const response = await fetch('/save-layout', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                
                if (response.ok) {
                    alert('Reihenfolge und Tiers erfolgreich dauerhaft gespeichert!');
                } else {
                    alert('Fehler beim Speichern auf dem Server.');
                }
            } catch (err) {
                console.error(err);
                alert('Server nicht erreichbar. Hast du main.py gestartet?');
            }
        }
    </script>
</body>
</html>
    """

    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    print("HTML-Board erfolgreich generiert.")

if __name__ == '__main__':
    generate_html()