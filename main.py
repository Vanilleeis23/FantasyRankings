import sys
import json
try:
    from fastapi import FastAPI, HTTPException, Request
    import uvicorn
    HAS_SERVER_LIBS = True
except ImportError:
    HAS_SERVER_LIBS = False
from fastapi.middleware.cors import CORSMiddleware
from generate_html import generate_html

if HAS_SERVER_LIBS:
    app = FastAPI()
    
    # ... hier folgen deine Pfade wie @app.post() etc. ...

    if __name__ == "__main__":
        uvicorn.run(app, host="127.0.0.1", port=8000)
else:
    # Wenn wir auf GitHub sind, führen wir beim Direktstart 
    # nur die HTML-Generierung aus
    if __name__ == "__main__":
        from generate_html import generate_html
        # Hier eventuell den Funktionsaufruf platzieren, falls nötig:
        # generate_html()
        print("HTML erfolgreich generiert (ohne FastAPI Server).")

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


