import sys
import json
from generate_html import generate_html

# Versuche, die Server-Bibliotheken zu laden (für lokalen Betrieb)
try:
    from fastapi import FastAPI, HTTPException, Request
    from fastapi.middleware.cors import CORSMiddleware
    import uvicorn
    HAS_SERVER_LIBS = True
except ImportError:
    HAS_SERVER_LIBS = False

# 1. Erstelle die FastAPI App (nur wenn die Bibliotheken da sind)
if HAS_SERVER_LIBS:
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
        # Generiert das Board beim Starten (lokal und auf GitHub) einmal frisch
        generate_html()
        print("HTML erfolgreich generiert.")
        
        if HAS_SERVER_LIBS:
            # Startet den Server auf Port 8000 (nur lokal)
            print("Starte den lokalen Hintergrund-Server auf http://localhost:8000 ...")
            uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
        else:
            # Fallback für GitHub Actions
            print("FastAPI nicht installiert. Server-Start übersprungen (HTML-Generierung abgeschlossen).")
            
    except Exception as e:
        print(f"Ein unerwarteter Fehler ist aufgetreten: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    run_server()
