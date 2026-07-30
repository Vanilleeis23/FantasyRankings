import sys
import json
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from generate_html import generate_html

# 1. Erstelle die FastAPI App
app = FastAPI()

# 2. CORS-Konfiguration für Variante A einfügen (Erlaubt file:// Doppelklick-Zugriff)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Wichtig für den file:// Zugriff
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/save-layout")
async def save_layout(request: Request):
    try:
        # Liest die Rohdaten direkt als JSON-Liste ein
        players = await request.json()
        
        # Überschreibt die lokale JSON-Datei stumm im Hintergrund
        with open('players.json', 'w', encoding='utf-8') as f:
            json.dump(players, f, ensure_ascii=False, indent=4)
            
        return {"status": "success", "message": "Layout erfolgreich gespeichert."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler beim Schreiben der Datei: {str(e)}")

    
def run_server():
    print("Starte die Generierung der Fantasy Football HTML-Seite...")
    try:
        # Generiert das Board beim Starten einmal frisch
        generate_html()
        print("HTML erfolgreich generiert.")
        
        # Startet den Server auf Port 8000
        print("Starte den lokalen Hintergrund-Server auf http://localhost:8000 ...")
        import uvicorn
        uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
        
    except Exception as e:
        print(f"Ein unerwarteter Fehler ist aufgetreten: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    run_server()


